package main

import (
	"github.com/kataras/iris/v12"
	"github.com/kataras/iris/v12/core/router"
	"maimaidx/prober/routers"
)

func main() {
	app := iris.New()
	crs := func(ctx iris.Context) {
		ctx.Header("Access-Control-Allow-Origin", "*")
		ctx.Header("Access-Control-Allow-Credentials", "true")
		ctx.Header("Access-Control-Allow-Methods", "POST, GET, OPTIONS, DELETE, PUT")
		ctx.Header("Access-Control-Allow-Headers", "Access-Control-Allow-Origin,Content-Type,Authorization")
		if ctx.Method() == "OPTIONS" {
			return
		}
		ctx.Next()
	}
	app.Use(crs)
	app.AllowMethods(iris.MethodOptions)
	app.Post("/login", routers.Login)
	app.Post("/register", routers.CreateUser)
	app.Post("/feedback", routers.SendFeedBack)
	app.Get("/music_data", routers.GetMusicData)
	app.PartyFunc("/player", func(p router.Party) {
		p.Use(routers.PlayerMiddleWare)
		p.Get("/records", routers.GetPlayerData)
		p.Post("/update_record", routers.UpdateRecord)
		p.Post("/update_records", routers.UpdateRecords)
	})
	app.Listen("0.0.0.0:8333")
}