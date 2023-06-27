package main

import (
	"net"
	"os/exec"
)

const (
	NETWORK_DEVICE_NAME = "Wi-Fi"
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
	Log(LogLevelInfo, "正在尝试自动回滚代理设置。")
	cmds := []string{"-setwebproxystate", "-setsecurewebproxystate"}
	for _, v := range cmds {
		cmd := exec.Command("networksetup", v, NETWORK_DEVICE_NAME, "off")
		err := cmd.Run()
		if err != nil {
			Log(LogLevelWarning, "自动回滚代理设置失败。请尝试手动修改代理。")
			return
		}
	}
}

func (s *systemProxyManager) apply() {
	host, port, err := net.SplitHostPort(s.addr)
	if err != nil {
		Log(LogLevelWarning, "自动修改代理设置失败。请尝试手动修改代理。")
		return
	}
	if host == "" {
		host = "127.0.0.1"
	}
	cmds := []string{"-setwebproxy", "-setsecurewebproxy"}
	for _, v := range cmds {
		cmd := exec.Command("networksetup", v, NETWORK_DEVICE_NAME, host, port)
		err := cmd.Run()
		if err != nil {
			Log(LogLevelWarning, "自动修改代理设置失败。请尝试手动修改代理。")
			s.rollback()
			return
		}
	}
	Log(LogLevelInfo, "代理设置已自动修改。")
}
