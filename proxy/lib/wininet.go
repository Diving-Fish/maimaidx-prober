package lib

import (
	"syscall"
	"unsafe"
)

const (
	INTERNET_INVALID_PORT_NUMBER = 0
	INTERNET_DEFAULT_FTP_PORT    = 21
	INTERNET_DEFAULT_GOPHER_PORT = 70
	INTERNET_DEFAULT_HTTP_PORT   = 80
	INTERNET_DEFAULT_HTTPS_PORT  = 443
	INTERNET_DEFAULT_SOCKS_PORT  = 1080
)

const (
	INTERNET_FLAG_RELOAD                   = 0x80000000
	INTERNET_FLAG_RAW_DATA                 = 0x40000000
	INTERNET_FLAG_EXISTING_CONNECT         = 0x20000000
	INTERNET_FLAG_ASYNC                    = 0x10000000
	INTERNET_FLAG_PASSIVE                  = 0x08000000
	INTERNET_FLAG_NO_CACHE_WRITE           = 0x04000000
	INTERNET_FLAG_DONT_CACHE               = INTERNET_FLAG_NO_CACHE_WRITE
	INTERNET_FLAG_MAKE_PERSISTENT          = 0x02000000
	INTERNET_FLAG_FROM_CACHE               = 0x01000000
	INTERNET_FLAG_OFFLINE                  = INTERNET_FLAG_FROM_CACHE
	INTERNET_FLAG_SECURE                   = 0x00800000
	INTERNET_FLAG_KEEP_CONNECTION          = 0x00400000
	INTERNET_FLAG_NO_AUTO_REDIRECT         = 0x00200000
	INTERNET_FLAG_READ_PREFETCH            = 0x00100000
	INTERNET_FLAG_NO_COOKIES               = 0x00080000
	INTERNET_FLAG_NO_AUTH                  = 0x00040000
	INTERNET_FLAG_RESTRICTED_ZONE          = 0x00020000
	INTERNET_FLAG_CACHE_IF_NET_FAIL        = 0x00010000
	INTERNET_FLAG_IGNORE_REDIRECT_TO_HTTP  = 0x00008000
	INTERNET_FLAG_IGNORE_REDIRECT_TO_HTTPS = 0x00004000
	INTERNET_FLAG_IGNORE_CERT_DATE_INVALID = 0x00002000
	INTERNET_FLAG_IGNORE_CERT_CN_INVALID   = 0x00001000
	INTERNET_FLAG_RESYNCHRONIZE            = 0x00000800
	INTERNET_FLAG_HYPERLINK                = 0x00000400
	INTERNET_FLAG_NO_UI                    = 0x00000200
	INTERNET_FLAG_PRAGMA_NOCACHE           = 0x00000100
	INTERNET_FLAG_CACHE_ASYNC              = 0x00000080
	INTERNET_FLAG_FORMS_SUBMIT             = 0x00000040
	INTERNET_FLAG_FWD_BACK                 = 0x00000020
	INTERNET_FLAG_NEED_FILE                = 0x00000010
	INTERNET_FLAG_MUST_CACHE_REQUEST       = INTERNET_FLAG_NEED_FILE
)

const (
	INTERNET_OPEN_TYPE_PRECONFIG                   = 0
	INTERNET_OPEN_TYPE_DIRECT                      = 1
	INTERNET_OPEN_TYPE_PROXY                       = 2
	INTERNET_OPEN_TYPE_PRECONFIG_WITH_NO_AUTOPROXY = 4
)

