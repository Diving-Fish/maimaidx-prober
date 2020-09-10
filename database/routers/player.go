package routers

import (
	"github.com/dgrijalva/jwt-go"
	"github.com/kataras/iris/v12"
	"gopkg.in/mgo.v2/bson"
	"maimaidx/prober/db"
	"maimaidx/prober/tools"
	"time"
)

func buildJwtToken(username string) string {
	claims := make(jwt.MapClaims)
	claims["username"] = username
	claims["exp"] = time.Now().Add(time.Hour * 24 * 30).Unix()
	claims["iat"] = time.Now().Unix()
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	ret, _ := token.SignedString([]byte(tools.JwtSecret))
	return ret
}

func decodeJwtToken(token string) (username string, err error) {
	tokenObject, err := jwt.Parse(token, func(token *jwt.Token) (interface{}, error) {
		return []byte(tools.JwtSecret), nil
	})
	if err != nil {
		return "", err
	}
	return tokenObject.Claims.(jwt.MapClaims)["username"].(string), nil
}

func findUser(username string) (m bson.M, err error) {
	err = db.PlayerData.Find(bson.M{"username": username}).One(&m)
	return
}

func Login(ctx iris.Context) {
	var jsonData map[string]interface{}
	ctx.ReadJSON(&jsonData)
	username := jsonData["username"].(string)
	password := jsonData["password"].(string)
	user, err := findUser(username)
	if err != nil || (tools.ToMD5(password + user["salt"].(string)) != user["password"].(string)) {
		ctx.StatusCode(401)
		ctx.JSON(map[string]interface{}{
			"errcode": -3,
			"message": "用户名或密码错误",
		})
		return
	}
	ctx.SetCookieKV("jwt_token", buildJwtToken(username))
	ctx.JSON(map[string]interface{}{
		"message": "登录成功",
	})
}

func CreateUser(ctx iris.Context) {
	var jsonData map[string]interface{}
	ctx.ReadJSON(&jsonData)
	username := jsonData["username"].(string)
	_, err := findUser(username)
	if err == nil {
		ctx.StatusCode(400)
		ctx.JSON(map[string]interface{}{
			"errcode": -1,
			"message": "此用户名已存在",
		})
		return
	}
	password := jsonData["password"].(string)
	records := jsonData["records"].([]interface{})
	salt := tools.RandomString(16)
	db.PlayerData.Insert(bson.M{
		"username": username,
		"password": tools.ToMD5(password + string(salt)),
		"salt": salt,
		"records": records,
	})
	ctx.SetCookieKV("jwt_token", buildJwtToken(username))
	ctx.JSON(map[string]interface{}{
		"message": "注册成功",
	})
}

func PlayerMiddleWare(ctx iris.Context) {
	token := ctx.GetCookie("jwt_token")
	username, err := decodeJwtToken(token)
	if err != nil {
		ctx.StatusCode(403)
		ctx.JSON(map[string]interface{}{
			"errcode": -2,
			"message": "登录凭证错误或已过期，请重新登录",
		})
		return
	}
	ctx.Values().Set("username", username)
	ctx.Next()
}

func GetPlayerData(ctx iris.Context) {
	username := ctx.Values().GetString("username")
	user, err := findUser(username)
	if err != nil {
		ctx.StatusCode(500)
		ctx.JSON(map[string]interface{}{
			"errcode": -101,
			"message": "服务器内部错误",
		})
		return
	}
	ctx.JSON(map[string]interface{} {
		"username": user["username"],
		"records": user["records"],
	})
}

func updateOne(records *[]interface{}, record bson.M) {
	for index, v := range *records {
		m := v.(bson.M)
		if m["level_index"] == record["level_index"] && m["title"] == record["title"] && m["type"] == record["type"] {
			(*records)[index] = record
			return
		}
	}
	*records = append(*records, record)
}

func UpdateRecord(ctx iris.Context) {
	username := ctx.Values().GetString("username")
	user, err := findUser(username)
	if err != nil {
		ctx.StatusCode(500)
		ctx.JSON(map[string]interface{}{
			"errcode": -101,
			"message": "服务器内部错误",
		})
		return
	}
	records := user["records"].([]interface{})
	var record bson.M
	ctx.ReadJSON(&record)
	updateOne(&records, record)
	user["records"] = records
	db.PlayerData.UpdateId(user["_id"], user)
	ctx.JSON(map[string]interface{}{
		"message": "更新成功",
	})
}

func UpdateRecords(ctx iris.Context) {
	username := ctx.Values().GetString("username")
	user, err := findUser(username)
	if err != nil {
		ctx.StatusCode(500)
		ctx.JSON(map[string]interface{}{
			"errcode": -101,
			"message": "服务器内部错误",
		})
		return
	}
	records := user["records"].([]interface{})
	var newRecords []bson.M
	ctx.ReadJSON(&newRecords)
	for _, record := range newRecords {
		updateOne(&records, record)
	}
	user["records"] = records
	db.PlayerData.UpdateId(user["_id"], user)
	ctx.JSON(map[string]interface{}{
		"message": "更新成功",
	})
}