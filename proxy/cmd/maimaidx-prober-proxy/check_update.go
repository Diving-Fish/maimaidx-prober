package main

import (
	"encoding/json"
	"io"
	"net/http"
)

var (
	version string = "custom"
)

type Tag struct {
	Name string `json:"name"`
}

func checkUpdate() {
	// 发送 GET 请求获取 tags 列表
	resp, err := http.Get("https://api.github.com/repos/Diving-Fish/maimaidx-prober/tags")
	if err != nil {
		Log(LogLevelError, "Failed to get tags:", err)
		return
	}
	defer resp.Body.Close()

	// 读取响应内容并解析 JSON
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		Log(LogLevelError, "Failed to read response:", err)
		return
	}
	var tags []Tag
	if err := json.Unmarshal(body, &tags); err != nil {
		Log(LogLevelError, "Failed to parse response:", err)
		return
	}

	// 获取最新的 tag
	newestTag := tags[0].Name

	// 检查当前版本是否为最新 tag
	if version == "custom" {
		Log(LogLevelInfo, "您使用的是自编译版本或测试版本。")
	} else if version != newestTag {
		// 如果当前版本不是最新 tag，则输出 URL
		Log(LogLevelInfo, "新版本可用: https://github.com/Diving-Fish/maimaidx-prober/releases/tag/%s", newestTag)
	} else {
		Log(LogLevelInfo, "您使用的是最新版本。")
	}
}
