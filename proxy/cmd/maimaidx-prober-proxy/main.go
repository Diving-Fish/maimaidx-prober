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
	flagSet := flag.NewFlagSet("proxy", flag.PanicOnError)

	flagSet.Bool("v", false, "should every proxy request be logged to stdout")
	flagSet.String("addr", ":8033", "proxy listen address")
	configPath := flagSet.String("config", "config.json", "path to config.json file")
	flagSet.Bool("no-edit-global-proxy", false, "don't edit the global proxy settings")
	flagSet.Bool("slice", false, "using more parts to import records")
	flagSet.Int("timeout", 30, "timeout when connect to servers")
	flagSet.String("mai-diffs", "", "mai diffs to import")

	checkUpdate()

	var spm *systemProxyManager
	commandFatal := func(err error) {
		if spm != nil {
			spm.rollback()
		}
		Log(LogLevelError, err.Error())
		fmt.Printf("请按 Enter 键继续……")
		bufio.NewReader(os.Stdin).ReadString('\n')
		os.Exit(0)
	}

	err := flagSet.Parse(os.Args[1:])
	if err != nil {
		commandFatal(fmt.Errorf("加载命令行参数出错，请检查您的参数"))
	}

	cfg, err := initConfig(*configPath)
	if err != nil {
		commandFatal(err)
	}

	err = cfg.FlagOverride(flagSet)
	if err != nil {
		commandFatal(err)
	}

	cfg.MaiIntDiffs, err = getMaiDiffs(cfg.MaiDiffs)
	if err != nil {
		commandFatal(err)
	}

	if !cfg.NoEditGlobalProxy {
		spm = newSystemProxyManager(cfg.Addr)
	}

	apiClient, err := newProberAPIClient(&cfg, cfg.NetworkTimeout)
	if err != nil {
		commandFatal(err)
	}
	proxyCtx := newProxyContext(apiClient, commandFatal, cfg.Verbose)

	Log(LogLevelInfo, "使用此软件则表示您同意共享您在微信公众号舞萌 DX、中二节奏中的数据。")
	Log(LogLevelInfo, "您可以在微信客户端访问微信公众号舞萌 DX、中二节奏的个人信息主页进行分数导入，如需退出请直接关闭程序或按下 Ctrl + C")

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

	if host, _, err := net.SplitHostPort(cfg.Addr); err == nil && host == "" {
		// hack
		cfg.Addr = "127.0.0.1" + cfg.Addr
	}
	Log(LogLevelInfo, "代理已开启到 %s", cfg.Addr)

	log.Fatal(http.ListenAndServe(cfg.Addr, srv))
}
