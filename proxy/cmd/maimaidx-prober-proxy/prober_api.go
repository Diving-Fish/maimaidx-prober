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

func (c *proberAPIClient) commit(data []byte) (err error) {
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
	req.AddCookie(c.jwt)
	_, err = c.cl.Do(req)
	if err != nil {
		// 这里有一个已知的后端 bug，可能会导致 status 500，但是数据仍然导入，这里暂时不做处理
		return nil
	}
	return
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
		for {
			err := c.fetchDataMaimaiPerDiff(i)
			if err == nil {
				break
			}
		}
	}
}

func (c *proberAPIClient) fetchDataMaimaiPerDiff(diff int) (err error) {
	req, err := http.NewRequest(http.MethodGet, "https://maimai.wahlap.com/maimai-mobile/record/musicGenre/search/?genre=99&diff="+strconv.Itoa(diff), nil)
	if err != nil {
		Log(LogLevelWarning, "从 Wahlap 服务器获取数据失败，正在重试……")
		return
	}
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
		err = c.commit(respText)
		if err != nil {
			Log(LogLevelWarning, "提交数据到查分服务器失败，正在重试……")
			return
		}
		Log(LogLevelInfo, "导入成功")
	case workingModeExport:
		err = os.WriteFile(fmt.Sprintf("mai-diff%d.html", diff), respText, 0644)
		if err != nil {
			Log(LogLevelWarning, "导出到文件失败")
			return nil
		}
		Log(LogLevelInfo, "已导出到文件")
	}
	return
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
	for i := 0; i < 7; i++ {
		Log(LogLevelInfo, "正在导入 %s……", labels[i])
		for {
			err := c.fetchDataChuniPerDiff(hds, cookies, i)
			if err == nil {
				break
			}
		}
	}
}

func (c *proberAPIClient) fetchDataChuniPerDiff(headers http.Header, cookies []*http.Cookie, diff int) (err error) {
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
	if diff < 5 {
		formData := url.Values{
			"genre": {"99"},
			"token": {cookies[0].Value},
		}
		req, err := http.NewRequest(http.MethodPost, "https://chunithm.wahlap.com/mobile"+postUrls[diff], strings.NewReader(formData.Encode()))
		if err != nil {
			Log(LogLevelWarning, "从 Wahlap 服务器获取数据失败，正在重试……")
			return err
		}
		req.Header = headers
		req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		_, err = c.cl.Do(req)
		if err != nil {
			Log(LogLevelWarning, "从 Wahlap 服务器获取数据失败，正在重试……")
			return err
		}
	}
	req, err := http.NewRequest(http.MethodGet, "https://chunithm.wahlap.com/mobile"+urls[diff], nil)
	if err != nil {
		Log(LogLevelWarning, "从 Wahlap 服务器获取数据失败，正在重试……")
		return
	}
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
		req2, err := http.NewRequest(http.MethodPost, url2, resp.Body)
		if err != nil {
			Log(LogLevelWarning, "从 Wahlap 服务器获取数据失败，正在重试……")
			return err
		}
		req2.AddCookie(c.jwt)
		_, err = c.cl.Do(req2)
		if err != nil {
			Log(LogLevelWarning, "从 Wahlap 服务器获取数据失败，正在重试……")
			return err
		}
		Log(LogLevelInfo, "导入成功")
	case workingModeExport:
		r, _ := io.ReadAll(resp.Body)
		err = os.WriteFile(fmt.Sprintf("chuni-diff%d.html", diff), r, 0644)
		if err != nil {
			Log(LogLevelWarning, "导出到文件失败")
			return nil
		}
		Log(LogLevelInfo, "已导出到文件")
	}
	return nil
}
