package main

import (
	"bufio"
	"crypto/tls"
	"flag"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/elazarl/goproxy"
)

func patchGoproxyCert() {
	certPath := "cert.crt"
	privateKeyPath := "key.pem"
	crt, _ := os.ReadFile(certPath)
	pem, _ := os.ReadFile(privateKeyPath)
	goproxy.GoproxyCa, _ = tls.X509KeyPair(crt, pem)
}

func main() {
	verbose := flag.Bool("v", false, "should every proxy request be logged to stdout")
	addr := flag.String("addr", ":8033", "proxy listen address")
	configPath := flag.String("config", "config.json", "path to config.json file")
	noEditGlobalProxy := flag.Bool("no-edit-global-proxy", false, "don't edit the global proxy settings")
	flag.Parse()

	var spm *systemProxyManager
	if !*noEditGlobalProxy {
		spm = newSystemProxyManager(*addr)
	}

	commandFatal := func(err error) {
		if spm != nil {
			spm.rollback()
		}
		fmt.Printf("%s\n请按 Enter 键继续……", err.Error())
		bufio.NewReader(os.Stdin).ReadString('\n')
		os.Exit(0)
	}

	cfg, err := initConfig(*configPath)
	if err != nil {
		commandFatal(err)
	}

	apiClient, err := newProberAPIClient(&cfg)
	if err != nil {
		commandFatal(err)
	}
	proxyCtx := newProxyContext(apiClient, commandFatal, *verbose)

	fmt.Println("使用此软件则表示您同意共享您在微信公众号舞萌 DX、中二节奏中的数据。")
	fmt.Println("您可以在微信客户端访问微信公众号舞萌 DX、中二节奏的个人信息主页进行分数导入，如需退出请直接关闭程序或按下 Ctrl + C")

	if spm != nil {
		spm.apply()
	}

	// 搞个抓SIGINT的东西，×的时候可以关闭代理
	c := make(chan os.Signal)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	go func() {
		for range c {
			if spm != nil {
				spm.rollback()
			}
			os.Exit(0)
		}
	}()

	patchGoproxyCert()
	srv := proxyCtx.makeProxyServer()

	if host, _, err := net.SplitHostPort(*addr); err == nil && host == "" {
		// hack
		*addr = "127.0.0.1" + *addr
	}
	fmt.Printf("代理已开启到 %s\n", *addr)

	log.Fatal(http.ListenAndServe(*addr, srv))
}
