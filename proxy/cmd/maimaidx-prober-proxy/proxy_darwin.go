//+build darwin

package main

import (
	"fmt"
	"os/exec"
)

func rollbackSystemProxySettings() {
	cmd := exec.Command("networksetup", "-setwebproxystate", "off")
	cmd.Run()
}

func applySystemProxySettings() {
	cmd := exec.Command("networksetup", "-setwebproxy", "Wi-Fi", "127.0.0.1", "8033")
	err := cmd.Run()
	if err != nil {
		fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
		rollbackSystemProxySettings()
		return
	}
	cmd2 := exec.Command("networksetup", "-setsecurewebproxy", "Wi-Fi", "127.0.0.1", "8033")
	err = cmd2.Run()
	if err != nil {
		fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
		rollbackSystemProxySettings()
		return
	}
	fmt.Println("代理设置已自动修改。")
}
