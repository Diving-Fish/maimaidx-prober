package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"strings"
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

// promptToken interactively asks the user to paste an Import-Token and
// validates it against the diving-fish API. It loops until the user provides
// a valid token or aborts (Ctrl-C). The returned string is the verified
// token.
func promptToken(reader *bufio.Reader) (string, error) {
	fmt.Println()
	fmt.Println("=========================================================")
	fmt.Println("欢迎使用 maimaidx-prober，请按以下步骤完成首次配置：")
	fmt.Println("  1. 打开 https://www.diving-fish.com/maimaidx/prober/ 并登录")
	fmt.Println("  2. 在「编辑个人资料」页面找到「Import-Token」并复制")
	fmt.Println("  3. 将 Token 粘贴到下方（粘贴后按回车）")
	fmt.Println("=========================================================")
	for {
		fmt.Print("请粘贴 Import-Token: ")
		line, err := reader.ReadString('\n')
		if err != nil {
			return "", fmt.Errorf("读取输入失败: %w", err)
		}
		token := strings.TrimSpace(line)
		if token == "" {
			Log(LogLevelWarning, "Token 不能为空，请重新粘贴")
			continue
		}
		fmt.Print("正在校验 Token，请稍候……")
		ok, err := validateToken(context.Background(), token)
		fmt.Println()
		if err != nil {
			Log(LogLevelWarning, "校验失败：%s。请检查网络后重试", err)
			continue
		}
		if !ok {
			Log(LogLevelWarning, "Token 无效，可能是输入错误或者尚未在 diving-fish 注册账号")
			continue
		}
		Log(LogLevelInfo, "Token 校验通过！")
		return token, nil
	}
}

// saveTokenToConfig persists the validated token into config.json, preserving
// any other fields the user might have set previously.
func saveTokenToConfig(path, token string) error {
	var raw map[string]interface{}
	if b, err := os.ReadFile(path); err == nil {
		if jerr := json.Unmarshal(b, &raw); jerr != nil || raw == nil {
			raw = map[string]interface{}{}
		}
	} else {
		raw = map[string]interface{}{}
	}
	raw["token"] = token
	out, err := json.MarshalIndent(raw, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, out, 0644)
}

// ensureToken checks the loaded config for a valid Import-Token. If the
// token is missing or rejected by the server, the user is prompted to paste
// one and the result is written back to config.json.
func ensureToken(cfg *config, configPath string) error {
	if cfg.Token != "" {
		ok, err := validateToken(context.Background(), cfg.Token)
		if err == nil && ok {
			return nil
		}
		if err != nil {
			Log(LogLevelWarning, "校验现有 Token 时出错：%s", err)
		} else {
			Log(LogLevelWarning, "现有 Token 已失效，需要重新输入")
		}
	}
	reader := bufio.NewReader(os.Stdin)
	token, err := promptToken(reader)
	if err != nil {
		return err
	}
	if err := saveTokenToConfig(configPath, token); err != nil {
		return fmt.Errorf("保存 Token 到 %s 失败: %w", configPath, err)
	}
	cfg.Token = token
	Log(LogLevelInfo, "Token 已写入 %s", configPath)
	return nil
}
