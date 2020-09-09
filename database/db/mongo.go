package db

import (
	"gopkg.in/mgo.v2"
	"log"
	"maimaidx/prober/tools"
)

var PlayerData *mgo.Collection
var MusicData *mgo.Collection
var FeedBack *mgo.Collection

func init() {
	session, err := mgo.Dial(tools.DbURL)
	if err != nil {
		log.Fatal(err)
	}
	PlayerData = session.DB("maimaidxprober").C("playerData")
	MusicData = session.DB("maimaidxprober").C("musicData")
	FeedBack = session.DB("maimaidxprober").C("feedBack")
}