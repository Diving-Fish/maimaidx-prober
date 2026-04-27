package main

import (
	"crypto/sha1"
	"crypto/x509"
	"encoding/hex"
	"encoding/pem"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"

	"github.com/Diving-Fish/maimaidx-prober/proxy/lib"
)

// ensureCertExists makes sure the local CA cert and private key are present
// on disk. If either file is missing, a fresh CA is generated. Returns an
// error if generation fails.
func ensureCertExists() error {
	cp, err := certPath()
	if err != nil {
		return err
	}
	kp, err := keyPath()
	if err != nil {
		return err
	}
	_, certErr := os.Stat(cp)
	_, keyErr := os.Stat(kp)
	if certErr == nil && keyErr == nil {
		return nil
	}
	return lib.GenerateCertTo(lib.CertOptions{CertPath: cp, KeyPath: kp})
}

// dataDir returns the per-user directory where the local CA and its private
// key are stored. On first call it creates the directory with conservative
// permissions (0700), so the private key is only readable by the current
// user even though it's written with 0600 separately.
func dataDir() (string, error) {
	var base string
	switch runtime.GOOS {
	case "windows":
		base = os.Getenv("LOCALAPPDATA")
		if base == "" {
			base = os.Getenv("APPDATA")
		}
	case "darwin":
		home, err := os.UserHomeDir()
		if err != nil {
			return "", err
		}
		base = filepath.Join(home, "Library", "Application Support")
	default:
		if x := os.Getenv("XDG_DATA_HOME"); x != "" {
			base = x
		} else {
			home, err := os.UserHomeDir()
			if err != nil {
				return "", err
			}
			base = filepath.Join(home, ".local", "share")
		}
	}
	if base == "" {
		return "", errors.New("cannot determine user data directory")
	}
	dir := filepath.Join(base, "maimaidx-prober")
	if err := os.MkdirAll(dir, 0700); err != nil {
		return "", err
	}
	return dir, nil
}

// certPath / keyPath return the resolved paths for the local CA. They prefer
// the per-user data directory but fall back to the executable's directory if
// a legacy cert.crt / key.pem is found there (kept for backward compatibility
// with previously-shipped releases).
func certPath() (string, error) { return resolveCertFile("cert.crt") }
func keyPath() (string, error)  { return resolveCertFile("key.pem") }

func resolveCertFile(name string) (string, error) {
	dir, err := dataDir()
	if err != nil {
		return "", err
	}
	pref := filepath.Join(dir, name)
	if _, err := os.Stat(pref); err == nil {
		return pref, nil
	}
	// Backward compat: check the executable directory.
	if exe, err := os.Executable(); err == nil {
		legacy := filepath.Join(filepath.Dir(exe), name)
		if _, err := os.Stat(legacy); err == nil {
			return legacy, nil
		}
	}
	// Default to the new location even if the file does not exist yet (the
	// caller is expected to create it).
	return pref, nil
}

// readCertificate parses the PEM file at path and returns the first
// CERTIFICATE block as an *x509.Certificate.
func readCertificate(path string) (*x509.Certificate, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	for {
		block, rest := pem.Decode(raw)
		if block == nil {
			return nil, fmt.Errorf("no CERTIFICATE block found in %s", path)
		}
		if block.Type == "CERTIFICATE" {
			return x509.ParseCertificate(block.Bytes)
		}
		raw = rest
	}
}

// certThumbprintHex returns the uppercase hex SHA-1 thumbprint of the given
// certificate, matching the format certutil/keychain expect.
func certThumbprintHex(cert *x509.Certificate) string {
	sum := sha1.Sum(cert.Raw)
	return strings.ToUpper(hex.EncodeToString(sum[:]))
}
