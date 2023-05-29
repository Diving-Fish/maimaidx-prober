//go:build !darwin && !windows

package main

type systemProxyManager struct{}

func newSystemProxyManager(addr string) *systemProxyManager {
	return &systemProxyManager{}
}

func (*systemProxyManager) rollback() {
	// unsupported on this platform
}

func (*systemProxyManager) apply() {
	// unsupported on this platform
}
