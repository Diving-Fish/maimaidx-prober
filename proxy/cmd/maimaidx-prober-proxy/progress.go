package main

import (
	"crypto/rand"
	"crypto/sha1"
	"encoding/base64"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"strings"
	"sync"
	"time"
)

// ProgressEvent is broadcast over WebSocket to the in-page UI.
type ProgressEvent struct {
	Type    string `json:"type"`              // "start" | "step" | "log" | "done" | "error"
	Game    string `json:"game,omitempty"`    // "maimai" | "chuni"
	Stage   string `json:"stage,omitempty"`   // human label of current step
	Current int    `json:"current,omitempty"` // 0-based index of the step about to run
	Total   int    `json:"total,omitempty"`   // total number of steps
	Count   int    `json:"count,omitempty"`   // number of song records imported (set on "done")
	Message string `json:"message,omitempty"` // free-form message (used by "log" / "error")
	Level   string `json:"level,omitempty"`   // "info" | "warn" | "error" (for "log")
	Time    int64  `json:"time"`              // unix milli
}

// progressHub fans out events to any number of subscribers and keeps a small
// ring buffer so that subscribers connecting after the import already started
// can replay recent history.
type progressHub struct {
	mu       sync.Mutex
	subs     map[chan ProgressEvent]struct{}
	history  []ProgressEvent
	historyN int
}

func newProgressHub(historyN int) *progressHub {
	return &progressHub{
		subs:     make(map[chan ProgressEvent]struct{}),
		historyN: historyN,
	}
}

func (h *progressHub) Publish(ev ProgressEvent) {
	if ev.Time == 0 {
		ev.Time = time.Now().UnixMilli()
	}
	h.mu.Lock()
	h.history = append(h.history, ev)
	if len(h.history) > h.historyN {
		h.history = h.history[len(h.history)-h.historyN:]
	}
	subs := make([]chan ProgressEvent, 0, len(h.subs))
	for c := range h.subs {
		subs = append(subs, c)
	}
	h.mu.Unlock()
	for _, c := range subs {
		select {
		case c <- ev:
		default:
			// subscriber too slow; drop to avoid blocking the producer
		}
	}
}

func (h *progressHub) Subscribe() (ch chan ProgressEvent, replay []ProgressEvent) {
	ch = make(chan ProgressEvent, 64)
	h.mu.Lock()
	defer h.mu.Unlock()
	h.subs[ch] = struct{}{}
	replay = append(replay, h.history...)
	return
}

func (h *progressHub) Unsubscribe(ch chan ProgressEvent) {
	h.mu.Lock()
	if _, ok := h.subs[ch]; ok {
		delete(h.subs, ch)
		close(ch)
	}
	h.mu.Unlock()
}

// Clear is called at the start of a new import run so the history doesn't
// leak across sessions.
func (h *progressHub) Clear() {
	h.mu.Lock()
	h.history = nil
	h.mu.Unlock()
}

// global state, configured at startup
var (
	progressHubInstance *progressHub
	progressToken       string
)

func initProgress() {
	progressHubInstance = newProgressHub(200)
	var b [16]byte
	if _, err := rand.Read(b[:]); err != nil {
		// extremely unlikely; fall back to a fixed but locally-scoped value
		progressToken = "fallback-progress-token"
		return
	}
	progressToken = hex.EncodeToString(b[:])
}

// progressPath is the URL path the in-page JS will open as a WebSocket.
// Both wahlap hosts route to the same handler since they're MITM'd by us.
func progressPath() string {
	return "/__prober/progress/" + progressToken
}

// -----------------------------------------------------------------------------
// WebSocket handling (RFC 6455, server-side, minimal but conformant).
// We implement only what we need: send unmasked text frames; respond to ping
// with pong; handle close. Unknown opcodes just close the connection.
// -----------------------------------------------------------------------------

const wsGUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

func wsAcceptKey(clientKey string) string {
	h := sha1.New()
	io.WriteString(h, clientKey+wsGUID)
	return base64.StdEncoding.EncodeToString(h.Sum(nil))
}

// originAllowed validates the WebSocket Origin header. The handshake comes in
// over a MITM'd TLS tunnel for a wahlap host, so the in-page Origin must be
// one of the two known scheme+host values.
func originAllowed(origin string) bool {
	switch origin {
	case "https://maimai.wahlap.com", "https://chunithm.wahlap.com":
		return true
	}
	return false
}

// buildHandshakeResponse returns a 101 response whose Body is one end of a
// net.Pipe. The other end is given to the caller to run WebSocket framing on.
//
// The MITM loop in goproxy detects the websocket Upgrade headers, writes the
// response status+headers to the client TLS conn, then bridges the body
// (clientSide here) with the client conn. So whatever we read/write on
// serverSide flows directly to/from the in-page JS, framed with WebSocket
// data frames that we encode by hand.
func buildHandshakeResponse(req *http.Request, clientKey string) (resp *http.Response, serverSide net.Conn) {
	clientSide, serverSide := net.Pipe()
	header := http.Header{}
	header.Set("Upgrade", "websocket")
	header.Set("Connection", "Upgrade")
	header.Set("Sec-WebSocket-Accept", wsAcceptKey(clientKey))
	resp = &http.Response{
		Status:        "101 Switching Protocols",
		StatusCode:    http.StatusSwitchingProtocols,
		Proto:         "HTTP/1.1",
		ProtoMajor:    1,
		ProtoMinor:    1,
		Header:        header,
		Body:          clientSide,
		ContentLength: -1,
		Request:       req,
	}
	return
}

