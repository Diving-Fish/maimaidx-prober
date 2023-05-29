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
)

type proberAPIClient struct {
	cl   http.Client
	jwt  *http.Cookie
	mode WorkingMode
}

func newProberAPIClient(cfg *config) (*proberAPIClient, error) {
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

	fmt.Println("登录成功，代理已开启到127.0.0.1:8033")

	return &proberAPIClient{
		cl:   http.Client{},
		jwt:  resp.Cookies()[0],
		mode: cfg.getWorkingMode(),
	}, nil
}

func (c *proberAPIClient) commit(data io.Reader) {
	resp2, _ := http.Post("http://www.diving-fish.com:8089/page", "text/plain", data)
	b, _ := io.ReadAll(resp2.Body)
	req, _ := http.NewRequest("POST", "https://www.diving-fish.com/api/maimaidxprober/player/update_records", bytes.NewReader(b))
	req.Header.Add("Content-Type", "application/json")
	req.AddCookie(c.jwt)
	c.cl.Do(req)
	fmt.Println("导入成功")
}

func (c *proberAPIClient) fetchData(req0 *http.Request, cookies []*http.Cookie) {
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
	for i := 0; i < 5; i++ {
		fmt.Printf("正在导入 %s 难度……", labels[i])
		req, _ := http.NewRequest("GET", "https://maimai.wahlap.com/maimai-mobile/record/musicGenre/search/?genre=99&diff="+strconv.Itoa(i), nil)
		resp, _ := c.cl.Do(req)
		switch c.mode {
		case MODE_UPDATE:
			c.commit(resp.Body)
		case MODE_EXPORT:
			r, _ := io.ReadAll(resp.Body)
			os.WriteFile(fmt.Sprintf("mai-diff%d.html", i), r, 0644)
			fmt.Println("已导出到文件")
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
		fmt.Printf("正在导入 %s……", labels[i])
		if i < 5 {
			formData := url.Values{
				"genre": {"99"},
				"token": {cookies[0].Value},
			}
			req, _ := http.NewRequest("POST", "https://chunithm.wahlap.com/mobile"+postUrls[i], strings.NewReader(formData.Encode()))
			req.Header = hds
			req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
			_, _ = c.cl.Do(req)
		}
		req, _ := http.NewRequest("GET", "https://chunithm.wahlap.com/mobile"+urls[i], nil)
		resp, _ := c.cl.Do(req)
		switch c.mode {
		case MODE_UPDATE:
			url2 := "https://www.diving-fish.com/api/chunithmprober/player/update_records_html"
			if i == 6 {
				url2 += "?recent=1"
			}
			req2, _ := http.NewRequest("POST", url2, resp.Body)
			req2.AddCookie(c.jwt)
			c.cl.Do(req2)
			fmt.Println("导入成功")
		case MODE_EXPORT:
			r, _ := io.ReadAll(resp.Body)
			os.WriteFile(fmt.Sprintf("chuni-diff%d.html", i), r, 0644)
			fmt.Println("已导出到文件")
		}
	}
}