const (
	HTTP_QUERY_MIME_VERSION              = 0
	HTTP_QUERY_CONTENT_TYPE              = 1
	HTTP_QUERY_CONTENT_TRANSFER_ENCODING = 2
	HTTP_QUERY_CONTENT_ID                = 3
	HTTP_QUERY_CONTENT_DESCRIPTION       = 4
	HTTP_QUERY_CONTENT_LENGTH            = 5
	HTTP_QUERY_CONTENT_LANGUAGE          = 6
	HTTP_QUERY_ALLOW                     = 7
	HTTP_QUERY_PUBLIC                    = 8
	HTTP_QUERY_DATE                      = 9
	HTTP_QUERY_EXPIRES                   = 10
	HTTP_QUERY_LAST_MODIFIED             = 11
	HTTP_QUERY_MESSAGE_ID                = 12
	HTTP_QUERY_URI                       = 13
	HTTP_QUERY_DERIVED_FROM              = 14
	HTTP_QUERY_COST                      = 15
	HTTP_QUERY_LINK                      = 16
	HTTP_QUERY_PRAGMA                    = 17
	HTTP_QUERY_VERSION                   = 18
	HTTP_QUERY_STATUS_CODE               = 19
	HTTP_QUERY_STATUS_TEXT               = 20
	HTTP_QUERY_RAW_HEADERS               = 21
	HTTP_QUERY_RAW_HEADERS_CRLF          = 22
	HTTP_QUERY_CONNECTION                = 23
	HTTP_QUERY_ACCEPT                    = 24
	HTTP_QUERY_ACCEPT_CHARSET            = 25
	HTTP_QUERY_ACCEPT_ENCODING           = 26
	HTTP_QUERY_ACCEPT_LANGUAGE           = 27
	HTTP_QUERY_AUTHORIZATION             = 28
	HTTP_QUERY_CONTENT_ENCODING          = 29
	HTTP_QUERY_FORWARDED                 = 30
	HTTP_QUERY_FROM                      = 31
	HTTP_QUERY_IF_MODIFIED_SINCE         = 32
	HTTP_QUERY_LOCATION                  = 33
	HTTP_QUERY_ORIG_URI                  = 34
	HTTP_QUERY_REFERER                   = 35
	HTTP_QUERY_RETRY_AFTER               = 36
	HTTP_QUERY_SERVER                    = 37
	HTTP_QUERY_TITLE                     = 38
	HTTP_QUERY_USER_AGENT                = 39
	HTTP_QUERY_WWW_AUTHENTICATE          = 40
	HTTP_QUERY_PROXY_AUTHENTICATE        = 41
	HTTP_QUERY_ACCEPT_RANGES             = 42
	HTTP_QUERY_SET_COOKIE                = 43
	HTTP_QUERY_COOKIE                    = 44
	HTTP_QUERY_REQUEST_METHOD            = 45
	HTTP_QUERY_REFRESH                   = 46
	HTTP_QUERY_CONTENT_DISPOSITION       = 47
	HTTP_QUERY_AGE                       = 48
	HTTP_QUERY_CACHE_CONTROL             = 49
	HTTP_QUERY_CONTENT_BASE              = 50
	HTTP_QUERY_CONTENT_LOCATION          = 51
	HTTP_QUERY_CONTENT_MD5               = 52
	HTTP_QUERY_CONTENT_RANGE             = 53
	HTTP_QUERY_ETAG                      = 54
	HTTP_QUERY_HOST                      = 55
	HTTP_QUERY_IF_MATCH                  = 56
	HTTP_QUERY_IF_NONE_MATCH             = 57
	HTTP_QUERY_IF_RANGE                  = 58
	HTTP_QUERY_IF_UNMODIFIED_SINCE       = 59
	HTTP_QUERY_MAX_FORWARDS              = 60
	HTTP_QUERY_PROXY_AUTHORIZATION       = 61
	HTTP_QUERY_RANGE                     = 62
	HTTP_QUERY_TRANSFER_ENCODING         = 63
	HTTP_QUERY_UPGRADE                   = 64
	HTTP_QUERY_VARY                      = 65
	HTTP_QUERY_VIA                       = 66
	HTTP_QUERY_WARNING                   = 67
	HTTP_QUERY_EXPECT                    = 68
	HTTP_QUERY_PROXY_CONNECTION          = 69
	HTTP_QUERY_UNLESS_MODIFIED_SINCE     = 70
	HTTP_QUERY_ECHO_REQUEST              = 71
	HTTP_QUERY_ECHO_REPLY                = 72
	HTTP_QUERY_ECHO_HEADERS              = 73
	HTTP_QUERY_ECHO_HEADERS_CRLF         = 74
	HTTP_QUERY_CUSTOM                    = 65535
)

const (
	HTTP_QUERY_FLAG_REQUEST_HEADERS = 0x80000000
	HTTP_QUERY_FLAG_SYSTEMTIME      = 0x40000000
	HTTP_QUERY_FLAG_NUMBER          = 0x20000000
	HTTP_QUERY_FLAG_COALESCE        = 0x10000000
)

