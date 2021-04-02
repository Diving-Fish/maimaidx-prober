package main

import (
	"bufio"
	"bytes"
	"crypto/tls"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"os"
	"regexp"
	"strconv"
	"strings"

	"github.com/elazarl/goproxy"

	"github.com/Diving-Fish/maimaidx-prober/proxy/lib"
)

const (
	MODE_UPDATE = 0
	MODE_EXPORT = 1 // only for debug or other
)

var (
	ProxyEnable   uint64 = 39
	ProxyServer          = "rollback"
	AutoConfigURL        = "rollback"
	mode                 = MODE_UPDATE
)

var jwt *http.Cookie

func commandFatal(prompt string) {
	rollbackSystemProxySettings()
	fmt.Printf("%s请按 Enter 键继续……", prompt)
	bufio.NewReader(os.Stdin).ReadString('\n')
	os.Exit(0)
}

func tryLogin(username string, password string) {
	body := map[string]interface{}{
		"username": username,
		"password": password,
	}
	b, _ := json.Marshal(&body)
	resp, _ := http.Post("https://www.diving-fish.com/api/maimaidxprober/login", "application/json", bytes.NewReader(b))
	if resp.StatusCode != 200 {
		commandFatal("登录凭据错误")
	}
	cookies := resp.Cookies()
	jwt = cookies[0]
	fmt.Println("登录成功，代理已开启到127.0.0.1:8033")
}

func commit(data io.Reader) {
	resp2, _ := http.Post("http://www.diving-fish.com:8089/page", "text/plain", data)
	b, _ := ioutil.ReadAll(resp2.Body)
	req, _ := http.NewRequest("POST", "https://www.diving-fish.com/api/maimaidxprober/player/update_records", bytes.NewReader(b))
	req.Header.Add("Content-Type", "application/json")
	req.AddCookie(jwt)
	client := &http.Client{}
	client.Do(req)
	fmt.Println("导入成功")
}

func fetchData(url *url.URL, cookies []*http.Cookie) {
	client := &http.Client{}
	client.Jar, _ = cookiejar.New(nil)
	client.Jar.SetCookies(url, cookies)
	labels := []string{
		"Basic", "Advanced", "Expert", "Master", "Re: MASTER",
	}
	for i := 0; i < 5; i++ {
		fmt.Printf("正在导入 %s 难度……", labels[i])
		req, _ := http.NewRequest("GET", "https://maimai.wahlap.com/maimai-mobile/record/musicGenre/search/?genre=99&diff="+strconv.Itoa(i), nil)
		resp, _ := client.Do(req)
		if mode == MODE_UPDATE {
			commit(resp.Body)
		} else if mode == MODE_EXPORT {
			r, _ := ioutil.ReadAll(resp.Body)
			ioutil.WriteFile(fmt.Sprintf("diff%d.html", i), r, 0644)
			fmt.Println("已导出到文件")
		}
	}
	if ProxyEnable != 39 {
		rollbackSystemProxySettings()
		fmt.Println("所有数据均已导入完成，请按 Enter 键以关闭此窗口，代理设置已经恢复到先前的设置~")
	} else {
		fmt.Println("所有数据均已导入完成，请按 Enter 键以关闭此窗口，不要忘记还原代理设置哦~")
	}
	bufio.NewReader(os.Stdin).ReadString('\n')
	os.Exit(0)
}

func main() {
	b, err := ioutil.ReadFile("config.json")
	if err != nil {
		// First run
		lib.GenerateCert()
		ioutil.WriteFile("config.json", []byte("{\"username\": \"\", \"password\": \"\"}"), 0644)
		commandFatal("初次使用请填写config.json文件，并依据教程完成根证书的安装。")
	}
	obj := map[string]interface{}{}
	json.Unmarshal(b, &obj)
	if obj["mode"] != nil && obj["mode"].(string) == "export" {
		mode = MODE_EXPORT
	}
	tryLogin(obj["username"].(string), obj["password"].(string))
	applySystemProxySettings()
	crt, _ := ioutil.ReadFile("cert.crt")
	pem, _ := ioutil.ReadFile("key.pem")
	goproxy.GoproxyCa, _ = tls.X509KeyPair(crt, pem)
	proxy := goproxy.NewProxyHttpServer()
	proxy.OnRequest(goproxy.ReqHostMatches(regexp.MustCompile("^maimai.wahlap.com:443.*$"))).
		HandleConnect(goproxy.AlwaysMitm)
	proxy.OnResponse().DoFunc(
		func(resp *http.Response, ctx *goproxy.ProxyCtx) *http.Response {
			path := resp.Request.URL.Path
			if regexp.MustCompile("^/maimai-mobile/home.*").MatchString(path) {
				resp.Body = ioutil.NopCloser(strings.NewReader("<p>正在获取您的乐曲数据，请稍候……这可能需要花费数秒，具体进度可以在代理服务器的命令行窗口查看。</p><p>此页面仅用于提示您成功访问了代理服务器，您可以立即关闭此窗口。</p>"))
				if resp.StatusCode == 302 {
					commandFatal("访问舞萌 DX 的成绩界面出错。")
				}
				go fetchData(resp.Request.URL, resp.Cookies())
			}
			return resp
		})
	verbose := flag.Bool("v", false, "should every proxy request be logged to stdout")
	addr := flag.String("addr", ":8033", "proxy listen address")
	flag.Parse()
	proxy.Verbose = *verbose
	log.Fatal(http.ListenAndServe(*addr, proxy))
}
