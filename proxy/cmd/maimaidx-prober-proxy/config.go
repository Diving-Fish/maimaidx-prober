package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/Diving-Fish/maimaidx-prober/proxy/lib"
)

type workingMode int

const (
	workingModeUpdate workingMode = 0
	workingModeExport workingMode = 1 // only for debug or other
)

type config struct {
	UserName    string   `json:"username"`
	Password    string   `json:"password"`
	Mode        string   `json:"mode,omitempty"`
	MaiDiffs    []string `json:"mai_diffs,omitempty"`
	MaiIntDiffs []int
}

func (c *config) getWorkingMode() workingMode {
	if c.Mode == "export" {
		return workingModeExport
	}
	return workingModeUpdate
}

func getMaiDiffs(MaiDiffs []string) (diffs []int, err error) {
	maiDiffMap := map[string]int{
		"0":         0,
		"bas":       0,
		"basic":     0,
		"1":         1,
		"adv":       1,
		"advanced":  1,
		"2":         2,
		"exp":       2,
		"expert":    2,
		"3":         3,
		"mas":       3,
		"master":    3,
		"4":         4,
		"rem":       4,
		"remaster":  4,
		"re:master": 4,
	}
	if len(MaiDiffs) == 0 {
		for i := 0; i <= 4; i++ {
			diffs = append(diffs, i) // 添加元素
		}
	} else {
		diffList := []string{"Basic", "Advanced", "Expert", "Master", "Re:MASTER"}
		diffStr := ""
		for _, diff := range MaiDiffs {
			if intDiff, exist := maiDiffMap[strings.ToLower(diff)]; exist {
				diffs = append(diffs, intDiff)
				diffStr += diffList[intDiff] + " "
			} else {
				Log(LogLevelWarning, "未找到 %s 难度等级，已跳过……", diff)
			}
		}
		if len(diffs) == 0 {
			Log(LogLevelWarning, "未为舞萌 DX 指定任何难度等级，导入将不会产生任何效果")
		} else {
			Log(LogLevelInfo, "您已修改舞萌的难度等级为：%s", diffStr)
		}
	}
	return
}

func initConfig(path string) (config, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		// First run
		lib.GenerateCert()
		os.WriteFile(path, []byte("{\"username\": \"\", \"password\": \"\"}"), 0644)
		return config{}, fmt.Errorf("初次使用请填写 %s 文件，并依据教程完成根证书的安装。", path)
	}

	var obj config
	err = json.Unmarshal(b, &obj)
	if err != nil {
		return config{}, fmt.Errorf("配置文件格式有误，无法解析：%w。请检查 %s 文件的内容", err, path)
	}

	return obj, nil
}
