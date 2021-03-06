//+build windows

package main

import (
	"fmt"
	"syscall"

	"golang.org/x/sys/windows/registry"

	"github.com/Diving-Fish/maimaidx-prober/proxy/lib"
)

func rollbackSystemProxySettings() {
	if ProxyEnable == 39 {
		return
	}
	key, _, _ := registry.CreateKey(registry.CURRENT_USER, `SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings`, registry.ALL_ACCESS)
	defer key.Close()
	key.SetDWordValue("ProxyEnable", uint32(ProxyEnable))
	if ProxyServer != "rollback" {
		key.SetStringValue("ProxyServer", ProxyServer)
	}
	if AutoConfigURL != "rollback" {
		key.SetStringValue("AutoConfigURL", AutoConfigURL)
	}
	_, _ = lib.InternetOptionSettingsChanged()
}

func applySystemProxySettings() {
	_, err := lib.InternetOptionSettingsChanged()
	if err != nil {
		fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
		return
	}
	key, _, _ := registry.CreateKey(registry.CURRENT_USER, `SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings`, registry.ALL_ACCESS)
	defer key.Close()
	ProxyEnable, _, err = key.GetIntegerValue("ProxyEnable")
	if err != nil {
		fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
		rollbackSystemProxySettings()
		return
	}
	err = key.SetDWordValue("ProxyEnable", 1)
	if err != nil {
		fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
		rollbackSystemProxySettings()
		return
	}
	ProxyServer, _, err = key.GetStringValue("ProxyServer")
	if err != nil {
		fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
		rollbackSystemProxySettings()
		return
	}
	err = key.SetStringValue("ProxyServer", "127.0.0.1:8033")
	if err != nil {
		fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
		rollbackSystemProxySettings()
		return
	}
	AutoConfigURL, _, err = key.GetStringValue("AutoConfigURL")
	if err != nil {
		if err == syscall.ENOENT {
			AutoConfigURL = "rollback"
		} else {
			fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
			rollbackSystemProxySettings()
			return
		}
	}
	err = key.DeleteValue("AutoConfigURL")
	if err != nil && err != syscall.ENOENT {
		fmt.Println("自动修改代理设置失败。请尝试手动修改代理。")
		rollbackSystemProxySettings()
		return
	}
	_, _ = lib.InternetOptionSettingsChanged()
	fmt.Println("代理设置已自动修改。")
}
