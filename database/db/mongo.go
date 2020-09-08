package db

import (
	"gopkg.in/mgo.v2"
	"log"
	"maimaidx/prober/tools"
)

var PlayerData *mgo.Collection

func init() {
	session, err := mgo.Dial(tools.DbURL)
	if err != nil {
		log.Fatal(err)
	}
	PlayerData = session.DB("maimaidxprober").C("playerData")
}