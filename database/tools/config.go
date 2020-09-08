package tools

import (
	"encoding/json"
	"io/ioutil"
	"os"
)

var DbURL string
var JwtSecret string

func init() {
	configFile, _ := os.OpenFile("config.json", os.O_RDONLY, 0777)
	config, _ := ioutil.ReadAll(configFile)
	configFile.Close()
	configJSON := map[string]interface{} {}
	json.Unmarshal(config, &configJSON)
	DbURL = configJSON["database_url"].(string)
	JwtSecret = configJSON["jwt_secret"].(string)
}