// writeFrame writes a single unmasked server frame to w.
func wsWriteFrame(w io.Writer, opcode byte, payload []byte) error {
	var hdr [10]byte
	hdr[0] = 0x80 | (opcode & 0x0F) // FIN=1
	n := 2
	switch {
	case len(payload) < 126:
		hdr[1] = byte(len(payload))
	case len(payload) <= 0xFFFF:
		hdr[1] = 126
		binary.BigEndian.PutUint16(hdr[2:4], uint16(len(payload)))
		n = 4
	default:
		hdr[1] = 127
		binary.BigEndian.PutUint64(hdr[2:10], uint64(len(payload)))
		n = 10
	}
	if _, err := w.Write(hdr[:n]); err != nil {
		return err
	}
	if len(payload) > 0 {
		if _, err := w.Write(payload); err != nil {
			return err
		}
	}
	return nil
}

// wsReadFrame reads one frame from r. opcode is the low 4 bits; payload is
// already unmasked. We refuse oversize frames defensively.
func wsReadFrame(r io.Reader) (opcode byte, payload []byte, err error) {
	var hdr [2]byte
	if _, err = io.ReadFull(r, hdr[:]); err != nil {
		return
	}
	opcode = hdr[0] & 0x0F
	masked := hdr[1]&0x80 != 0
	length := uint64(hdr[1] & 0x7F)
	switch length {
	case 126:
		var ext [2]byte
		if _, err = io.ReadFull(r, ext[:]); err != nil {
			return
		}
		length = uint64(binary.BigEndian.Uint16(ext[:]))
	case 127:
		var ext [8]byte
		if _, err = io.ReadFull(r, ext[:]); err != nil {
			return
		}
		length = binary.BigEndian.Uint64(ext[:])
	}
	if length > 1<<20 {
		err = errors.New("websocket frame too large")
		return
	}
	var mask [4]byte
	if masked {
		if _, err = io.ReadFull(r, mask[:]); err != nil {
			return
		}
	}
	payload = make([]byte, length)
	if length > 0 {
		if _, err = io.ReadFull(r, payload); err != nil {
			return
		}
		if masked {
			for i := range payload {
				payload[i] ^= mask[i%4]
			}
		}
	}
	return
}

// runProgressWS runs the server side of a WebSocket connection: replays
// recent history, then streams new events until the client closes or errors.
func runProgressWS(conn net.Conn) {
	defer conn.Close()
	ch, replay := progressHubInstance.Subscribe()
	defer progressHubInstance.Unsubscribe(ch)

	send := func(ev ProgressEvent) error {
		b, err := json.Marshal(ev)
		if err != nil {
			return err
		}
		_ = conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
		err = wsWriteFrame(conn, 0x1, b)
		_ = conn.SetWriteDeadline(time.Time{})
		return err
	}

	// replay recent history first
	for _, ev := range replay {
		if err := send(ev); err != nil {
			return
		}
	}

	// reader goroutine: handle ping/close, signal read errors via done
	done := make(chan struct{})
	go func() {
		defer close(done)
		for {
			op, payload, err := wsReadFrame(conn)
			if err != nil {
				return
			}
			switch op {
			case 0x8: // close
				_ = wsWriteFrame(conn, 0x8, payload)
				return
			case 0x9: // ping
				_ = wsWriteFrame(conn, 0xA, payload)
			case 0xA: // pong, ignore
			}
		}
	}()

	pingT := time.NewTicker(25 * time.Second)
	defer pingT.Stop()
	for {
		select {
		case <-done:
			return
		case <-pingT.C:
			if err := wsWriteFrame(conn, 0x9, nil); err != nil {
				return
			}
		case ev, ok := <-ch:
			if !ok {
				return
			}
			if err := send(ev); err != nil {
				return
			}
		}
	}
}

// tryHandleProgressUpgrade inspects an incoming MITM'd request and, if it's
// our hidden progress endpoint and a valid WebSocket upgrade, returns a
// handshake response (101) wired up to a server-side goroutine running the
// progress stream. If the request isn't ours, it returns nil and the caller
// should fall through to the normal proxy flow.
func tryHandleProgressUpgrade(req *http.Request) *http.Response {
	if req == nil || req.URL == nil {
		return nil
	}
	if req.URL.Path != progressPath() {
		return nil
	}
	// Validate it actually is a WebSocket upgrade.
	if !strings.EqualFold(req.Header.Get("Upgrade"), "websocket") ||
		!strings.Contains(strings.ToLower(req.Header.Get("Connection")), "upgrade") {
		return plainResponse(req, http.StatusBadRequest, "expected websocket upgrade")
	}
	// Origin must match the MITM'd host.
	if !originAllowed(req.Header.Get("Origin")) {
		return plainResponse(req, http.StatusForbidden, "forbidden origin")
	}
	key := req.Header.Get("Sec-WebSocket-Key")
	if key == "" {
		return plainResponse(req, http.StatusBadRequest, "missing key")
	}

	resp, server := buildHandshakeResponse(req, key)
	go runProgressWS(server)
	return resp
}

func plainResponse(req *http.Request, code int, body string) *http.Response {
	hdr := http.Header{}
	hdr.Set("Content-Type", "text/plain; charset=utf-8")
	return &http.Response{
		Status:        fmt.Sprintf("%d %s", code, http.StatusText(code)),
		StatusCode:    code,
		Proto:         "HTTP/1.1",
		ProtoMajor:    1,
		ProtoMinor:    1,
		Header:        hdr,
		Body:          io.NopCloser(strings.NewReader(body)),
		ContentLength: int64(len(body)),
		Request:       req,
	}
}