const (
	HTTP_STATUS_CONTINUE           = 100
	HTTP_STATUS_SWITCH_PROTOCOLS   = 101
	HTTP_STATUS_OK                 = 200
	HTTP_STATUS_CREATED            = 201
	HTTP_STATUS_ACCEPTED           = 202
	HTTP_STATUS_PARTIAL            = 203
	HTTP_STATUS_NO_CONTENT         = 204
	HTTP_STATUS_RESET_CONTENT      = 205
	HTTP_STATUS_PARTIAL_CONTENT    = 206
	HTTP_STATUS_AMBIGUOUS          = 300
	HTTP_STATUS_MOVED              = 301
	HTTP_STATUS_REDIRECT           = 302
	HTTP_STATUS_REDIRECT_METHOD    = 303
	HTTP_STATUS_NOT_MODIFIED       = 304
	HTTP_STATUS_USE_PROXY          = 305
	HTTP_STATUS_REDIRECT_KEEP_VERB = 307
	HTTP_STATUS_BAD_REQUEST        = 400
	HTTP_STATUS_DENIED             = 401
	HTTP_STATUS_PAYMENT_REQ        = 402
	HTTP_STATUS_FORBIDDEN          = 403
	HTTP_STATUS_NOT_FOUND          = 404
	HTTP_STATUS_BAD_METHOD         = 405
	HTTP_STATUS_NONE_ACCEPTABLE    = 406
	HTTP_STATUS_PROXY_AUTH_REQ     = 407
	HTTP_STATUS_REQUEST_TIMEOUT    = 408
	HTTP_STATUS_CONFLICT           = 409
	HTTP_STATUS_GONE               = 410
	HTTP_STATUS_LENGTH_REQUIRED    = 411
	HTTP_STATUS_PRECOND_FAILED     = 412
	HTTP_STATUS_REQUEST_TOO_LARGE  = 413
	HTTP_STATUS_URI_TOO_LONG       = 414
	HTTP_STATUS_UNSUPPORTED_MEDIA  = 415
	HTTP_STATUS_RETRY_WITH         = 449
	HTTP_STATUS_SERVER_ERROR       = 500
	HTTP_STATUS_NOT_SUPPORTED      = 501
	HTTP_STATUS_BAD_GATEWAY        = 502
	HTTP_STATUS_SERVICE_UNAVAIL    = 503
	HTTP_STATUS_GATEWAY_TIMEOUT    = 504
	HTTP_STATUS_VERSION_NOT_SUP    = 505
)

const (
	INTERNET_SERVICE_FTP    = 1
	INTERNET_SERVICE_GOPHER = 2
	INTERNET_SERVICE_HTTP   = 3
)

const (
	INTERNET_OPTION_SETTINGS_CHANGED = 39
)

var (
	modwininet = syscall.NewLazyDLL("wininet.dll")

	procHttpOpenRequestW           = modwininet.NewProc("HttpOpenRequestW")
	procHttpQueryInfoW             = modwininet.NewProc("HttpQueryInfoW")
	procHttpSendRequestW           = modwininet.NewProc("HttpSendRequestW")
	procInternetCloseHandle        = modwininet.NewProc("InternetCloseHandle")
	procInternetConnectW           = modwininet.NewProc("InternetConnectW")
	procInternetOpenUrlW           = modwininet.NewProc("InternetOpenUrlW")
	procInternetOpenW              = modwininet.NewProc("InternetOpenW")
	procInternetReadFile           = modwininet.NewProc("InternetReadFile")
	procInternetQueryDataAvailable = modwininet.NewProc("InternetQueryDataAvailable")
	procInternetSetOptionW		   = modwininet.NewProc("InternetSetOptionW")
)

