package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
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
	jwt      *http.Cookie
	mode     workingMode
	maiDiffs []int
}

func newProberAPIClient(cfg *config, networkTimeout int) (*proberAPIClient, error) {
	body := map[string]interface{}{
		"username": cfg.UserName,
		"password": cfg.Password,
	}
	b, err := json.Marshal(&body)
	if err != nil {
		return nil, fmt.Errorf("配置文件读取出错，请按照教程指示填写: %w", err)
	}
	resp, err := http.Post("https://www.diving-fish.com/api/maimaidxprober/login", "application/json", bytes.NewReader(b))
	if err != nil {
		return nil, fmt.Errorf("登录失败: %w", err)
	}
	if resp.StatusCode != 200 {
		return nil, errors.New("登录凭据错误")
	}

	Log(LogLevelInfo, "登录成功")

	return &proberAPIClient{
		cl:       http.Client{Timeout: time.Duration(networkTimeout) * time.Second},
		jwt:      resp.Cookies()[0],
		mode:     cfg.getWorkingMode(),
		maiDiffs: cfg.MaiIntDiffs,
	}, nil
}

func (c *proberAPIClient) commit(data io.Reader) {
	resp2, _ := http.Post("http://www.diving-fish.com:8089/page", "text/plain", data)
	b, _ := io.ReadAll(resp2.Body)
	req, _ := http.NewRequest(http.MethodPost, "https://www.diving-fish.com/api/maimaidxprober/player/update_records", bytes.NewReader(b))
	req.Header.Add("Content-Type", "application/json")
	req.AddCookie(c.jwt)
	c.cl.Do(req)
}

func (c *proberAPIClient) fetchDataMaimai(req0 *http.Request, cookies []*http.Cookie) {
	c.cl.Jar, _ = cookiejar.New(nil)
	if len(cookies) != 2 {
		for _, cookie := range req0.Cookies() {
			if cookie.Name == "userId" {
				cookie2 := *cookies[0]
				cookie2.Name = cookie.Name
				cookie2.Value = cookie.Value
				cookies = append(cookies, &cookie2)
			}
		}
	}
	c.cl.Jar.SetCookies(req0.URL, cookies)
	labels := []string{
		"Basic", "Advanced", "Expert", "Master", "Re: MASTER",
	}
	for _, i := range c.maiDiffs {
		Log(LogLevelInfo, "正在导入 %s 难度……", labels[i])
		var resp *http.Response
		for {
			req, _ := http.NewRequest(http.MethodGet, "https://maimai.wahlap.com/maimai-mobile/record/musicGenre/search/?genre=99&diff="+strconv.Itoa(i), nil)
			var err error
			resp, err = c.cl.Do(req)
			_, timeoutErr := io.ReadAll(resp.Body)
			if err == nil && resp != nil && timeoutErr == nil {
				break
			}
			if err != nil {
				Log(LogLevelWarning, "从 Wahlap 服务器获取数据失败，正在重试……")
			} else if timeoutErr != nil {
				Log(LogLevelWarning, "从 Wahlap 服务器获取数据超时，正在重试……您也可以使用命令行参数 -timeout 120 来调整超时时间为 120 秒（默认为 30 秒）")
			}
		}
		switch c.mode {
		case workingModeUpdate:
			c.commit(resp.Body)
			Log(LogLevelInfo, "导入成功")
		case workingModeExport:
			r, _ := io.ReadAll(resp.Body)
			os.WriteFile(fmt.Sprintf("mai-diff%d.html", i), r, 0644)
			Log(LogLevelInfo, "已导出到文件")
		}
	}
}

func (c *proberAPIClient) fetchDataChuni(req0 *http.Request, cookies []*http.Cookie) {
	c.cl.Jar, _ = cookiejar.New(nil)
	if len(cookies) != 3 {
		for _, cookie := range req0.Cookies() {
			if cookie.Name == "userId" || cookie.Name == "friendCodeList" {
				cookie2 := *cookies[0]
				cookie2.Name = cookie.Name
				cookie2.Value = cookie.Value
				cookies = append(cookies, &cookie2)
			}
		}
	}
	c.cl.Jar.SetCookies(req0.URL, cookies)
	hds := req0.Header.Clone()
	hds.Del("Cookie")
	labels := []string{
		"Basic 难度", "Advanced 难度", "Expert 难度", "Master 难度", "Ultima 难度", "World's End 难度", "Best 10 ",
	}
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
		"/home/playerData/ratingDetailRecent/",
	}

	for i := 0; i < 7; i++ {
		Log(LogLevelInfo, "正在导入 %s……", labels[i])
		if i < 5 {
			formData := url.Values{
				"genre": {"99"},
				"token": {cookies[0].Value},
			}
			req, _ := http.NewRequest(http.MethodPost, "https://chunithm.wahlap.com/mobile"+postUrls[i], strings.NewReader(formData.Encode()))
			req.Header = hds
			req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
			_, _ = c.cl.Do(req)
		}
		req, _ := http.NewRequest(http.MethodGet, "https://chunithm.wahlap.com/mobile"+urls[i], nil)
		resp, _ := c.cl.Do(req)
		switch c.mode {
		case workingModeUpdate:
			url2 := "https://www.diving-fish.com/api/chunithmprober/player/update_records_html"
			if i == 6 {
				url2 += "?recent=1"
			}
			req2, _ := http.NewRequest(http.MethodPost, url2, resp.Body)
			req2.AddCookie(c.jwt)
			c.cl.Do(req2)
			Log(LogLevelInfo, "导入成功")
		case workingModeExport:
			r, _ := io.ReadAll(resp.Body)
			os.WriteFile(fmt.Sprintf("chuni-diff%d.html", i), r, 0644)
			Log(LogLevelInfo, "已导出到文件")
		}
	}
}
