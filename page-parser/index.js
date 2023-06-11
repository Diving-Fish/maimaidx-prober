const express = require("express");
const bodyParser = require("body-parser");
const xpath = require("xpath");
const dom = require("xmldom").DOMParser;
const { default: axios } = require("axios");
const xmldom = require("xmldom");
const fs = require("fs");

music_data = [];
axios
  .get("https://www.diving-fish.com/api/maimaidxprober/music_data")
  .then((resp) => {
    music_data = resp.data;
  });

const getDS = function (title, index, type) {
  for (const music of music_data) {
    if (music.type == type && music.title == title) {
      return music.ds[index];
    }
  }
};

const level_label = ["Basic", "Advanced", "Expert", "Master", "Re:MASTER"];

const computeRecord = function (record) {
  record.ds = getDS(record.title, record.level_index, record.type);
  record.level_label = level_label[record.level_index];
  let l = 14;
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
    l = 8.5;
  } else if (rate < 94) {
    l = 9.5;
  } else if (rate < 97) {
    l = 10.5;
  } else if (rate < 98) {
    l = 12.5;
  } else if (rate < 99) {
    l = 12.7;
  } else if (rate < 99.5) {
    l = 13;
  } else if (rate < 100) {
    l = 13.2;
  } else if (rate < 100.5) {
    l = 13.5;
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
};

const pageToRecordList = function (pageData) {
  const getSibN = function (node, n) {
    let cur = node;
    let f = false;
    if (n < 0) {
      n = -n;
      f = true;
    }
    for (let i = 0; i < n; i++) {
      if (f) cur = cur.previousSibling;
      else cur = cur.nextSibling;
    }
    return cur;
  };

  let link = false;
  let records = [];
  let doc = new dom({
    locator: {},
    errorHandler: {
      warning: function (w) {},
      error: function (e) {},
      fatalError: function (e) {
        console.error(e);
      },
    },
  }).parseFromString(pageData);
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
        title = "Link(CoF)";
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
    let fsNode = getSibN(name, 6);
    let fcNode = getSibN(name, 8);
    let rateNode = getSibN(name, 10);
    let record_data = {
      title: title,
      level: levelNode.textContent,
      level_index: labels.indexOf(
        diffNode.getAttribute("src").match("diff_(.*).png")[1]
      ),
      type: "",
      achievements: parseFloat(scoreNode.textContent),
      dxScore: parseInt(dxScoreNode.textContent.replace(",", "")),
      rate: rateNode.getAttribute("src").match("_icon_(.*).png")[1],
      fc: fcNode
        .getAttribute("src")
        .match("_icon_(.*).png")[1]
        .replace("back", ""),
      fs: fsNode
        .getAttribute("src")
        .match("_icon_(.*).png")[1]
        .replace("back", ""),
    };
    const docId = name.parentNode.parentNode.parentNode.getAttribute("id");
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
};

/**
 * 好友对战 html 解析函数, 格式：
 * <login><u>{username}</u><p>{password}</p></login>
 * <dxscorevs>{dx对战页面的html}</dxscorevs>
 * <achievementsvs>{<achievement对战页面的html}</achievementsvs>
 *
 * author @bakapiano
 */
