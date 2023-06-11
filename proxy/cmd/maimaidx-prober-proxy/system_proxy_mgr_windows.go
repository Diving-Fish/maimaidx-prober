package main

import (
	"fmt"
	"net"
	"syscall"

	"golang.org/x/sys/windows/registry"

	"github.com/Diving-Fish/maimaidx-prober/proxy/lib"
)

type systemProxyManager struct {
	proxyEnable   uint64
	proxyServer   string
	autoConfigURL string
	addr          string
}

func newSystemProxyManager(addr string) *systemProxyManager {
	return &systemProxyManager{
		proxyEnable:   39,
		proxyServer:   "rollback",
		autoConfigURL: "rollback",
		addr:          addr,
	}
}

func (s *systemProxyManager) rollback() {
	if s.proxyEnable == 39 {
		return
	}
	key, _, _ := registry.CreateKey(registry.CURRENT_USER, `SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings`, registry.ALL_ACCESS)
	defer key.Close()
	key.SetDWordValue("ProxyEnable", uint32(s.proxyEnable))
	if s.proxyServer != "rollback" {
		key.SetStringValue("ProxyServer", s.proxyServer)
	}
	if s.autoConfigURL != "rollback" {
		key.SetStringValue("AutoConfigURL", s.autoConfigURL)
	}
	_, _ = lib.InternetOptionSettingsChanged()
}

func (s *systemProxyManager) apply() {
	host, port, err := net.SplitHostPort(s.addr)
	if err != nil {
		fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
		return
	}
	if host == "" {
		host = "127.0.0.1"
	}
	newProxyServerStr := host + ":" + port

	_, err = lib.InternetOptionSettingsChanged()
	if err != nil {
		fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
		return
	}
	key, _, _ := registry.CreateKey(registry.CURRENT_USER, `SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings`, registry.ALL_ACCESS)
	defer key.Close()
	s.proxyEnable, _, err = key.GetIntegerValue("ProxyEnable")
	if err != nil {
		fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
		s.rollback()
		return
	}
	err = key.SetDWordValue("ProxyEnable", 1)
	if err != nil {
		fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
		s.rollback()
		return
	}
	s.proxyServer, _, err = key.GetStringValue("ProxyServer")
	if err != nil {
		fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
		s.rollback()
		return
	}
	err = key.SetStringValue("ProxyServer", newProxyServerStr)
	if err != nil {
		fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
		s.rollback()
		return
	}
	s.autoConfigURL, _, err = key.GetStringValue("AutoConfigURL")
	if err != nil {
		if err == syscall.ENOENT {
			s.autoConfigURL = "rollback"
		} else {
			fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
			s.rollback()
			return
		}
	}
	err = key.DeleteValue("AutoConfigURL")
	if err != nil && err != syscall.ENOENT {
		fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
		s.rollback()
		return
	}
	_, _ = lib.InternetOptionSettingsChanged()
	fmt.Println("代理设置已自动修改。")
}
