package routers

import (
	"github.com/kataras/iris/v12"
	"gopkg.in/mgo.v2/bson"
	"maimaidx/prober/db"
)

func GetMusicData(ctx iris.Context) {
	var result []bson.M
	db.MusicData.Find(bson.M{}).All(&result)
	ctx.JSON(result)
}