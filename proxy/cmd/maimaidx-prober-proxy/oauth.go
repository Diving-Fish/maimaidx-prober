package main

// 水鱼账号的 OAuth 授权码流程（PKCE，公开客户端）。
//
// 这个程序分发给用户各自运行，装在谁的机器上 client_secret 就摊给谁看，
// 所以它是**公开客户端**：不持有应用凭据，全程不发送 client_secret（发了
// 反而会被判成认证失败），改由 PKCE 证明「换票的和发起授权的是同一个进程」。
//
// 回调落在本机：授权码经由 http://127.0.0.1:<临时端口>/callback 回来，端口由
// 系统分配。授权服务器对回环地址不比对端口（RFC 8252 §7.3），所以登记一个
// http://127.0.0.1/callback 就够，不必写死端口——写死了一旦被别的程序占用，
// 用户就彻底授权不了。
//
// 拿到的 refresh token 每次刷新都会轮换，**旧的那把再出现会被判为泄露、
// 整条链一起吊销**。因此凭据文件必须原子替换（先写临时文件再 rename），
// 刷新也必须串行，不能让两个请求同时拿着同一把去刷。

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"time"
)

const (
	defaultIssuer = "https://auth.diving-fish.com"

	// 本程序在水鱼账号上登记的应用标识。公开客户端，回调地址登记为
	// http://127.0.0.1/callback ，接入方式为「网页 / 客户端应用」、
	// 部署形态为「分发给用户各自部署」。
	defaultClientID = "prober-proxy"

	// 只申请上传成绩所必需的两项。这个程序不读成绩、不读资料，多要一项
	// 就是让用户在同意页上多授权一件本程序根本不做的事。
	oauthScope = "prober.records.write chunithm.records.write"

	// 授权码回调的落点。路径参与逐字符比对，改这里就要同步改登记值。
	callbackPath = "/callback"

	// 用户在浏览器里完成登录 + 同意的时间上限。
	authorizeTimeout = 5 * time.Minute
)

// oauthTokens 是落盘的凭据。access token 只有 15 分钟，真正需要保住的是
// refresh token 。
type oauthTokens struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	ExpiresAt    int64  `json:"expires_at"`
	Scope        string `json:"scope,omitempty"`
}

// endpoints 来自 IdP 的发现文档，不硬编码路径：换端点时用户手上的旧版本
// 也能跟着走。
type endpoints struct {
	Authorization string `json:"authorization_endpoint"`
	Token         string `json:"token_endpoint"`
}

type oauthClient struct {
	issuer   string
	clientID string
	credPath string
	hc       *http.Client

	mu  sync.Mutex // 串行化刷新：并发刷新会把整条 refresh token 链弄废
	tok oauthTokens
	ep  endpoints
}

func credentialsPath(configPath string) string {
	return filepath.Join(filepath.Dir(configPath), "credentials.json")
}

func newOAuthClient(cfg *config, configPath string) *oauthClient {
	issuer := strings.TrimRight(cfg.OAuthIssuer, "/")
	if issuer == "" {
		issuer = defaultIssuer
	}
	clientID := cfg.OAuthClientID
	if clientID == "" {
		clientID = defaultClientID
	}
	return &oauthClient{
		issuer:   issuer,
		clientID: clientID,
		credPath: credentialsPath(configPath),
		hc:       &http.Client{Timeout: 30 * time.Second},
	}
}

