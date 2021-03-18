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
  const getSibN = function (node, n) {
    let cur = node;
    let f = false;
    if (n < 0) {
      n = -n;
      f = true;
    }
    for (let i = 0; i < n; i++) {
      if (f)
        cur = cur.previousSibling;
      else
        cur = cur.nextSibling;
    }
    return cur;
  }
  try {
    let link = false;
    let records = [];
    let doc = new dom().parseFromString(pageData);
    // this modify is about to detect two different 'Link'.
    const names = xpath.select(
      '//div[@class="music_name_block t_l f_13 break"]',
      doc
    );
    const labels = ["basic", "advanced", "expert", "master", "remaster"];
    for (const name of names) {
      let title = name.textContent;
      if (title == "Link") {
        if (!link) {
          title = "Link(CoF)"
          link = true;
        }
      }
      let diffNode = getSibN(name, -6);
      let levelNode = getSibN(name, -2);
      let scoreNode = getSibN(name, 2);
      if (scoreNode.tagName !== "div") {
        continue;
      }
      let dxScoreNode = getSibN(name, 4);
      let fcNode = getSibN(name, 6);
      let fsNode = getSibN(name, 8);
      let rateNode = getSibN(name, 10);
      let record_data = {
        title: title,
        level: levelNode.textContent,
        level_index: labels.indexOf(
          diffNode.getAttribute("src").match("diff_(.*).png")[1]
        ),
        type: "",
        achievements: parseFloat(scoreNode.textContent),
        dxScore: parseInt(
          dxScoreNode.textContent.replace(",", "")
        ),
        rate: rateNode
          .getAttribute("src")
          .match("_icon_(.*).png")[1],
        fc: fcNode
          .getAttribute("src")
          .match("_icon_(.*).png")[1]
          .replace("back", ""),
        fs: fsNode
          .getAttribute("src")
          .match("_icon_(.*).png")[1]
          .replace("back", ""),
      };
      const docId = name.parentNode.parentNode.parentNode.getAttribute(
        "id"
      );
      if (docId) {
        if (docId.slice(0, 3) == "sta") record_data.type = "SD";
        else record_data.type = "DX";
      } else {
        record_data.type = name.parentNode.parentNode.nextSibling.nextSibling
          .getAttribute("src")
          .match("_(.*).png")[1];
        if (record_data.type == "standard") record_data.type = "SD";
        else record_data.type = "DX";
      }
      records.push(record_data);
    }
    return records;
  } catch (err) {
    console.log(err);
    return { "status": "error" }
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