const friendVSPageToRecordList = function (pageData) {
  const recordMap = {};
  const labels = ["basic", "advanced", "expert", "master", "remaster"];
  labels.forEach((label) => {
    recordMap[label] = {};
  });
  const doc = new dom({
    locator: {},
    errorHandler: {
      warning: function (w) {},
      error: function (e) {},
      fatalError: function (e) {
        console.error(e);
      },
    },
  }).parseFromString(pageData);

  ["dxscorevs", "achievementsvs"].forEach((pageType) => {
    for (const label of labels) {
      const elements = xpath.select(
        `//div[@class="music_${label}_score_back w_450 m_15 p_3 f_0"]`,
        doc
      );
      if (elements.length === 0) continue;

      const parseElement = (e) => {
        const result = {};
        result.title = e.getElementsByTagName("div")[2].textContent.trim();
        result.level = e.getElementsByTagName("div")[1].textContent.trim();
        result.type = "";
        result.level_index = labels.indexOf(label);
        result.type = e
          .getElementsByTagName("img")[1]
          .getAttribute("src")
          .toString()
          .trim()
          .endsWith("standard.png")
          ? "SD"
          : "DX";

        const fcNode = e
          .getElementsByTagName("tbody")[0]
          .getElementsByTagName("tr")[1]
          .getElementsByTagName("td")[1]
          .getElementsByTagName("img")[1];
        const fsNode = e
          .getElementsByTagName("tbody")[0]
          .getElementsByTagName("tr")[1]
          .getElementsByTagName("td")[1]
          .getElementsByTagName("img")[0];
        const rateNode = e
          .getElementsByTagName("tbody")[0]
          .getElementsByTagName("tr")[1]
          .getElementsByTagName("td")[1]
          .getElementsByTagName("img")[2];
        (result.rate = rateNode.getAttribute("src").match("_icon_(.*).png")[1]),
          (result.fc = fcNode
            .getAttribute("src")
            .match("_icon_(.*).png")[1]
            .replace("back", ""));
        result.fs = fsNode
          .getAttribute("src")
          .match("_icon_(.*).png")[1]
          .replace("back", "");

        const scoreString = e
          .getElementsByTagName("tbody")[0]
          .getElementsByTagName("tr")[0]
          .getElementsByTagName("td")[2]
          .textContent.replace(",", "")
          .replace("%", "")
          .trim();
        if (scoreString === "―") return;

        if (pageType === "dxscorevs") {
          result.dxScore = parseInt(scoreString);
          recordMap[label][result.title] = result;
        } else {
          result.achievements = parseFloat(scoreString);
          recordMap[label][result.title].achievements = result.achievements;
        }
      };

      elements.forEach(parseElement);
      break;
    }
  });

  const results = [];
  Object.values(recordMap).forEach((map) => {
    Object.values(map).forEach((record) => {
      results.push(record);
    });
  });
  return results;
};

const getLoginedUploader = async (body) => {
  const loginCredentials = body.slice(7, body.indexOf("</login>"));
  let xml = new dom().parseFromString(loginCredentials);
  const u = xml.getElementsByTagName("u")[0].textContent;
  const p = xml.getElementsByTagName("p")[0].textContent;

  const resp = await axios.post(
    "https://www.diving-fish.com/api/maimaidxprober/login",
    {
      username: u,
      password: p,
    }
  );
  const token = resp.headers["set-cookie"][0];
  const cookiePayload = token.slice(0, token.indexOf(";"));

  return async (records) => {
    await axios.post(
      "https://www.diving-fish.com/api/maimaidxprober/player/update_records",
      records,
      {
        headers: {
          cookie: cookiePayload,
        },
      }
    );
  };
};

const serve = (pageParser) => {
  return async (req, res) => {
    // Try parse records
    try {
      let records = pageParser(req.body);
      for (let record of records) {
        computeRecord(record);
      }
    }
    catch (err) {
      res.status(400).send({ message: "Failed to parse body" });
      return
    }

    // Get login credentials
    if (req.body.startsWith("<login>")) {
      let upload = null;
      try {
        upload = await getLoginedUploader(req.body);
      } catch (err) {
        console.log(err);
        res.status(401).send({ message: "login failed" });
        return;
      }

      await upload(records);
      res.send({ message: "success" });
    } else {
      res.send(records);
    }
  };
};

const app = express();
app.use(bodyParser.text({ limit: "32MB" }));
app.all("*", function (req, res, next) {
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Headers", "content-type");
  res.header("Access-Control-Allow-Methods", "DELETE,PUT,POST,GET,OPTIONS");
  if (req.method.toLowerCase() == "options") res.send(200);
  else next();
});
const port = 8089;

app.post("/page/friendVS", serve(friendVSPageToRecordList));
app.post("/page", serve(pageToRecordList));
app.listen(port, () => {
  console.log(`Listening at http://localhost:${port}`);
});
