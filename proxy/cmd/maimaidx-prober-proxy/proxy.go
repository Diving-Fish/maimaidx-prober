package main

import (
	"errors"
	"io"
	"net/http"
	"regexp"
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

func (p *proxyContext) handleResponse(resp *http.Response, ctx *goproxy.ProxyCtx) *http.Response {
	if resp == nil || resp.Request == nil || resp.Request.URL == nil {
		return resp
	}

	path := resp.Request.URL.Path
	if regexp.MustCompile("^/maimai-mobile/home.*").MatchString(path) {
		resp.Body = io.NopCloser(strings.NewReader("<p>正在获取您的舞萌 DX 乐曲数据，请稍候……这可能需要花费数秒，具体进度可以在代理服务器的命令行窗口查看。</p><p>此页面仅用于提示您成功访问了代理服务器，您可以立即关闭此窗口。</p>"))
		if resp.StatusCode == 302 {
			p.fatalHandler(errors.New("访问舞萌 DX 的成绩界面出错。"))
		}
		go p.prober.fetchData(resp.Request, resp.Cookies())
	}

	if regexp.MustCompile("^/mobile/home.*").MatchString(path) {
		resp.Body = io.NopCloser(strings.NewReader("<p>正在获取您的中二节奏乐曲数据，请稍候……这可能需要花费数秒，具体进度可以在代理服务器的命令行窗口查看。</p><p>此页面仅用于提示您成功访问了代理服务器，您可以立即关闭此窗口。</p>"))
		if resp.StatusCode == 302 {
			p.fatalHandler(errors.New("访问中二节奏的成绩界面出错。"))
		}
		go p.prober.fetchDataChuni(resp.Request, resp.Cookies())
	}

	return resp
}

func (p *proxyContext) makeProxyServer() *goproxy.ProxyHttpServer {
	proxy := goproxy.NewProxyHttpServer()
	proxy.Verbose = p.verbose
	proxy.OnRequest(goproxy.ReqHostMatches(regexp.MustCompile("^(maimai|chunithm).wahlap.com:443.*$"))).
		HandleConnect(goproxy.AlwaysMitm)
	proxy.OnResponse().DoFunc(p.handleResponse)

	return proxy
}
