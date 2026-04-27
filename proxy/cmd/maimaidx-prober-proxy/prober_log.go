package main

import (
	"fmt"
	"log"
)

type LogLevel int

const (
	LogLevelInfo    LogLevel = 0
	LogLevelWarning LogLevel = 1
	LogLevelError   LogLevel = 2
)

func Log(level LogLevel, msg string, argv ...interface{}) {
	s := []string{"INFO", "WARN", "ERROR"}
	log.Printf(s[level]+": "+msg+"\n", argv...)
	if progressHubInstance != nil {
		levels := []string{"info", "warn", "error"}
		progressHubInstance.Publish(ProgressEvent{
			Type:    "log",
			Level:   levels[level],
			Message: fmt.Sprintf(msg, argv...),
		})
	}
}
