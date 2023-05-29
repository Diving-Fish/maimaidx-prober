package main

import (
	"bytes"
	_ "embed"
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

//go:embed prompt_maimai.html
var promptMaimai []byte

//go:embed prompt_chuni.html
var promptChuni []byte

func (p *proxyContext) handleResponse(resp *http.Response, ctx *goproxy.ProxyCtx) *http.Response {
	if resp == nil || resp.Request == nil || resp.Request.URL == nil {
		return resp
	}

	path := resp.Request.URL.Path
	switch {
	case strings.HasPrefix(path, "/maimai-mobile/home"):
		resp.Body = io.NopCloser(bytes.NewReader(promptMaimai))
		if resp.StatusCode == 302 {
			p.fatalHandler(errors.New("访问舞萌 DX 的成绩界面出错。"))
		}
		go p.prober.fetchDataMaimai(resp.Request, resp.Cookies())

	case strings.HasPrefix(path, "/mobile/home"):
		resp.Body = io.NopCloser(bytes.NewReader(promptChuni))
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
