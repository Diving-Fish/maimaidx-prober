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
	"path/filepath"
	"syscall"

	"github.com/elazarl/goproxy"
)

func patchGoproxyCert() error {
	cp, err := certPath()
	if err != nil {
		return err
	}
	kp, err := keyPath()
	if err != nil {
		return err
	}
	crt, err := os.ReadFile(cp)
	if err != nil {
		return fmt.Errorf("读取证书失败 (%s): %w", cp, err)
	}
	key, err := os.ReadFile(kp)
	if err != nil {
		return fmt.Errorf("读取私钥失败 (%s): %w", kp, err)
	}
	pair, err := tls.X509KeyPair(crt, key)
	if err != nil {
		return fmt.Errorf("解析证书/私钥失败: %w", err)
	}
	goproxy.GoproxyCa = pair
	return nil
}

func main() {
	flagSet := flag.NewFlagSet("proxy", flag.PanicOnError)

	flagSet.Bool("v", false, "should every proxy request be logged to stdout")
	flagSet.String("addr", ":8033", "proxy listen address")
	ex, _ := os.Executable()
	exPath := filepath.Dir(ex)
	configPath := flagSet.String("config", exPath+"/config.json", "path to config.json file")
	flagSet.Bool("no-edit-global-proxy", false, "don't edit the global proxy settings")
	flagSet.Bool("slice", false, "using more parts to import records")
	flagSet.Int("timeout", 30, "timeout when connect to servers")
	flagSet.String("mai-diffs", "", "mai diffs to import")
	doInstallCert := flagSet.Bool("install-cert", false, "install the local CA into the OS root store and exit")
	doUninstallCert := flagSet.Bool("uninstall-cert", false, "remove the local CA from the OS root store and exit")

	checkUpdate()
	initProgress()

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

	// Subcommands that operate on the local CA. They run before initConfig so
	// they don't require a populated config.json (only the cert/key files).
	if *doInstallCert || *doUninstallCert {
		if err := ensureCertExists(); err != nil {
			commandFatal(err)
		}
		cp, _ := certPath()
		var cerr error
		if *doInstallCert {
			cerr = installCert(cp)
		} else {
			cerr = uninstallCert(cp)
		}
		if cerr != nil {
			commandFatal(cerr)
		}
		Log(LogLevelInfo, "操作完成")
		fmt.Printf("请按 Enter 键继续……")
		bufio.NewReader(os.Stdin).ReadString('\n')
		return
	}

	cfg, err := initConfig(*configPath)
	if err != nil {
		commandFatal(err)
	}

	// Make sure the local CA is generated and installed into the OS trust
	// store BEFORE we ask the user for their token. On Windows this may
	// trigger a UAC prompt; on macOS a keychain password prompt. Idempotent:
	// if the cert is already trusted, this is a fast no-op.
	if err := ensureCertInstalled(); err != nil {
		commandFatal(fmt.Errorf("证书安装失败：%w", err))
	}

	// Interactively collect & validate the Import-Token if the config does
	// not already contain a working one.
	if err := ensureToken(&cfg, *configPath); err != nil {
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

	if err := patchGoproxyCert(); err != nil {
		commandFatal(err)
	}
	srv := proxyCtx.makeProxyServer()

	if host, _, err := net.SplitHostPort(cfg.Addr); err == nil && host == "" {
		// hack
		cfg.Addr = "127.0.0.1" + cfg.Addr
	}
	Log(LogLevelInfo, "代理已开启到 %s", cfg.Addr)

	log.Fatal(http.ListenAndServe(cfg.Addr, srv))
}
