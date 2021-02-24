const express = require('express');
const bodyParser = require('body-parser')
const xpath = require("xpath")
const dom = require("xmldom").DOMParser;
const { default: axios } = require('axios');

const app = express();
app.use(bodyParser.text({ limit: '4MB' }));
const port = 8089;

music_data = []

axios.get("https://www.diving-fish.com/api/maimaidxprober/music_data").then(resp => {
    music_data = resp.data
})

const getDS = function (title, index, type) {
    for (const music of music_data) {
        if (music.type == type && music.title == title) {
            return music.ds[index];
        }
    }
}

const level_label = ["Basic", "Advanced", "Expert", "Master", "Re:MASTER"]

const computeRecord = function (record) {
    record.ds = getDS(record.title, record.level_index, record.type);
    record.level_label = level_label[record.level_index];
    let l = 15;
    const rate = record.achievements;
    if (rate < 50) {
      l = 0;
    } else if (rate < 60) {
      l = 5;
    } else if (rate < 70) {
      l = 6;
    } else if (rate < 75) {
      l = 7;
    } else if (rate < 80) {
      l = 7.5;
    } else if (rate < 90) {
      l = 8;
    } else if (rate < 94) {
      l = 9;
    } else if (rate < 97) {
      l = 9.4;
    } else if (rate < 98) {
      l = 10;
    } else if (rate < 99) {
      l = 11;
    } else if (rate < 99.5) {
      l = 12;
    } else if (rate < 99.99) {
      l = 13;
    } else if (rate < 100) {
      l = 13.5;
    } else if (rate < 100.5) {
      l = 14;
    }
    record.ra = Math.floor(record.ds * (Math.min(100.5, rate) / 100) * l);
    if (isNaN(record.ra)) record.ra = 0;
    // Update Rate
    if (record.achievements < 50) {
      record.rate = "d";
    } else if (record.achievements < 60) {
      record.rate = "c";
    } else if (record.achievements < 70) {
      record.rate = "b";
    } else if (record.achievements < 75) {
      record.rate = "bb";
    } else if (record.achievements < 80) {
      record.rate = "bbb";
    } else if (record.achievements < 90) {
      record.rate = "a";
    } else if (record.achievements < 94) {
      record.rate = "aa";
    } else if (record.achievements < 97) {
      record.rate = "aaa";
    } else if (record.achievements < 98) {
      record.rate = "s";
    } else if (record.achievements < 99) {
      record.rate = "sp";
    } else if (record.achievements < 99.5) {
      record.rate = "ss";
    } else if (record.achievements < 100) {
      record.rate = "ssp";
    } else if (record.achievements < 100.5) {
      record.rate = "sss";
    } else {
      record.rate = "sssp";
    }
  }

const pageToRecordList = function (pageData) {
    try {
        let records = [];
        let doc = new dom().parseFromString(pageData);
        const scores = xpath.select(
            '//div[@class="music_score_block w_120 t_r f_l f_12"]',
            doc
        );
        const labels = ["basic", "advanced", "expert", "master", "remaster"];
        for (const score of scores) {
            let levelNode =
                score.previousSibling.previousSibling.previousSibling
                    .previousSibling.previousSibling.previousSibling.previousSibling
                    .previousSibling;
            let record_data = {
                title: "",
                level: "",
                level_index: labels.indexOf(
                    levelNode.getAttribute("src").match("diff_(.*).png")[1]
                ),
                type: "",
                achievements: 0,
                dxScore: 0,
                rate: "",
                fc: "",
                fs: "",
            };
            const docId = score.parentNode.parentNode.parentNode.getAttribute(
                "id"
            );
            if (docId) {
                if (docId.slice(0, 3) == "sta") record_data.type = "SD";
                else record_data.type = "DX";
            } else {
                record_data.type = score.parentNode.parentNode.nextSibling.nextSibling
                    .getAttribute("src")
                    .match("_(.*).png")[1];
                if (record_data.type == "standard") record_data.type = "SD";
                else record_data.type = "DX";
            }
            record_data.achievements = parseFloat(score.textContent);
            let currentNode = score.previousSibling.previousSibling;
            record_data.title = currentNode.textContent;
            currentNode = currentNode.previousSibling.previousSibling;
            record_data.level = currentNode.textContent;
            currentNode = score.nextSibling.nextSibling;
            record_data.dxScore = parseInt(
                currentNode.textContent.replace(",", "")
            );
            currentNode = currentNode.nextSibling.nextSibling;
            record_data.fs = currentNode
                .getAttribute("src")
                .match("_icon_(.*).png")[1]
                .replace("back", "");
            currentNode = currentNode.nextSibling.nextSibling;
            record_data.fc = currentNode
                .getAttribute("src")
                .match("_icon_(.*).png")[1]
                .replace("back", "");
            currentNode = currentNode.nextSibling.nextSibling;
            record_data.rate = currentNode
                .getAttribute("src")
                .match("_icon_(.*).png")[1];
            records.push(record_data);
        }
        // console.log(records);
        return records;
    } catch (err) {
        console.log(err);
        return {"status": "error"}
    }
}

app.post('/page', (req, res) => {
    let records = pageToRecordList(req.body);
    for (let record of records) {
        computeRecord(record);
    }
    res.send(records);
})

app.listen(port, () => {
    console.log(`Listening at http://localhost:${port}`)
})