//go:build darwin

package main

import (
	"fmt"
	"net"
	"os/exec"
)

type systemProxyManager struct {
	addr string
}

func newSystemProxyManager(addr string) *systemProxyManager {
	return &systemProxyManager{
		addr: addr,
	}
}

func (s *systemProxyManager) rollback() {
	cmd := exec.Command("networksetup", "-setwebproxystate", "off")
	cmd.Run()
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

	cmd := exec.Command("networksetup", "-setwebproxy", "Wi-Fi", host, port)
	err = cmd.Run()
	if err != nil {
		fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
		s.rollback()
		return
	}
	cmd2 := exec.Command("networksetup", "-setsecurewebproxy", "Wi-Fi", host, port)
	err = cmd2.Run()
	if err != nil {
		fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
		s.rollback()
		return
	}
	fmt.Println("代理设置已自动修改。")
}
