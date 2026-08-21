package main

import (
	"context"
	"net/http"
	"net/url"
	"os"
	"time"
)

// ensureCertInstalled makes sure the local CA exists on disk and is trusted
// by the OS. On Windows / macOS it transparently triggers the platform's
// install flow (UAC popup or keychain password prompt). If the certificate
// is already installed, it is a fast no-op so we don't spam the user with
// security dialogs on every start.
func ensureCertInstalled() error {
	if err := ensureCertExists(); err != nil {
		return err
	}
	cp, err := certPath()
	if err != nil {
		return err
	}
	cert, err := readCertificate(cp)
	if err != nil {
		return err
	}
	thumb := certThumbprintHex(cert)
	if isCertInstalled(thumb) {
		Log(LogLevelInfo, "本地根证书已经安装到系统信任列表，跳过安装步骤")
		return nil
	}
	Log(LogLevelInfo, "首次启动需要将本地根证书安装到系统信任列表，可能会弹出系统授权对话框，请允许……")
	return installCert(cp)
}

// authorizer 提供访问查分器 API 所需的认证头。两种实现：OAuth 授权
// （新用户走这条）和旧版的成绩导入 Token（已经配好的老用户继续用）。
type authorizer interface {
	apply(req *http.Request) error
	describe() string
}

// importTokenAuth 是旧版认证方式：一把长期有效、能代表账号做任何事的
// 静态凭据。OAuth 那条路给出的令牌只有 15 分钟、只带上传成绩这一项权限，
// 用户还能随时在水鱼账号里撤销——所以新用户不再走这里。
type importTokenAuth struct{ token string }

func (a importTokenAuth) apply(req *http.Request) error {
	req.Header.Set("Import-Token", a.token)
	return nil
}

func (a importTokenAuth) describe() string { return "成绩导入 Token（旧版）" }

// validateToken pings /token_available to check whether the given Import
// Token corresponds to a registered account. We treat HTTP 200 as success
// and any other status (including network errors) as failure.
func validateToken(ctx context.Context, token string) (bool, error) {
	if token == "" {
		return false, nil
	}
	u := "https://www.diving-fish.com/api/maimaidxprober/token_available?token=" + url.QueryEscape(token)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
	if err != nil {
		return false, err
	}
	cl := &http.Client{Timeout: 10 * time.Second}
	resp, err := cl.Do(req)
	if err != nil {
		return false, err
	}
	defer resp.Body.Close()
	return resp.StatusCode == http.StatusOK, nil
}

// ensureAuth 决定这次运行拿什么去调查分器接口。
//
// 顺序即优先级：已经授权过的走 OAuth；没授权但 config.json 里留着一把还
// 有效的旧 Token 的，继续用它，不打扰升级上来的老用户；两样都没有就跑一遍
// 授权流程。reauth 为真时无条件重新授权。
func ensureAuth(cfg *config, configPath string, reauth bool) (authorizer, error) {
	oc := newOAuthClient(cfg, configPath)

	if reauth {
		if err := oc.authorize(context.Background()); err != nil {
			return nil, err
		}
		return oc, nil
	}

	if err := oc.load(); err == nil {
		// 手上的凭据未必还有效（refresh token 可能已被用户撤销或被判泄露
		// 吊销）。当场换一张 access token 试试，失败就重新走授权，
		// 而不是留到第一次上传成绩时才炸
		if _, err := oc.accessToken(context.Background()); err == nil {
			Log(LogLevelInfo, "已读取水鱼账号授权凭据")
			return oc, nil
		}
		Log(LogLevelWarning, "原有授权已失效，需要重新授权")
	} else if !os.IsNotExist(err) {
		Log(LogLevelWarning, "读取凭据文件失败：%s，需要重新授权", err)
	}

	if cfg.Token != "" {
		ok, err := validateToken(context.Background(), cfg.Token)
		if err != nil {
			Log(LogLevelWarning, "校验现有 Token 时出错：%s", err)
		} else if ok {
			Log(LogLevelInfo, "正在使用 config.json 中的成绩导入 Token")
			return importTokenAuth{token: cfg.Token}, nil
		} else {
			Log(LogLevelWarning, "config.json 中的 Token 已失效")
		}
	}

	if err := oc.authorize(context.Background()); err != nil {
		return nil, err
	}
	return oc, nil
}
