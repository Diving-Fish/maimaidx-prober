//go:build darwin

package main

import (
	"fmt"
	"os/exec"
)

type systemProxyManager struct{}

func newSystemProxyManager(addr string) *systemProxyManager {
	return &systemProxyManager{}
}

func (s *systemProxyManager) rollback() {
	cmd := exec.Command("networksetup", "-setwebproxystate", "off")
	cmd.Run()
}

func (s *systemProxyManager) apply() {
	cmd := exec.Command("networksetup", "-setwebproxy", "Wi-Fi", "127.0.0.1", "8033")
	err := cmd.Run()
	if err != nil {
		fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
		s.rollback()
		return
	}
	cmd2 := exec.Command("networksetup", "-setsecurewebproxy", "Wi-Fi", "127.0.0.1", "8033")
	err = cmd2.Run()
	if err != nil {
		fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
		s.rollback()
		return
	}
	fmt.Println("代理设置已自动修改。")
}
