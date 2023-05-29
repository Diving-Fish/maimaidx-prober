package main

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/Diving-Fish/maimaidx-prober/proxy/lib"
)

type WorkingMode int

const (
	MODE_UPDATE WorkingMode = 0
	MODE_EXPORT WorkingMode = 1 // only for debug or other
)

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
