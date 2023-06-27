package main

import "log"

type LogLevel int

const (
	LogLevelInfo    LogLevel = 0
	LogLevelWarning LogLevel = 1
	LogLevelError   LogLevel = 2
)

func Log(level LogLevel, msg string, argv ...interface{}) {
	s := []string{"INFO", "WARN", "ERROR"}
	log.Printf(s[level]+": "+msg+"\n", argv...)
}
