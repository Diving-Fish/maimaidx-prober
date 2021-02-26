package lib

import "syscall"


const (
	INTERNET_OPTION_SETTINGS_CHANGED = 39
	ERROR_SUCCESS = 0
)

var (
	modwininet = syscall.NewLazyDLL("wininet.dll")

	procInternetSetOptionW		   = modwininet.NewProc("InternetSetOptionW")
)

func InternetOptionSettingsChanged() (syscall.Handle, error)  {
	p1 := uint16(0)
	p2 := uint64(INTERNET_OPTION_SETTINGS_CHANGED)
	p3 := uint16(0)
	p4 := uint64(0)
	r1, _, e1 := syscall.Syscall6(
		procInternetSetOptionW.Addr(),
		4,
		uintptr(p1),
		uintptr(p2),
		uintptr(p3),
		uintptr(p4),
		0,
		0,
		)
	if r1 == 0 {
		if e1 != ERROR_SUCCESS {
			return 0, e1
		} else {
			return 0, syscall.EINVAL
		}
	}
	return syscall.Handle(r1), nil
}