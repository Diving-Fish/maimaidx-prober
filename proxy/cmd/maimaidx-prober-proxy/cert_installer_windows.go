//go:build windows

package main

import (
	"fmt"
	"os"
	"os/exec"
	"strings"
	"syscall"
	"unsafe"

	"golang.org/x/sys/windows"
)

// installCert installs the local CA into the LocalMachine\Root store via
// certutil. Requires administrator privileges; if the current process is not
// elevated, we re-launch ourselves with the same -install-cert flag through
// ShellExecute "runas", which triggers the standard UAC prompt (one click).
func installCert(certFile string) error {
	if !isElevated() {
		return elevateAndRun("-install-cert")
	}
	out, err := runCertutil("-addstore", "-f", "ROOT", certFile)
	if err != nil {
		return fmt.Errorf("certutil 安装根证书失败: %w\n%s", err, out)
	}
	Log(LogLevelInfo, "证书已安装到 LocalMachine\\Root")
	return nil
}

// uninstallCert removes the local CA from LocalMachine\Root by SHA-1
// thumbprint. Same elevation handling as installCert.
func uninstallCert(certFile string) error {
	cert, err := readCertificate(certFile)
	if err != nil {
		return fmt.Errorf("读取证书失败: %w", err)
	}
	thumb := certThumbprintHex(cert)
	if !isElevated() {
		return elevateAndRun("-uninstall-cert")
	}
	out, err := runCertutil("-delstore", "ROOT", thumb)
	if err != nil {
		return fmt.Errorf("certutil 删除根证书失败: %w\n%s", err, out)
	}
	Log(LogLevelInfo, "证书已从 LocalMachine\\Root 中移除")
	return nil
}

func runCertutil(args ...string) (string, error) {
	cmd := exec.Command("certutil", args...)
	out, err := cmd.CombinedOutput()
	return strings.TrimSpace(string(out)), err
}

// isCertInstalled reports whether a certificate with the given SHA-1
// thumbprint already lives in LocalMachine\Root. It is best-effort: any
// error from certutil is treated as "not installed" so we will attempt
// (re)installation, which is idempotent.
func isCertInstalled(thumb string) bool {
	_, err := runCertutil("-verifystore", "ROOT", thumb)
	return err == nil
}

// isElevated reports whether the current process is running with the
// administrator token.
func isElevated() bool {
	var tok windows.Token
	if err := windows.OpenProcessToken(windows.CurrentProcess(), windows.TOKEN_QUERY, &tok); err != nil {
		return false
	}
	defer tok.Close()
	return tok.IsElevated()
}

// elevateAndRun re-launches the current executable with the given flag using
// ShellExecuteW("runas"), then waits for it to exit. The child process will
// trigger a UAC consent dialog.
func elevateAndRun(flagName string) error {
	exe, err := os.Executable()
	if err != nil {
		return err
	}
	exePtr, err := syscall.UTF16PtrFromString(exe)
	if err != nil {
		return err
	}
	verbPtr, _ := syscall.UTF16PtrFromString("runas")
	argsPtr, _ := syscall.UTF16PtrFromString(flagName)
	cwd, _ := os.Getwd()
	cwdPtr, _ := syscall.UTF16PtrFromString(cwd)

	info := shellExecuteInfo{
		Verb:       verbPtr,
		File:       exePtr,
		Parameters: argsPtr,
		Directory:  cwdPtr,
		Show:       1, // SW_SHOWNORMAL
		Mask:       seeMaskNoCloseProcess,
	}
	info.Size = uint32(unsafe.Sizeof(info))

	if err := shellExecuteEx(&info); err != nil {
		return fmt.Errorf("自我提权失败 (UAC 被拒？): %w", err)
	}
	if info.Process != 0 {
		h := windows.Handle(info.Process)
		_, _ = windows.WaitForSingleObject(h, windows.INFINITE)
		var code uint32
		_ = windows.GetExitCodeProcess(h, &code)
		_ = windows.CloseHandle(h)
		if code != 0 {
			return fmt.Errorf("提权后的进程退出码 %d", code)
		}
	}
	return nil
}

const seeMaskNoCloseProcess = 0x00000040

// shellExecuteInfo mirrors SHELLEXECUTEINFOW.
type shellExecuteInfo struct {
	Size       uint32
	Mask       uint32
	Hwnd       uintptr
	Verb       *uint16
	File       *uint16
	Parameters *uint16
	Directory  *uint16
	Show       int32
	Instance   uintptr
	IDList     uintptr
	Class      *uint16
	HKeyClass  uintptr
	HotKey     uint32
	IconOrMon  uintptr
	Process    uintptr
}

var (
	modShell32       = syscall.NewLazyDLL("shell32.dll")
	procShellExecExW = modShell32.NewProc("ShellExecuteExW")
)

func shellExecuteEx(info *shellExecuteInfo) error {
	r1, _, e1 := procShellExecExW.Call(uintptr(unsafe.Pointer(info)))
	if r1 == 0 {
		if e1 != nil && e1 != syscall.Errno(0) {
			return e1
		}
		return syscall.EINVAL
	}
	return nil
}
