package tools

import (
	"crypto/md5"
	"fmt"
	"math/rand"
)

func RandomString(length int) string {
	var charSet []byte
	var ret []byte
	for c := '0'; c <= '9'; c++ {
		charSet = append(charSet, byte(c))
	}
	for c := 'A'; c <= 'Z'; c++ {
		charSet = append(charSet, byte(c))
	}
	for c := 'a'; c <= 'z'; c++ {
		charSet = append(charSet, byte(c))
	}
	for i := 0; i < length; i++ {
		ret = append(ret, charSet[rand.Intn(len(charSet))])
	}
	return string(ret)
}

func ToMD5(input string) (output string) {
	return fmt.Sprintf("%x", md5.Sum([]byte(input)))
}
