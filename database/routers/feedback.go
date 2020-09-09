package routers

import (
	"github.com/kataras/iris/v12"
	"maimaidx/prober/db"
)

func SendFeedBack(ctx iris.Context) {
	var jsonObject map[string]interface{}
	ctx.ReadJSON(&jsonObject)
	db.FeedBack.Insert(jsonObject)
	ctx.JSON(map[string]interface{} {
		"message": "提交成功",
	})
}