// discover 拉一次发现文档，取授权端点和令牌端点。
func (c *oauthClient) discover(ctx context.Context) error {
	if c.ep.Token != "" {
		return nil
	}
	u := c.issuer + "/.well-known/openid-configuration"
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
	if err != nil {
		return err
	}
	resp, err := c.hc.Do(req)
	if err != nil {
		return fmt.Errorf("无法连接水鱼账号服务（%s）：%w", c.issuer, err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("水鱼账号服务返回了 %d", resp.StatusCode)
	}
	var ep endpoints
	if err := json.NewDecoder(resp.Body).Decode(&ep); err != nil {
		return fmt.Errorf("解析水鱼账号服务的发现文档失败：%w", err)
	}
	if ep.Authorization == "" || ep.Token == "" {
		return fmt.Errorf("水鱼账号服务的发现文档缺少必要的端点")
	}
	c.ep = ep
	return nil
}

func (c *oauthClient) load() error {
	b, err := os.ReadFile(c.credPath)
	if err != nil {
		return err
	}
	var tok oauthTokens
	if err := json.Unmarshal(b, &tok); err != nil {
		return err
	}
	if tok.RefreshToken == "" {
		return fmt.Errorf("凭据文件里没有 refresh token")
	}
	c.tok = tok
	return nil
}

// save 原子写。直接覆写的话，刷新成功、落盘写了一半断电，下次启动拿着
// 半截文件里的旧串去刷，服务端会按泄露处理把整条链吊销。
func (c *oauthClient) save() error {
	b, err := json.MarshalIndent(c.tok, "", "  ")
	if err != nil {
		return err
	}
	tmp := c.credPath + ".tmp"
	if err := os.WriteFile(tmp, b, 0600); err != nil {
		return err
	}
	return os.Rename(tmp, c.credPath)
}

func randomString(n int) (string, error) {
	b := make([]byte, n)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return base64.RawURLEncoding.EncodeToString(b), nil
}

// tokenRequest 换票。公开客户端**不带 client_secret**：登记的认证方式是
// none ，多送一个 secret 一样会被判成 invalid_client 。
func (c *oauthClient) tokenRequest(ctx context.Context, form url.Values) error {
	form.Set("client_id", c.clientID)
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.ep.Token,
		strings.NewReader(form.Encode()))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	resp, err := c.hc.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	var body struct {
		AccessToken      string `json:"access_token"`
		RefreshToken     string `json:"refresh_token"`
		ExpiresIn        int64  `json:"expires_in"`
		Scope            string `json:"scope"`
		Error            string `json:"error"`
		ErrorDescription string `json:"error_description"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		return fmt.Errorf("解析令牌响应失败（HTTP %d）：%w", resp.StatusCode, err)
	}
	if resp.StatusCode != http.StatusOK || body.Error != "" {
		msg := body.ErrorDescription
		if msg == "" {
			msg = body.Error
		}
		return fmt.Errorf("换取令牌失败（HTTP %d）：%s", resp.StatusCode, msg)
	}

	// 先校验再落库：这里一旦写进 c.tok ，手上那把还能用的旧 refresh token
	// 就没了，而它是重新授权之外唯一的退路
	if body.RefreshToken == "" {
		return fmt.Errorf("授权服务器未返回 refresh token")
	}
	c.tok = oauthTokens{
		AccessToken:  body.AccessToken,
		RefreshToken: body.RefreshToken,
		// 提前 60 秒过期，免得票在路上就到期了
		ExpiresAt: time.Now().Add(time.Duration(body.ExpiresIn-60) * time.Second).Unix(),
		Scope:     body.Scope,
	}
	return c.save()
}

// authorize 跑一遍完整的授权码流程：本机起一个只服务这一次回调的 HTTP
// 服务，把用户送去浏览器，收到授权码后立刻换票。
func (c *oauthClient) authorize(ctx context.Context) error {
	if err := c.discover(ctx); err != nil {
		return err
	}

	// 端口交给系统分配：写死的端口被占用就没有退路，而回环地址的端口
	// 不参与登记值比对
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return fmt.Errorf("无法在本机监听回调端口：%w", err)
	}
	defer ln.Close()
	redirectURI := fmt.Sprintf("http://127.0.0.1:%d%s",
		ln.Addr().(*net.TCPAddr).Port, callbackPath)

	verifier, err := randomString(32)
	if err != nil {
		return err
	}
	sum := sha256.Sum256([]byte(verifier))
	challenge := base64.RawURLEncoding.EncodeToString(sum[:])
	state, err := randomString(16)
	if err != nil {
		return err
	}

	type result struct {
		code string
		err  error
	}
	done := make(chan result, 1)
	mux := http.NewServeMux()
	mux.HandleFunc(callbackPath, func(w http.ResponseWriter, r *http.Request) {
		q := r.URL.Query()
		// state 必须自己核对：对不上说明这次回调不是本进程发起的那一次
		if q.Get("state") != state {
			writeCallbackPage(w, false, "回调校验失败，请重新授权。")
			done <- result{err: fmt.Errorf("state 不匹配，已中止授权")}
			return
		}
		if e := q.Get("error"); e != "" {
			desc := q.Get("error_description")
			if desc == "" {
				desc = e
			}
			writeCallbackPage(w, false, "授权未完成："+desc)
			done <- result{err: fmt.Errorf("用户未完成授权：%s", desc)}
			return
		}
		code := q.Get("code")
		if code == "" {
			writeCallbackPage(w, false, "回调中没有授权码，请重新授权。")
			done <- result{err: fmt.Errorf("回调中没有授权码")}
			return
		}
		writeCallbackPage(w, true, "授权成功，可以关闭本页面回到程序了。")
		done <- result{code: code}
	})
	srv := &http.Server{Handler: mux}
	go srv.Serve(ln)
	defer srv.Close()

	q := url.Values{
		"response_type":         {"code"},
		"client_id":             {c.clientID},
		"redirect_uri":          {redirectURI},
		"scope":                 {oauthScope},
		"state":                 {state},
		"code_challenge":        {challenge},
		"code_challenge_method": {"S256"},
	}
	authURL := c.ep.Authorization + "?" + q.Encode()

	fmt.Println()
	fmt.Println("=========================================================")
	fmt.Println("请在浏览器中登录水鱼账号并授权本程序上传你的成绩：")
	fmt.Println()
	fmt.Println("  " + authURL)
	fmt.Println()
	fmt.Println("若浏览器没有自动打开，请复制上面的地址手动访问。")
	fmt.Println("=========================================================")
	if err := openBrowser(authURL); err != nil {
		Log(LogLevelWarning, "无法自动打开浏览器：%s", err)
	}
	Log(LogLevelInfo, "正在等待授权完成……")

	waitCtx, cancel := context.WithTimeout(ctx, authorizeTimeout)
	defer cancel()
	var res result
	select {
	case res = <-done:
	case <-waitCtx.Done():
		return fmt.Errorf("等待授权超时，请重新运行本程序")
	}
	if res.err != nil {
		return res.err
	}

	if err := c.tokenRequest(ctx, url.Values{
		"grant_type":    {"authorization_code"},
		"code":          {res.code},
		"redirect_uri":  {redirectURI}, // 必须与授权请求里的完全一致
		"code_verifier": {verifier},
	}); err != nil {
		return err
	}
	Log(LogLevelInfo, "授权成功，凭据已保存到 %s", c.credPath)
	return nil
}

func (c *oauthClient) refresh(ctx context.Context) error {
	if err := c.discover(ctx); err != nil {
		return err
	}
	return c.tokenRequest(ctx, url.Values{
		"grant_type":    {"refresh_token"},
		"refresh_token": {c.tok.RefreshToken},
	})
}

// accessToken 返回一张还没过期的 access token，必要时先刷新。
func (c *oauthClient) accessToken(ctx context.Context) (string, error) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.tok.AccessToken != "" && time.Now().Unix() < c.tok.ExpiresAt {
		return c.tok.AccessToken, nil
	}
	if c.tok.RefreshToken == "" {
		return "", fmt.Errorf("尚未授权")
	}
	if err := c.refresh(ctx); err != nil {
		return "", err
	}
	return c.tok.AccessToken, nil
}

func (c *oauthClient) apply(req *http.Request) error {
	tok, err := c.accessToken(req.Context())
	if err != nil {
		return err
	}
	req.Header.Set("Authorization", "Bearer "+tok)
	return nil
}

func (c *oauthClient) describe() string { return "水鱼账号授权（OAuth）" }

func writeCallbackPage(w http.ResponseWriter, ok bool, msg string) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	title := "授权成功"
	if !ok {
		title = "授权失败"
		w.WriteHeader(http.StatusBadRequest)
	}
	fmt.Fprintf(w, `<!doctype html><meta charset="utf-8">
<title>%s · 水鱼查分器</title>
<body style="font-family:system-ui,sans-serif;margin:4rem auto;max-width:32rem;text-align:center">
<h1 style="font-size:1.5rem">%s</h1><p style="color:#555">%s</p></body>`, title, title, msg)
}

func openBrowser(target string) error {
	switch runtime.GOOS {
	case "windows":
		// 走 url.dll 而不是 cmd /c start：后者会把 URL 里的 & 当成命令分隔符
		return exec.Command("rundll32", "url.dll,FileProtocolHandler", target).Start()
	case "darwin":
		return exec.Command("open", target).Start()
	default:
		return exec.Command("xdg-open", target).Start()
	}
}
