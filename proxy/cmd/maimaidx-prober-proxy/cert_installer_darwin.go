//go:build darwin

package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// userKeychain returns the path to the current user's login keychain.
func userKeychain() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	candidates := []string{
		filepath.Join(home, "Library", "Keychains", "login.keychain-db"),
		filepath.Join(home, "Library", "Keychains", "login.keychain"),
	}
	for _, p := range candidates {
		if _, err := os.Stat(p); err == nil {
			return p, nil
		}
	}
	// Fallback: let `security` resolve the default keychain.
	out, err := exec.Command("security", "default-keychain").Output()
	if err != nil {
		return "", fmt.Errorf("无法定位 login keychain: %w", err)
	}
	return strings.Trim(strings.TrimSpace(string(out)), `"`), nil
}

// installCert installs the local CA into the user's login keychain and marks
// it as trustRoot. The system pops a single SecurityAgent dialog asking for
// the user password; no further clicking is required.
func installCert(certFile string) error {
	kc, err := userKeychain()
	if err != nil {
		return err
	}
	cmd := exec.Command("security", "add-trusted-cert",
		"-r", "trustRoot",
		"-k", kc,
		certFile)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("security add-trusted-cert 失败: %w\n%s", err, strings.TrimSpace(string(out)))
	}
	Log(LogLevelInfo, "证书已安装到 login keychain 并标记为信任根")
	return nil
}

// isCertInstalled reports whether a certificate with the given SHA-1
// thumbprint already lives in the user's login keychain.
func isCertInstalled(thumb string) bool {
	kc, err := userKeychain()
	if err != nil {
		return false
	}
	err = exec.Command("security", "find-certificate", "-Z", thumb, kc).Run()
	return err == nil
}

// uninstallCert removes the local CA from the user's login keychain by SHA-1
// hash, which uniquely identifies the certificate even if multiple share the
// same Common Name.
func uninstallCert(certFile string) error {
	cert, err := readCertificate(certFile)
	if err != nil {
		return fmt.Errorf("读取证书失败: %w", err)
	}
	thumb := certThumbprintHex(cert)
	kc, err := userKeychain()
	if err != nil {
		return err
	}
	cmd := exec.Command("security", "delete-certificate", "-Z", thumb, kc)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("security delete-certificate 失败: %w\n%s", err, strings.TrimSpace(string(out)))
	}
	Log(LogLevelInfo, "证书已从 login keychain 中移除")
	return nil
}
