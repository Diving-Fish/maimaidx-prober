//go:build darwin
// +build darwin

package main

import (
	"fmt"
	"os/exec"
)

const (
	NETWORK_DEVICE_NAME = "Wi-Fi"
)

func rollbackSystemProxySettings() {
	fmt.Println("正在尝试自动回滚代理设置。")
	cmds := []string{"-setwebproxystate", "-setsecurewebproxystate"}
	for _, v := range cmds {
		cmd := exec.Command("networksetup", v, NETWORK_DEVICE_NAME, "off")
		err := cmd.Run()
		if err != nil {
			fmt.Println("自动回滚代理设置失败。请尝试手动修改代理。")
			return
		}
	}
}

func applySystemProxySettings() {
	cmds := []string{"-setwebproxy", "-setsecurewebproxy"}
	for _, v := range cmds {
		cmd := exec.Command("networksetup", v, NETWORK_DEVICE_NAME, "127.0.0.1", "8033")
		err := cmd.Run()
		if err != nil {
			fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
			rollbackSystemProxySettings()
			return
		}
	}
	fmt.Println("代理设置已自动修改。")
}
