package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

var (
	version string = "custom"
)

type Tag struct {
	Name string `json:"name"`
}

// latestTag 取仓库最新的 tag 名。检查更新是纯粹的锦上添花，任何一步失败都
// 只返回错误交给调用方降级处理，不影响后续启动。
func latestTag() (string, error) {
	// api.github.com 在国内经常连不上，给个短超时，别让启动卡在这里
	cl := &http.Client{Timeout: 5 * time.Second}
	resp, err := cl.Get("https://api.github.com/repos/Diving-Fish/maimaidx-prober/tags")
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	// 限流（403 / 429）时 GitHub 返回的是 {"message": ...} 而不是数组，
	// 直接拿去解析只会得到一句看不懂的 unmarshal 报错
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("GitHub 返回 HTTP %d", resp.StatusCode)
	}

	var tags []Tag
	if err := json.NewDecoder(resp.Body).Decode(&tags); err != nil {
		return "", err
	}
	if len(tags) == 0 {
		return "", fmt.Errorf("仓库没有任何 tag")
	}
	return tags[0].Name, nil
}

func checkUpdate() {
	if version == "custom" {
		Log(LogLevelInfo, "您使用的是自编译版本或测试版本。")
		return
	}

	newestTag, err := latestTag()
	if err != nil {
		Log(LogLevelWarning, "检查更新失败：%s，已跳过", err)
		return
	}

	if version != newestTag {
		Log(LogLevelInfo, "新版本可用: https://github.com/Diving-Fish/maimaidx-prober/releases/tag/%s", newestTag)
	} else {
		Log(LogLevelInfo, "您使用的是最新版本。")
	}
}
