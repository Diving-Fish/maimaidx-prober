//go:build !windows && !darwin

package main

import "fmt"

// installCert is intentionally not implemented on Linux/other Unix systems:
// there is no portable way to install a CA across distributions and browser
// trust stores (NSS) without root and per-distro logic. Users should follow
// the README instructions for their distribution.
func installCert(certFile string) error {
	return fmt.Errorf(
		"当前系统不支持自动安装根证书，请按照说明手动安装：\n"+
			"  Debian/Ubuntu: sudo cp %[1]s /usr/local/share/ca-certificates/maimaidx-prober.crt && sudo update-ca-certificates\n"+
			"  RHEL/Fedora:   sudo cp %[1]s /etc/pki/ca-trust/source/anchors/maimaidx-prober.crt && sudo update-ca-trust extract\n"+
			"  Arch Linux:    sudo trust anchor --store %[1]s\n"+
			"如使用 Chrome/Firefox，可能还需要使用 certutil 写入 NSS 数据库",
		certFile,
	)
}

// isCertInstalled cannot reliably detect installation across distributions.
// Returning true means the auto-install step is a no-op, leaving the manual
// install instructions in the README as the source of truth.
func isCertInstalled(thumb string) bool { return true }

func uninstallCert(certFile string) error {
	return fmt.Errorf(
		"当前系统不支持自动卸载根证书，请按照说明手动操作：\n"+
			"  Debian/Ubuntu: sudo rm /usr/local/share/ca-certificates/maimaidx-prober.crt && sudo update-ca-certificates --fresh\n"+
			"  RHEL/Fedora:   sudo rm /etc/pki/ca-trust/source/anchors/maimaidx-prober.crt && sudo update-ca-trust extract\n"+
			"  Arch Linux:    sudo trust anchor --remove %s",
		certFile,
	)
}
