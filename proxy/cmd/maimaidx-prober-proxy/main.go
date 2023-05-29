package main

import (
	"bufio"
	"crypto/tls"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/signal"
	"regexp"
	"strings"
	"syscall"

	"github.com/elazarl/goproxy"
)

var (
	ProxyEnable   uint64 = 39
	ProxyServer          = "rollback"
	AutoConfigURL        = "rollback"
)

func commandFatal(prompt string) {
	rollbackSystemProxySettings()
	fmt.Printf("%s请按 Enter 键继续……", prompt)
	bufio.NewReader(os.Stdin).ReadString('\n')
	os.Exit(0)
}

func main() {
	verbose := flag.Bool("v", false, "should every proxy request be logged to stdout")
	addr := flag.String("addr", ":8033", "proxy listen address")
	configPath := flag.String("config", "config.json", "path to config.json file")
	flag.Parse()

	cfg := initConfig(*configPath)

	apiClient := mustNewProberAPIClient(&cfg)

	applySystemProxySettings()
	// 搞个抓SIGINT的东西，×的时候可以关闭代理
	c := make(chan os.Signal)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	go func() {
		for range c {
			if ProxyEnable != 39 {
				rollbackSystemProxySettings()
			}
			os.Exit(0)
		}
	}()
	crt, _ := os.ReadFile("cert.crt")
	pem, _ := os.ReadFile("key.pem")
	goproxy.GoproxyCa, _ = tls.X509KeyPair(crt, pem)
	fmt.Println("使用此软件则表示您同意共享您在微信公众号舞萌 DX、中二节奏中的数据。")
	fmt.Println("您可以在微信客户端访问微信公众号舞萌 DX、中二节奏的个人信息主页进行分数导入，如需退出请直接关闭程序或按下 Ctrl + C")
	proxy := goproxy.NewProxyHttpServer()
	proxy.OnRequest(goproxy.ReqHostMatches(regexp.MustCompile("^(maimai|chunithm).wahlap.com:443.*$"))).
		HandleConnect(goproxy.AlwaysMitm)
	proxy.OnResponse().DoFunc(
		func(resp *http.Response, ctx *goproxy.ProxyCtx) *http.Response {
			if resp == nil || resp.Request == nil || resp.Request.URL == nil {
				return resp
			}
			path := resp.Request.URL.Path
			if regexp.MustCompile("^/maimai-mobile/home.*").MatchString(path) {
				resp.Body = io.NopCloser(strings.NewReader("<p>正在获取您的舞萌 DX 乐曲数据，请稍候……这可能需要花费数秒，具体进度可以在代理服务器的命令行窗口查看。</p><p>此页面仅用于提示您成功访问了代理服务器，您可以立即关闭此窗口。</p>"))
				if resp.StatusCode == 302 {
					commandFatal("访问舞萌 DX 的成绩界面出错。")
				}
				go apiClient.fetchData(resp.Request, resp.Cookies())
			}
			if regexp.MustCompile("^/mobile/home.*").MatchString(path) {
				resp.Body = io.NopCloser(strings.NewReader("<p>正在获取您的中二节奏乐曲数据，请稍候……这可能需要花费数秒，具体进度可以在代理服务器的命令行窗口查看。</p><p>此页面仅用于提示您成功访问了代理服务器，您可以立即关闭此窗口。</p>"))
				if resp.StatusCode == 302 {
					commandFatal("访问中二节奏的成绩界面出错。")
				}
				go apiClient.fetchDataChuni(resp.Request, resp.Cookies())
			}
			return resp
		})
	proxy.Verbose = *verbose
	log.Fatal(http.ListenAndServe(*addr, proxy))
}
