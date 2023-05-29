//go:build !darwin && !windows

package main

func rollbackSystemProxySettings() {
	// unsupported on this platform
}

func applySystemProxySettings() {
	// unsupported on this platform
}
