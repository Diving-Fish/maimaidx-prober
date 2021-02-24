package main

import (
	"bytes"
	"crypto/tls"
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"proxy/lib"
	"regexp"

	"github.com/elazarl/goproxy"
)

var jwt *http.Cookie

func tryLogin(username string, password string) {
	body := map[string]interface{}{
		"username": username,
		"password": password,
	}
	b, _ := json.Marshal(&body)
	resp, _ := http.Post("https://www.diving-fish.com/api/maimaidxprober/login", "application/json", bytes.NewReader(b))
	if resp.StatusCode != 200 {
		fmt.Println("登录凭据错误。请按任意键继续……")
		var a byte
		fmt.Scan(&a)
		os.Exit(0)
	}
	cookies := resp.Cookies()
	jwt = cookies[0]
	fmt.Println("登录成功，代理已开启到127.0.0.1:8033")
}

func commit(b []byte) {
	req, _ := http.NewRequest("POST", "https://www.diving-fish.com/api/maimaidxprober/player/update_records", bytes.NewReader(b))
	req.Header.Add("Content-Type", "application/json")
	req.AddCookie(jwt)
	client := &http.Client{}
	client.Do(req)
	fmt.Println("导入成功")
}

func main() {
	b, err := ioutil.ReadFile("config.json")
	if err != nil {
		// First run
		lib.GenerateCert()
		b2, _ := json.Marshal(map[string]interface{}{"username": "", "password": ""})
		ioutil.WriteFile("config.json", b2, 0644)
		fmt.Println("初次使用请填写config.json文件，并依据教程完成根证书的安装。请按任意键继续……")
		var a byte
		fmt.Scan(&a)
		os.Exit(0)
	}
	obj := map[string]interface{}{}
	json.Unmarshal(b, &obj)
	tryLogin(obj["username"].(string), obj["password"].(string))
	crt, _ := ioutil.ReadFile("cert.crt")
	pem, _ := ioutil.ReadFile("key.pem")
	goproxy.GoproxyCa, _ = tls.X509KeyPair(crt, pem)
	proxy := goproxy.NewProxyHttpServer()
	proxy.OnRequest(goproxy.ReqHostMatches(regexp.MustCompile("^maimai.wahlap.com:443.*$"))).
		HandleConnect(goproxy.AlwaysMitm)
	proxy.OnResponse().DoFunc(
		func(resp *http.Response, ctx *goproxy.ProxyCtx) *http.Response {
			path := resp.Request.URL.Path
			rawQuery := resp.Request.URL.RawQuery
			if path == "/maimai-mobile/record/musicGenre/search/" && regexp.MustCompile("genre=99&diff=[0-4]").MatchString(rawQuery) {
				data, _ := ioutil.ReadAll(resp.Body)
				resp.Body = ioutil.NopCloser(bytes.NewReader(data))
				resp2, _ := http.Post("http://www.diving-fish.com:8089/page", "text/plain", bytes.NewReader(data))
				b, _ := ioutil.ReadAll(resp2.Body)
				commit(b)
			}
			return resp
	})
	verbose := flag.Bool("v", false, "should every proxy request be logged to stdout")
	addr := flag.String("addr", ":8033", "proxy listen address")
	flag.Parse()
	proxy.Verbose = *verbose
	log.Fatal(http.ListenAndServe(*addr, proxy))
}