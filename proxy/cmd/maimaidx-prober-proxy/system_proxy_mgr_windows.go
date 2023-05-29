//go:build windows

package main

import (
	"fmt"
	"net"
	"syscall"

	"golang.org/x/sys/windows/registry"

	"github.com/Diving-Fish/maimaidx-prober/proxy/lib"
)

type systemProxyManager struct {
	ProxyEnable   uint64
	ProxyServer   string
	AutoConfigURL string
	addr          string
}

func newSystemProxyManager(addr string) *systemProxyManager {
	return &systemProxyManager{
		ProxyEnable:   39,
		ProxyServer:   "rollback",
		AutoConfigURL: "rollback",
		addr:          addr,
	}
}

func (s *systemProxyManager) rollback() {
	if s.ProxyEnable == 39 {
		return
	}
	key, _, _ := registry.CreateKey(registry.CURRENT_USER, `SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings`, registry.ALL_ACCESS)
	defer key.Close()
	key.SetDWordValue("ProxyEnable", uint32(s.ProxyEnable))
	if s.ProxyServer != "rollback" {
		key.SetStringValue("ProxyServer", s.ProxyServer)
	}
	if s.AutoConfigURL != "rollback" {
		key.SetStringValue("AutoConfigURL", s.AutoConfigURL)
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
	s.ProxyEnable, _, err = key.GetIntegerValue("ProxyEnable")
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
	s.ProxyServer, _, err = key.GetStringValue("ProxyServer")
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
	s.AutoConfigURL, _, err = key.GetStringValue("AutoConfigURL")
	if err != nil {
		if err == syscall.ENOENT {
			s.AutoConfigURL = "rollback"
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
