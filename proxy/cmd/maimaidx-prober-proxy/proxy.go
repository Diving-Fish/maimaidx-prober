package main

import (
	"bytes"
	_ "embed"
	"errors"
	"html/template"
	"io"
	"net/http"
	"regexp"
	"strconv"
	"strings"

	"github.com/elazarl/goproxy"
)

type proxyContext struct {
	prober       *proberAPIClient
	verbose      bool
	fatalHandler func(error)
}

func newProxyContext(
	prober *proberAPIClient,
	fatalHandler func(error),
	verbose bool,
) *proxyContext {
	return &proxyContext{
		prober:       prober,
		verbose:      verbose,
		fatalHandler: fatalHandler,
	}
}

//go:embed prompt_maimai.html
var promptMaimaiSrc string

//go:embed prompt_chuni.html
var promptChuniSrc string

var (
	promptMaimaiTpl = template.Must(template.New("mai").Parse(promptMaimaiSrc))
	promptChuniTpl  = template.Must(template.New("chuni").Parse(promptChuniSrc))
)

type promptData struct {
	WSPath string
}

func renderPrompt(tpl *template.Template) []byte {
	var buf bytes.Buffer
	_ = tpl.Execute(&buf, promptData{WSPath: progressPath()})
	return buf.Bytes()
}

func writePromptResponse(resp *http.Response, body []byte) {
	resp.Body = io.NopCloser(bytes.NewReader(body))
	resp.ContentLength = int64(len(body))
	resp.Header.Set("Content-Type", "text/html; charset=utf-8")
	resp.Header.Set("Content-Length", strconv.Itoa(len(body)))
	resp.Header.Del("Content-Encoding")
	resp.Header.Set("Cache-Control", "no-store")
}

func (p *proxyContext) handleResponse(resp *http.Response, ctx *goproxy.ProxyCtx) *http.Response {
	if resp == nil || resp.Request == nil || resp.Request.URL == nil {
		return resp
	}

	path := resp.Request.URL.Path
	switch {
	case strings.HasPrefix(path, "/maimai-mobile/home"):
		writePromptResponse(resp, renderPrompt(promptMaimaiTpl))
		if resp.StatusCode == 302 {
			p.fatalHandler(errors.New("访问舞萌 DX 的成绩界面出错。"))
		}
		go p.prober.fetchDataMaimai(resp.Request, resp.Cookies())

	case strings.HasPrefix(path, "/mobile/home"):
		writePromptResponse(resp, renderPrompt(promptChuniTpl))
		if resp.StatusCode == 302 {
			p.fatalHandler(errors.New("访问中二节奏的成绩界面出错。"))
		}
		go p.prober.fetchDataChuni(resp.Request, resp.Cookies())
	}

	return resp
}

// handleProgressRequest intercepts the WebSocket upgrade for our hidden
// progress endpoint and short-circuits the round-trip to wahlap.
func (p *proxyContext) handleProgressRequest(req *http.Request, ctx *goproxy.ProxyCtx) (*http.Request, *http.Response) {
	if resp := tryHandleProgressUpgrade(req); resp != nil {
		return req, resp
	}
	return req, nil
}

func (p *proxyContext) makeProxyServer() *goproxy.ProxyHttpServer {
	proxy := goproxy.NewProxyHttpServer()
	proxy.Verbose = p.verbose
	proxy.OnRequest(goproxy.ReqHostMatches(regexp.MustCompile("^(maimai|chunithm).wahlap.com:443.*$"))).
		HandleConnect(goproxy.AlwaysMitm)
	// Intercept our hidden progress endpoint *before* it is round-tripped to
	// wahlap. Matches the inner request inside a MITM'd TLS tunnel, where Host
	// has no port suffix.
	proxy.OnRequest(goproxy.ReqHostMatches(regexp.MustCompile(`^(maimai|chunithm)\.wahlap\.com$`))).
		DoFunc(p.handleProgressRequest)
	proxy.OnResponse().DoFunc(p.handleResponse)

	return proxy
}
