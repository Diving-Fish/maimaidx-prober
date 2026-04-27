package lib

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"fmt"
	"math/big"
	"os"
	"time"
)

// CertOptions configures CA generation.
type CertOptions struct {
	CertPath string // where to write the PEM-encoded certificate
	KeyPath  string // where to write the PEM-encoded PKCS#8 private key
	// PermittedDNSDomains restricts the issued CA so it can only sign leaf
	// certificates whose DNS SANs fall under one of these domains. Leaving
	// it empty disables Name Constraints (NOT recommended).
	PermittedDNSDomains []string
	Validity            time.Duration // certificate validity (default 2 years)
	CommonName          string        // subject common name (default: "maimaidx-prober Local Root CA")
}

// GenerateCertTo creates a fresh self-signed CA limited (via Name Constraints)
// to the configured DNS domains and writes both the certificate and its
// private key to disk. The private key file is created with mode 0600.
//
// The CA is intended to be installed into the OS root store; restricting it
// with Name Constraints means leakage of the private key cannot be abused to
// MITM unrelated HTTPS traffic.
func GenerateCertTo(opts CertOptions) error {
	if opts.CertPath == "" || opts.KeyPath == "" {
		return fmt.Errorf("cert/key path required")
	}
	if opts.Validity <= 0 {
		opts.Validity = 2 * 365 * 24 * time.Hour
	}
	if opts.CommonName == "" {
		opts.CommonName = "maimaidx-prober Local Root CA"
	}
	if len(opts.PermittedDNSDomains) == 0 {
		opts.PermittedDNSDomains = []string{"wahlap.com"}
	}

	priv, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return fmt.Errorf("generate key: %w", err)
	}

	serialLimit := new(big.Int).Lsh(big.NewInt(1), 128)
	serial, err := rand.Int(rand.Reader, serialLimit)
	if err != nil {
		return fmt.Errorf("generate serial: %w", err)
	}

	now := time.Now()
	tpl := x509.Certificate{
		SerialNumber: serial,
		Subject: pkix.Name{
			CommonName:   opts.CommonName,
			Organization: []string{"maimaidx-prober"},
		},
		NotBefore:                   now.Add(-time.Hour),
		NotAfter:                    now.Add(opts.Validity),
		KeyUsage:                    x509.KeyUsageDigitalSignature | x509.KeyUsageKeyEncipherment | x509.KeyUsageCertSign,
		ExtKeyUsage:                 []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
		BasicConstraintsValid:       true,
		IsCA:                        true,
		MaxPathLenZero:              true,
		PermittedDNSDomainsCritical: true,
		PermittedDNSDomains:         opts.PermittedDNSDomains,
	}

	der, err := x509.CreateCertificate(rand.Reader, &tpl, &tpl, &priv.PublicKey, priv)
	if err != nil {
		return fmt.Errorf("create certificate: %w", err)
	}

	certOut, err := os.OpenFile(opts.CertPath, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0644)
	if err != nil {
		return fmt.Errorf("open cert file: %w", err)
	}
	if err := pem.Encode(certOut, &pem.Block{Type: "CERTIFICATE", Bytes: der}); err != nil {
		_ = certOut.Close()
		return fmt.Errorf("write cert: %w", err)
	}
	if err := certOut.Close(); err != nil {
		return err
	}

	keyOut, err := os.OpenFile(opts.KeyPath, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0600)
	if err != nil {
		return fmt.Errorf("open key file: %w", err)
	}
	keyBytes, err := x509.MarshalPKCS8PrivateKey(priv)
	if err != nil {
		_ = keyOut.Close()
		return fmt.Errorf("marshal key: %w", err)
	}
	if err := pem.Encode(keyOut, &pem.Block{Type: "PRIVATE KEY", Bytes: keyBytes}); err != nil {
		_ = keyOut.Close()
		return fmt.Errorf("write key: %w", err)
	}
	return keyOut.Close()
}

// GenerateCert is the legacy entry point kept for callers that still write to
// the current working directory. New code should use GenerateCertTo.
func GenerateCert() {
	if err := GenerateCertTo(CertOptions{CertPath: "cert.crt", KeyPath: "key.pem"}); err != nil {
		panic(err)
	}
}