func InternetOptionSettingsChanged() (syscall.Handle, error)  {
	p1 := uint16(0)
	p2 := uint64(39)
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

func HttpOpenRequest(connect syscall.Handle, verb *uint16, objectName *uint16, version *uint16, referer *uint16, acceptTypes **uint16, flags uint32, context uintptr) (syscall.Handle, error) {
	r1, _, e1 := syscall.Syscall9(
		procHttpOpenRequestW.Addr(),
		8,
		uintptr(connect),
		uintptr(unsafe.Pointer(verb)),
		uintptr(unsafe.Pointer(objectName)),
		uintptr(unsafe.Pointer(version)),
		uintptr(unsafe.Pointer(referer)),
		uintptr(unsafe.Pointer(acceptTypes)),
		uintptr(flags),
		uintptr(context),
		0)
	if r1 == 0 {
		if e1 != ERROR_SUCCESS {
			return 0, e1
		} else {
			return 0, syscall.EINVAL
		}
	}
	return syscall.Handle(r1), nil
}

func HttpQueryInfo(request syscall.Handle, infoLevel uint32, buffer *byte, bufferLength *uint32, index *uint32) error {
	r1, _, e1 := syscall.Syscall6(
		procHttpQueryInfoW.Addr(),
		5,
		uintptr(request),
		uintptr(infoLevel),
		uintptr(unsafe.Pointer(buffer)),
		uintptr(unsafe.Pointer(bufferLength)),
		uintptr(unsafe.Pointer(index)),
		0)
	if r1 == 0 {
		if e1 != ERROR_SUCCESS {
			return e1
		} else {
			return syscall.EINVAL
		}
	}
	return nil
}

func HttpSendRequest(request syscall.Handle, headers *uint16, headersLength uint32, optional *byte, optionalLength uint32) error {
	r1, _, e1 := syscall.Syscall6(
		procHttpSendRequestW.Addr(),
		5,
		uintptr(request),
		uintptr(unsafe.Pointer(headers)),
		uintptr(headersLength),
		uintptr(unsafe.Pointer(optional)),
		uintptr(optionalLength),
		0)
	if r1 == 0 {
		if e1 != ERROR_SUCCESS {
			return e1
		} else {
			return syscall.EINVAL
		}
	}
	return nil
}

func InternetCloseHandle(internet syscall.Handle) error {
	r1, _, e1 := syscall.Syscall(procInternetCloseHandle.Addr(), 1, uintptr(internet), 0, 0)
	if r1 == 0 {
		if e1 != ERROR_SUCCESS {
			return e1
		} else {
			return syscall.EINVAL
		}
	}
	return nil
}

func InternetConnect(internet syscall.Handle, serverName *uint16, serverPort uint16, username *uint16, password *uint16, service uint32, flags uint32, context uintptr) (syscall.Handle, error) {
	r1, _, e1 := syscall.Syscall9(
		procInternetConnectW.Addr(),
		8,
		uintptr(internet),
		uintptr(unsafe.Pointer(serverName)),
		uintptr(serverPort),
		uintptr(unsafe.Pointer(username)),
		uintptr(unsafe.Pointer(password)),
		uintptr(service),
		uintptr(flags),
		context,
		0)
	if r1 == 0 {
		if e1 != ERROR_SUCCESS {
			return 0, e1
		} else {
			return 0, syscall.EINVAL
		}
	}
	return syscall.Handle(r1), nil
}

func InternetOpen(agent *uint16, accessType uint32, proxyName *uint16, proxyBypass *uint16, flags uint32) (syscall.Handle, error) {
	r1, _, e1 := syscall.Syscall6(
		procInternetOpenW.Addr(),
		5,
		uintptr(unsafe.Pointer(agent)),
		uintptr(accessType),
		uintptr(unsafe.Pointer(proxyName)),
		uintptr(unsafe.Pointer(proxyBypass)),
		uintptr(flags),
		0)
	if r1 == 0 {
		if e1 != ERROR_SUCCESS {
			return 0, e1
		} else {
			return 0, syscall.EINVAL
		}
	}
	return syscall.Handle(r1), nil
}

func InternetOpenUrl(internet syscall.Handle, url *uint16, headers *uint16, headersLength uint32, flags uint32, context uintptr) (syscall.Handle, error) {
	r1, _, e1 := syscall.Syscall6(
		procInternetOpenUrlW.Addr(),
		6,
		uintptr(internet),
		uintptr(unsafe.Pointer(url)),
		uintptr(unsafe.Pointer(headers)),
		uintptr(headersLength),
		uintptr(flags),
		uintptr(context))
	if r1 == 0 {
		if e1 != ERROR_SUCCESS {
			return 0, e1
		} else {
			return 0, syscall.EINVAL
		}
	}
	return syscall.Handle(r1), nil
}

func InternetReadFile(file syscall.Handle, buffer *byte, numberOfBytesToRead uint32, numberOfBytesRead *uint32) error {
	r1, _, e1 := syscall.Syscall6(
		procInternetReadFile.Addr(),
		4,
		uintptr(file),
		uintptr(unsafe.Pointer(buffer)),
		uintptr(numberOfBytesToRead),
		uintptr(unsafe.Pointer(numberOfBytesRead)),
		0,
		0)
	if r1 == 0 {
		if e1 != ERROR_SUCCESS {
			return e1
		} else {
			return syscall.EINVAL
		}
	}
	return nil
}

func InternetQueryDataAvailable(file syscall.Handle, numberOfBytesAvailable *uint32, flags uint32, context uintptr) error {
	r1, _, e1 := syscall.Syscall6(
		procInternetQueryDataAvailable.Addr(),
		4,
		uintptr(file),
		uintptr(unsafe.Pointer(numberOfBytesAvailable)),
		uintptr(flags),
		context,
		0,
		0)
	if r1 == 0 {
		if e1 != ERROR_SUCCESS {
			return e1
		} else {
			return syscall.EINVAL
		}
	}
	return nil
}