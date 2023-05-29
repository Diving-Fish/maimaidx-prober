package main

import (
	"bufio"
	"bytes"
	"crypto/tls"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"os"
	"os/signal"
	"regexp"
	"strconv"
	"strings"
	"syscall"

	"github.com/elazarl/goproxy"

	"github.com/Diving-Fish/maimaidx-prober/proxy/lib"
)

type WorkingMode int

const (
	MODE_UPDATE WorkingMode = 0
	MODE_EXPORT WorkingMode = 1 // only for debug or other
)

var (
	ProxyEnable   uint64 = 39
	ProxyServer          = "rollback"
	AutoConfigURL        = "rollback"
)

func commandFatal(prompt string) {
	rollbackSystemProxySettings()
	fmt.Printf("%s请按 Enter 键继续……", prompt)
	bufio.NewReader(os.Stdin).ReadString('\n')
	os.Exit(0)
}

type proberAPIClient struct {
	cl   http.Client
	jwt  *http.Cookie
	mode WorkingMode
}

func mustNewProberAPIClient(cfg *config) *proberAPIClient {
	body := map[string]interface{}{
		"username": cfg.UserName,
		"password": cfg.Password,
	}
	b, err := json.Marshal(&body)
	if err != nil {
		commandFatal("配置文件读取出错，请按照教程指示填写")
	}
	resp, err := http.Post("https://www.diving-fish.com/api/maimaidxprober/login", "application/json", bytes.NewReader(b))
	if err != nil {
		commandFatal("登录失败")
	}
	if resp.StatusCode != 200 {
		commandFatal("登录凭据错误")
	}

	fmt.Println("登录成功，代理已开启到127.0.0.1:8033")

	return &proberAPIClient{
		cl:   http.Client{},
		jwt:  resp.Cookies()[0],
		mode: cfg.getWorkingMode(),
	}
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

type config struct {
	UserName string `json:"username"`
	Password string `json:"password"`
	Mode     string `json:"mode,omitempty"`
}

func (c *config) getWorkingMode() WorkingMode {
	if c.Mode == "export" {
		return MODE_EXPORT
	}
	return MODE_UPDATE
}

func initConfig(path string) config {
	b, err := os.ReadFile(path)
	if err != nil {
		// First run
		lib.GenerateCert()
		os.WriteFile(path, []byte("{\"username\": \"\", \"password\": \"\"}"), 0644)
		commandFatal(fmt.Sprintf("初次使用请填写 %s 文件，并依据教程完成根证书的安装。", path))
	}

	var obj config
	err = json.Unmarshal(b, &obj)
	if err != nil {
		commandFatal(fmt.Sprintf("配置文件格式有误，无法解析：请检查 %s 文件的内容", path))
	}

	return obj
}

func main() {
	verbose := flag.Bool("v", false, "should every proxy request be logged to stdout")
	addr := flag.String("addr", ":8033", "proxy listen address")
	configPath := flag.String("config", "config.json", "path to config.json file")
	flag.Parse()

	cfg := initConfig(*configPath)

	apiClient := mustNewProberAPIClient(&cfg)

	applySystemProxySettings()
	// 搞个抓SIGINT的东西，×的时候可以关闭代理
	c := make(chan os.Signal)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	go func() {
		for range c {
			if ProxyEnable != 39 {
				rollbackSystemProxySettings()
			}
			os.Exit(0)
		}
	}()
	crt, _ := os.ReadFile("cert.crt")
	pem, _ := os.ReadFile("key.pem")
	goproxy.GoproxyCa, _ = tls.X509KeyPair(crt, pem)
	fmt.Println("使用此软件则表示您同意共享您在微信公众号舞萌 DX、中二节奏中的数据。")
	fmt.Println("您可以在微信客户端访问微信公众号舞萌 DX、中二节奏的个人信息主页进行分数导入，如需退出请直接关闭程序或按下 Ctrl + C")
	proxy := goproxy.NewProxyHttpServer()
	proxy.OnRequest(goproxy.ReqHostMatches(regexp.MustCompile("^(maimai|chunithm).wahlap.com:443.*$"))).
		HandleConnect(goproxy.AlwaysMitm)
	proxy.OnResponse().DoFunc(
		func(resp *http.Response, ctx *goproxy.ProxyCtx) *http.Response {
			if resp == nil || resp.Request == nil || resp.Request.URL == nil {
				return resp
			}
			path := resp.Request.URL.Path
			if regexp.MustCompile("^/maimai-mobile/home.*").MatchString(path) {
				resp.Body = io.NopCloser(strings.NewReader("<p>正在获取您的舞萌 DX 乐曲数据，请稍候……这可能需要花费数秒，具体进度可以在代理服务器的命令行窗口查看。</p><p>此页面仅用于提示您成功访问了代理服务器，您可以立即关闭此窗口。</p>"))
				if resp.StatusCode == 302 {
					commandFatal("访问舞萌 DX 的成绩界面出错。")
				}
				go apiClient.fetchData(resp.Request, resp.Cookies())
			}
			if regexp.MustCompile("^/mobile/home.*").MatchString(path) {
				resp.Body = io.NopCloser(strings.NewReader("<p>正在获取您的中二节奏乐曲数据，请稍候……这可能需要花费数秒，具体进度可以在代理服务器的命令行窗口查看。</p><p>此页面仅用于提示您成功访问了代理服务器，您可以立即关闭此窗口。</p>"))
				if resp.StatusCode == 302 {
					commandFatal("访问中二节奏的成绩界面出错。")
				}
				go apiClient.fetchDataChuni(resp.Request, resp.Cookies())
			}
			return resp
		})
	proxy.Verbose = *verbose
	log.Fatal(http.ListenAndServe(*addr, proxy))
}
