package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"
)

type proberAPIClient struct {
	cl       http.Client
	token    string
	mode     workingMode
	maiDiffs []int
	slice    bool
	maiMeta  maimaiProxyMeta
}

// maimaiProxyMeta mirrors the JSON returned by
// /api/maimaidxprober/proxy_meta and lists the difficulty / version names
// that the per-diff fetch loop iterates over. Keeping this on the server
// means new game versions can be added without re-releasing the proxy.
type maimaiProxyMeta struct {
	DiffLabels    []string `json:"diff_labels"`
	VersionTags   []string `json:"version_tags"`
	VersionLabels []string `json:"version_labels"`
}

func fetchMaimaiProxyMeta(cl *http.Client) (maimaiProxyMeta, error) {
	var meta maimaiProxyMeta
	resp, err := cl.Get("https://www.diving-fish.com/api/maimaidxprober/proxy_meta")
	if err != nil {
		return meta, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return meta, fmt.Errorf("proxy_meta returned status %d", resp.StatusCode)
	}
	if err := json.NewDecoder(resp.Body).Decode(&meta); err != nil {
		return meta, err
	}
	return meta, nil
}

func newProberAPIClient(cfg *config, networkTimeout int) (*proberAPIClient, error) {
	req, _ := http.NewRequest("POST", "https://www.diving-fish.com/api/maimaidxprober/player/update_records", bytes.NewReader([]byte("[]")))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Add("Import-Token", cfg.Token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil || resp.StatusCode != 200 {
		return nil, fmt.Errorf("成绩导入 Token 无效，请检查 config.json 文件。")
	}

	Log(LogLevelInfo, "登录成功")

	meta, err := fetchMaimaiProxyMeta(http.DefaultClient)
	if err != nil {
		return nil, fmt.Errorf("无法从查分服务器获取 proxy 元数据：%v", err)
	}

	return &proberAPIClient{
		cl:       http.Client{Timeout: time.Duration(networkTimeout) * time.Second},
		token:    cfg.Token,
		mode:     cfg.getWorkingMode(),
		maiDiffs: cfg.MaiIntDiffs,
		slice:    cfg.Slice,
		maiMeta:  meta,
	}, nil
}

// commit uploads the captured Wahlap HTML to the diving-fish maimai
// update_records pipeline. The backend response includes "updates" /
// "creates" counters which we surface so the UI can show how many records
// were touched.
func (c *proberAPIClient) commit(data []byte) (updates int, creates int, err error) {
	resp2, err := http.Post("http://www.diving-fish.com:8089/page", "text/plain", bytes.NewReader(data))
	if err != nil {
		return
	}
	b, err := io.ReadAll(resp2.Body)
	if err != nil {
		return
	}
	req, err := http.NewRequest(http.MethodPost, "https://www.diving-fish.com/api/maimaidxprober/player/update_records", bytes.NewReader(b))
	if err != nil {
		return
	}
	req.Header.Add("Content-Type", "application/json")
	req.Header.Add("Import-Token", c.token)
	resp, err := c.cl.Do(req)
	if err != nil {
		// 这里有一个已知的后端 bug，可能会导致 status 500，但是数据仍然导入，这里暂时不做处理
		return 0, 0, nil
	}
	updates, creates = parseUpdatesCreates(resp.Body)
	resp.Body.Close()
	return
}

// parseUpdatesCreates extracts the {"updates": N, "creates": M} fields
// returned by the prober update_records / update_records_html endpoints.
// Missing fields are treated as zero so we never fail the import just because
// the backend changed shape.
func parseUpdatesCreates(r io.Reader) (updates int, creates int) {
	var payload struct {
		Updates int `json:"updates"`
		Creates int `json:"creates"`
	}
	_ = json.NewDecoder(r).Decode(&payload)
	return payload.Updates, payload.Creates
}

// browserHeaders returns a header set safe to forward to wahlap. It strips
// hop-by-hop / per-request headers (Cookie is supplied by the cookie jar,
// Content-Length/Content-Type are recomputed by net/http) but keeps the
// fingerprinting-relevant ones (User-Agent, Accept*, sec-ch-ua*, sec-fetch-*,
// upgrade-insecure-requests, etc.) so EdgeOne's WAF doesn't flag us as a
// bot.
func browserHeaders(src http.Header) http.Header {
	h := src.Clone()
	for _, k := range []string{
		"Cookie", "Content-Length", "Content-Type",
		"Host", "Connection", "Proxy-Connection",
		"Transfer-Encoding", "Te", "Upgrade", "Trailer",
	} {
		h.Del(k)
	}
	return h
}

// applyHeaders copies every header from src into dst, replacing any existing
// value. Use this instead of `req.Header = src` so we don't accidentally
// share the underlying map between concurrent requests.
func applyHeaders(dst, src http.Header) {
	for k, vs := range src {
		dst[k] = append([]string(nil), vs...)
	}
}

// seedCookieJar populates a fresh jar with both the cookies the browser
// already had (parsed from the request's Cookie header) and the ones the
// server is setting on this response (Set-Cookie). Crucially, cookies parsed
// from a Cookie header only carry Name/Value -- Path is empty, so cookiejar
// would default it to the URL's directory (e.g. /maimai-mobile/home/) and
// then refuse to send them when we later GET /maimai-mobile/record/...
// We therefore force Path="/" on every request-side cookie so they apply
// across the whole site, matching what the browser is actually doing.
func seedCookieJar(u *url.URL, reqCookies, respCookies []*http.Cookie) http.CookieJar {
	jar, _ := cookiejar.New(nil)
	// cookiejar derives the storage host from u.Host, but the goproxy URL
	// often carries a `:443` suffix that breaks domain-matching. Strip the
	// port so cookies are stored against the bare hostname.
	jarURL := *u
	if h, _, err := net.SplitHostPort(jarURL.Host); err == nil {
		jarURL.Host = h
	}
	if len(reqCookies) > 0 {
		normalized := make([]*http.Cookie, 0, len(reqCookies))
		for _, c := range reqCookies {
			copy := *c
			if copy.Path == "" {
				copy.Path = "/"
			}
			// Leave Domain empty: that's how the browser actually stored
			// these cookies (no Domain attr in the original Set-Cookie ->
			// host-only). Setting Domain explicitly would flip HostOnly to
			// false. cookiejar will fill HostOnly=true / Domain=jarURL.Host
			// for us when Domain is empty.
			copy.Domain = ""
			// MaxAge/Expires are unknown from a request-side Cookie header;
			// treat them as session cookies (Persistent=false) which matches
			// what the browser does for cookies set without those attrs.
			copy.MaxAge = 0
			copy.Expires = time.Time{}
			// The Cookie request header doesn't carry HttpOnly either, but
			// the browser would never have sent a cookie back unless the
			// origin allowed it -- mark them HttpOnly so the jar's stored
			// state matches what the browser actually has.
			copy.HttpOnly = true
			normalized = append(normalized, &copy)
		}
		jar.SetCookies(&jarURL, normalized)
	}
	if len(respCookies) > 0 {
		// Set-Cookie cookies usually carry their own Path/Domain so we can
		// pass them through unchanged; setting them after the request-side
		// cookies means any name collision (e.g. _t) is resolved in favour
		// of the freshest value from the server.
		jar.SetCookies(&jarURL, respCookies)
	}
	return jar
}

func (c *proberAPIClient) fetchDataMaimai(req0 *http.Request, respCookies []*http.Cookie) {
	// Seed the jar with everything the browser sent in the home request --
	// crucially this includes the EdgeOne / TencentEdge challenge cookies
	// (__tst_status, EO_Bot_Ssid) without which the WAF will keep returning
	// the JS bot-check page instead of the real HTML.
	c.cl.Jar = seedCookieJar(req0.URL, req0.Cookies(), respCookies)
	headers := browserHeaders(req0.Header)

	labels := c.maiMeta.DiffLabels
	versionTags := c.maiMeta.VersionTags
	versionLabels := c.maiMeta.VersionLabels
	stepsPerDiff := 1
	if c.slice {
		stepsPerDiff = len(versionTags)
	}
	total := len(c.maiDiffs) * stepsPerDiff
	progressHubInstance.Clear()
	progressHubInstance.Publish(ProgressEvent{Type: "start", Game: "maimai", Total: total})
	done := 0
	totalUpdates, totalCreates := 0, 0
	for _, i := range c.maiDiffs {
		if c.slice {
			for j, versionTag := range versionTags {
				progressHubInstance.Publish(ProgressEvent{
					Type: "step", Game: "maimai",
					Stage:   fmt.Sprintf("%s · %s", versionLabels[j], labels[i]),
					Current: done, Total: total,
				})
				Log(LogLevelInfo, "正在导入 %s 版本的 %s 难度……", versionLabels[j], labels[i])
				for {
					u, cr, err := c.fetchDataMaimaiPerDiffAndVersion(headers, i, versionTag)
					if err == nil {
						totalUpdates += u
						totalCreates += cr
						break
					}
				}
				done++
			}
		} else {
			progressHubInstance.Publish(ProgressEvent{
				Type: "step", Game: "maimai",
				Stage:   labels[i],
				Current: done, Total: total,
			})
			Log(LogLevelInfo, "正在导入 %s 难度……", labels[i])
			for {
				u, cr, err := c.fetchDataMaimaiPerDiff(headers, i)
				if err == nil {
					totalUpdates += u
					totalCreates += cr
					break
				}
			}
			done++
		}
	}
	if c.mode == workingModeUpdate {
		Log(LogLevelInfo, "全部难度导入完成，共新增 %d 条、更新 %d 条成绩记录", totalCreates, totalUpdates)
	}
	progressHubInstance.Publish(ProgressEvent{Type: "done", Game: "maimai", Current: total, Total: total, Count: totalUpdates + totalCreates})
}

func (c *proberAPIClient) fetchDataMaimaiPerDiff(headers http.Header, diff int) (updates int, creates int, err error) {
	req, err := http.NewRequest(http.MethodGet, "https://maimai.wahlap.com/maimai-mobile/record/musicSort/search/?search=A&sort=1&playCheck=on&diff="+strconv.Itoa(diff), nil)
	if err != nil {
		Log(LogLevelWarning, "从 Wahlap 服务器获取数据失败，正在重试……")
		return
	}
	applyHeaders(req.Header, headers)
	req.Header.Set("Referer", "https://maimai.wahlap.com/maimai-mobile/record/")
	resp, err := c.cl.Do(req)
	if err != nil {
		Log(LogLevelWarning, "从 Wahlap 服务器获取数据失败，正在重试……")
		return
	}
	respText, err := io.ReadAll(resp.Body)
	if err != nil {
		Log(LogLevelWarning, "从 Wahlap 服务器获取数据超时，正在重试……您也可以使用命令行参数 -timeout 120 来调整超时时间为 120 秒（默认为 30 秒）")
		return
	}
	switch c.mode {
	case workingModeUpdate:
		updates, creates, err = c.commit(respText)
		if err != nil {
			Log(LogLevelWarning, "提交数据到查分服务器失败，正在重试……")
			return
		}
		Log(LogLevelInfo, "导入成功，本难度新增 %d 条、更新 %d 条", creates, updates)
	case workingModeExport:
		err = os.WriteFile(fmt.Sprintf("mai-diff%d.html", diff), respText, 0644)
		if err != nil {
			Log(LogLevelWarning, "导出到文件失败")
			return 0, 0, nil
		}
		Log(LogLevelInfo, "已导出到文件")
	}
	return
}

func (c *proberAPIClient) fetchDataChuni(req0 *http.Request, respCookies []*http.Cookie) {
	c.cl.Jar = seedCookieJar(req0.URL, req0.Cookies(), respCookies)
	// The chunithm form posts include a `_t` token field; locate it from
	// whichever cookie source provides it.
	var token string
	for _, c := range append(append([]*http.Cookie{}, respCookies...), req0.Cookies()...) {
		if c.Name == "_t" {
			token = c.Value
			break
		}
	}
	hds := browserHeaders(req0.Header)
	labels := []string{
		"Basic 难度", "Advanced 难度", "Expert 难度", "Master 难度", "Ultima 难度", "World's End 难度",
	}
	progressHubInstance.Clear()
	progressHubInstance.Publish(ProgressEvent{Type: "start", Game: "chuni", Total: 6})
	totalUpdates, totalCreates := 0, 0
	for i := 0; i < 6; i++ {
		progressHubInstance.Publish(ProgressEvent{
			Type: "step", Game: "chuni",
			Stage:   labels[i],
			Current: i, Total: 6,
		})
		Log(LogLevelInfo, "正在导入 %s……", labels[i])
		for {
			u, cr, err := c.fetchDataChuniPerDiff(hds, token, i)
			if err == nil {
				totalUpdates += u
				totalCreates += cr
				break
			}
		}
	}
	if c.mode == workingModeUpdate {
		Log(LogLevelInfo, "全部难度导入完成，共新增 %d 条、更新 %d 条成绩记录", totalCreates, totalUpdates)
	}
	progressHubInstance.Publish(ProgressEvent{Type: "done", Game: "chuni", Current: 6, Total: 6, Count: totalUpdates + totalCreates})
}

func (c *proberAPIClient) fetchDataChuniPerDiff(headers http.Header, token string, diff int) (updates int, creates int, err error) {
	postUrls := []string{
		"/record/musicGenre/sendBasic",
		"/record/musicGenre/sendAdvanced",
		"/record/musicGenre/sendExpert",
		"/record/musicGenre/sendMaster",
		"/record/musicGenre/sendUltima",
	}
	urls := []string{
		"/record/musicGenre/basic",
		"/record/musicGenre/advanced",
		"/record/musicGenre/expert",
		"/record/musicGenre/master",
		"/record/musicGenre/ultima",
		"/record/worldsEndList/",
	}
	if diff < 5 {
		formData := url.Values{
			"genre": {"99"},
			"token": {token},
		}
		req, rerr := http.NewRequest(http.MethodPost, "https://chunithm.wahlap.com/mobile"+postUrls[diff], strings.NewReader(formData.Encode()))
		if rerr != nil {
			Log(LogLevelWarning, "从 Wahlap 服务器获取数据失败，正在重试……")
			return 0, 0, rerr
		}
		applyHeaders(req.Header, headers)
		req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		req.Header.Set("Referer", "https://chunithm.wahlap.com/mobile/record/musicGenre/")
		if _, derr := c.cl.Do(req); derr != nil {
			Log(LogLevelWarning, "从 Wahlap 服务器获取数据失败，正在重试……")
			return 0, 0, derr
		}
	}
	req, err := http.NewRequest(http.MethodGet, "https://chunithm.wahlap.com/mobile"+urls[diff], nil)
	if err != nil {
		Log(LogLevelWarning, "从 Wahlap 服务器获取数据失败，正在重试……")
		return
	}
	applyHeaders(req.Header, headers)
	req.Header.Set("Referer", "https://chunithm.wahlap.com/mobile/home/")
	resp, err := c.cl.Do(req)
	if err != nil {
		Log(LogLevelWarning, "从 Wahlap 服务器获取数据失败，正在重试……")
		return
	}
	switch c.mode {
	case workingModeUpdate:
		url2 := "https://www.diving-fish.com/api/chunithmprober/player/update_records_html"
		if diff == 6 {
			url2 += "?recent=1"
		}
		req2, rerr := http.NewRequest(http.MethodPost, url2, resp.Body)
		if rerr != nil {
			Log(LogLevelWarning, "从 Wahlap 服务器获取数据失败，正在重试……")
			return 0, 0, rerr
		}
		req2.Header.Add("Import-Token", c.token)
		resp2, derr := c.cl.Do(req2)
		if derr != nil {
			Log(LogLevelWarning, "从 Wahlap 服务器获取数据失败，正在重试……")
			return 0, 0, derr
		}
		updates, creates = parseUpdatesCreates(resp2.Body)
		resp2.Body.Close()
		Log(LogLevelInfo, "导入成功，本难度新增 %d 条、更新 %d 条", creates, updates)
	case workingModeExport:
		r, _ := io.ReadAll(resp.Body)
		err = os.WriteFile(fmt.Sprintf("chuni-diff%d.html", diff), r, 0644)
		if err != nil {
			Log(LogLevelWarning, "导出到文件失败")
			return 0, 0, nil
		}
		Log(LogLevelInfo, "已导出到文件")
	}
	return 0, 0, nil
}

func (c *proberAPIClient) fetchDataMaimaiPerDiffAndVersion(headers http.Header, diff int, version string) (updates int, creates int, err error) {
	pageUrl := fmt.Sprintf("https://maimai.wahlap.com/maimai-mobile/record/musicSort/search/?search=%s&sort=1&playCheck=on&diff=%d", version, diff)
	req, err := http.NewRequest(http.MethodGet, pageUrl, nil)
	if err != nil {
		Log(LogLevelWarning, "从 Wahlap 服务器获取数据失败，正在重试……")
		return
	}
	applyHeaders(req.Header, headers)
	req.Header.Set("Referer", "https://maimai.wahlap.com/maimai-mobile/record/")
	resp, err := c.cl.Do(req)
	if err != nil {
		Log(LogLevelWarning, "从 Wahlap 服务器获取数据失败，正在重试……")
		return
	}
	respText, err := io.ReadAll(resp.Body)
	if err != nil {
		Log(LogLevelWarning, "从 Wahlap 服务器获取数据超时，正在重试……您也可以使用命令行参数 -timeout 120 来调整超时时间为 120 秒（默认为 30 秒）")
		return
	}
	switch c.mode {
	case workingModeUpdate:
		updates, creates, err = c.commit(respText)
		if err != nil {
			Log(LogLevelWarning, "提交数据到查分服务器失败，正在重试……")
			return
		}
		Log(LogLevelInfo, "导入成功，本版本难度新增 %d 条、更新 %d 条", creates, updates)
	case workingModeExport:
		err = os.WriteFile(fmt.Sprintf("mai-diff-%s-%d.html", version, diff), respText, 0644)
		if err != nil {
			Log(LogLevelWarning, "导出到文件失败")
			return 0, 0, nil
		}
		Log(LogLevelInfo, "已导出到文件")
	}
	return
}
