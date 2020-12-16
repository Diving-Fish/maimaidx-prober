<template>
  <div id="app">
    <h1>舞萌 DX 查分器</h1>
    <p>
      <a
        href="/maimaidx/prober_guide" target="_blank"
      >使用指南</a>
    </p>
    <p>欢迎加入舞萌DX查分器交流群：981682758</p>
    <p>经反馈，微信更新到3.0版本后无法查看源代码，仍然需要使用该查分器的用户可以从<a href="https://pan.baidu.com/s/1PZOC7W1I1vX6TfaSHmh7EA">此链接（提取码：gj89）</a>下载2.9.5版本的微信安装包。<br>经测试，卸载时选择保存设置数据，数据不会丢失，但仍建议您进行数据备份。</p>
    <el-dialog title="导入数据" :visible.sync="dialogVisible">
      <el-input type="textarea" :rows="15" placeholder="请将乐曲数据的源代码复制到这里" v-model="textarea"></el-input>
      <span slot="footer" class="dialog-footer">
        <el-button type="primary" @click="flushData()">确定</el-button>
      </span>
    </el-dialog>
    <el-dialog title="微信扫码导入数据" :visible.sync="qrDialogVisible">
      <p>该功能基于网页版微信开发，代码已开源。</p>
      <p>如担心数据被盗风险，请使用原来的方式进行数据导入。</p>
      <p>无法使用网页版微信的用户，请使用原来的方式进行数据导入。</p>
      <img :src="'data:image/png;base64,' + qrcode" />
      <p>{{ qrcodePrompt }}</p>
    </el-dialog>
    <el-dialog title="登录" width="30%" :visible.sync="loginVisible">
      <el-form label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="loginForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="loginForm.password" placeholder="请输入密码" type="password" />
        </el-form-item>
        <el-button type="primary" @click="login">登录</el-button>
        <el-button @click="invokeRegister">立即注册</el-button>
      </el-form>
    </el-dialog>
    <el-dialog title="注册" width="30%" :visible.sync="registerVisible">
      <span style="margin-bottom: 30px; display: block">注册后会自动同步当前已导入的乐曲数据</span>
      <el-form label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="registerForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="registerForm.password" placeholder="请输入密码" type="password" />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="registerForm.passwordConfirm" placeholder="请输入密码" type="password" />
        </el-form-item>
        <el-button type="primary" @click="register">注册</el-button>
      </el-form>
    </el-dialog>
    <el-dialog title="反馈" width="40%" :visible.sync="feedbackVisible">
      <el-input
        type="textarea"
        :rows="5"
        placeholder="补充乐曲定数或者对查分器有什么意见和建议都可以写在这里"
        v-model="feedbackText"
      ></el-input>
      <span slot="footer" class="dialog-footer">
        <el-button type="primary" @click="sendFeedback()">确定</el-button>
      </span>
    </el-dialog>
    <el-dialog
      :title="`修改${currentUpdate.title}（${currentUpdate.level_label}）的完成率为`"
      width="40%"
      :visible.sync="modifyAchivementVisible"
    >
      <el-input v-model="currentAchievements" />
      <span slot="footer" class="dialog-footer">
        <el-button type="primary" @click="finishEditRow()">确定</el-button>
      </span>
    </el-dialog>
    <div style="display: flex; margin: 0 auto; width: fit-content">
      <el-button v-if="username == '未登录'" @click="loginVisible = true" type="primary">登录并同步数据</el-button>
      <el-button v-else @click="sync()" type="primary">同步数据</el-button>
      <el-button style="margin-left: 30px" @click="dialogVisible = true">导入数据</el-button>
      <el-button style="margin-left: 30px" @click="screenshot">导出为截图</el-button>
      <el-button style="margin-left: 30px" @click="feedbackVisible = true">提交反馈</el-button>
    </div>
    <el-button style="margin-top: 20px" @click="scanQRCode" type="danger">使用微信扫码导入数据（不推荐）</el-button>
    <div id="tableBody">
      <p>底分: {{ sdRa }} + {{ dxRa }} = {{ sdRa + dxRa }}</p>
      <el-input placeholder="搜索乐曲" v-model="searchKey"></el-input>
      <el-tabs v-model="activeName">
        <el-tab-pane label="标准乐谱" name="SD">
          <el-table :data="sdDisplay" style="width: 100%">
            <el-table-column prop="rank" label="排名" width="80" />
            <el-table-column label="乐曲名">
              <template slot-scope="scope">
                <a>{{ scope.row.title }}</a>
                <el-tag size="small" style="margin-left: 10px" type="success" v-if="scope.row.fc">{{ rawToString(scope.row.fc) }}</el-tag>
                <el-tag size="small" style="margin-left: 10px" v-if="scope.row.fs">{{ rawToString(scope.row.fs) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="难度" width="180">
              <template slot-scope="scope">
                <a
                  :class="'difficulty' + scope.row.level_index"
                >{{ scope.row.level_label }} {{ scope.row.level }}</a>
              </template>
            </el-table-column>
            <el-table-column prop="ds" sortable label="定数" width="120" />
            <el-table-column sort-by="achievements" sortable label="达成率" width="180">
              <template slot-scope="scope">{{ scope.row.achievements.toFixed(4) }}%
                <el-tag size="small" style="margin-left: 10px" type="info">{{ rawToString(scope.row.rate) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="DX Rating" width="120">
              <template slot-scope="scope">
                <a v-if="scope.row.rank <= 25" style="color: #3CB371">{{ scope.row.ra }}</a>
                <a v-else>{{ scope.row.ra }}</a>
              </template>
            </el-table-column>
            <el-table-column label="编辑" width="60">
              <template slot-scope="scope">
                <el-button @click="editRow(scope.row)" icon="el-icon-edit" circle></el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="DX 乐谱" name="DX">
          <el-table :data="dxDisplay" style="width: 100%">
            <el-table-column prop="rank" label="排名" width="80" />
            <el-table-column label="乐曲名">
              <template slot-scope="scope">
                <a>{{ scope.row.title }}</a>
                <el-tag size="small" style="margin-left: 10px" type="success" v-if="scope.row.fc">{{ rawToString(scope.row.fc) }}</el-tag>
                <el-tag size="small" style="margin-left: 10px" v-if="scope.row.fs">{{ rawToString(scope.row.fs) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="难度" width="180">
              <template slot-scope="scope">
                <a
                  :class="'difficulty' + scope.row.level_index"
                >{{ scope.row.level_label }} {{ scope.row.level }}</a>
              </template>
            </el-table-column>
            <el-table-column prop="ds" sortable label="定数" width="120" />
            <el-table-column sort-by="achievements" sortable label="达成率" width="180">
              <template slot-scope="scope">{{ scope.row.achievements.toFixed(4) }}%
                <el-tag size="small" style="margin-left: 10px" type="info">{{ rawToString(scope.row.rate) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="DX Rating" width="120">
              <template slot-scope="scope">
                <a v-if="scope.row.rank <= 15" style="color: #3CB371">{{ scope.row.ra }}</a>
                <a v-else>{{ scope.row.ra }}</a>
              </template>
            </el-table-column>
            <el-table-column label="编辑" width="60">
              <template slot-scope="scope">
                <el-button @click="editRow(scope.row)" icon="el-icon-edit" circle></el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>
    <div style="border-top: 2px #E4E7ED solid; text-align: left">
      <h3>更新记录</h3>
      <p>2020/12/12 大家都在买东西，我在加功能。增加了使用微信扫码导入数据的功能。</p>
      <p>2020/09/26 修正了ENENGY SYNERGY MATRIX的乐曲定数，补充了セイクリッド ルイン的定数。增加了评级标签和FC/FS标签</p>
      <p>2020/09/10 教师节快乐！增加了登录、注册和数据同步的功能，增加了修改单曲完成率的功能，不需要再反复导入数据了</p>
      <p>2020/09/02 增加了导出为截图的功能，增加了Session High⤴ 和 バーチャルダム ネーション 的 Master 难度乐曲定数</p>
      <p>2020/08/31 发布初版</p>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import Vue from 'vue';
const xpath = require("xpath"),
  dom = require("xmldom").DOMParser,
  html2canvas = require("html2canvas");
export default {
  name: "App",
  data: function () {
    return {
      loginForm: {
        username: "",
        password: "",
      },
      registerForm: {
        username: "",
        password: "",
        passwordConfirm: ""
      },
      currentUpdate: {},
      currentAchievements: 0,
      username: "未登录",
      activeName: "SD",
      textarea: "",
      searchKey: "",
      records: [],
      music_data: [],
      level_label: ["Basic", "Advanced", "Expert", "Master", "Re:MASTER"],
      feedbackText: "",
      feedbackVisible: false,
      loginVisible: false,
      registerVisible: false,
      dialogVisible: false,
      modifyAchivementVisible: false,
      qrDialogVisible: false,
      qrcode: "",
      qrcodePrompt: "",
      ws: null
    };
  },
  computed: {
    sdDisplay: function () {
      return this.sdData.filter((elem) => {return elem.title.indexOf(this.searchKey) !== -1});
    },
    dxDisplay: function () {
      return this.dxData.filter((elem) => {return elem.title.indexOf(this.searchKey) !== -1});
    },
    sdData: function () {
      let data = this.records
        .filter((elem) => {
          return elem.type == "SD";
        })
        .sort((a, b) => {
          return b.ra - a.ra;
        });
      for (let i = 0; i < data.length; i++) {
        data[i].rank = i + 1;
      }
      return data;
    },
    dxData: function () {
      let data = this.records
        .filter((elem) => {
          return elem.type == "DX";
        })
        .sort((a, b) => {
          return b.ra - a.ra;
        });
      for (let i = 0; i < data.length; i++) {
        data[i].rank = i + 1;
      }
      return data;
    },
    sdRa: function () {
      let ret = 0;
      for (let i = 0; i < Math.min(this.sdData.length, 25); i++) {
        ret += this.sdData[i].ra;
      }
      return ret;
    },
    dxRa: function () {
      let ret = 0;
      for (let i = 0; i < Math.min(this.dxData.length, 15); i++) {
        ret += this.dxData[i].ra;
      }
      return ret;
    },
  },
  created: function () {
    this.fetchMusicData();
  },
  watch: {
    currentAchievements: function (to) {
      if (to == "") return;
      let flag = true;
      if (to.toString().match(/\.0*$/)) flag = false;
      const r = parseFloat(to);
      if (isNaN(r)) {
        this.currentAchievements = 0;
      } else {
        if (r < 0) {
          this.currentAchievements = 0;
        } else if (r > 101) {
          this.currentAchievements = 101;
        } else {
          if (flag) this.currentAchievements = r;
        }
      }
    },
    qrDialogVisible: function(to) {
      if (!to) {
        console.log("cancelled by user.")
        this.qrcode = ""
        this.ws.close()
        this.ws = null
      }
    }
  },
  methods: {
    scanQRCode: function() {
      this.qrDialogVisible = true
      this.qrcodePrompt = "请使用微信扫描上方二维码，加载二维码需要一定时间，请稍候……"
      this.ws = new WebSocket("wss://www.diving-fish.com:8099/ws")
      this.ws.exitcode = 0
      let main_message = false
      this.ws.onmessage = (event) => {
        if (event.data == "main-part") {
          main_message = true
          this.qrcode = ""
          this.qrcodePrompt = "导入数据需要 30 秒左右，请耐心等待……"
          return
        }
        if (main_message) {
          if (event.data == 'no-web-wx') {
            this.ws.exitcode = -1
            return
          }
          const records = this.pageToRecordList(event.data);
          this.merge(records);
        } else {
          this.qrcode = event.data
        }
      }
      this.ws.onclose = () => {
        if (this.ws.exitcode == 0)
          this.qrcodePrompt = "导入完毕，请关闭窗口"
        else
          this.qrcodePrompt = "您的微信号无法登录网页微信"
        this.ws = null
      }
    },
    rawToString: function(text) {
      if (text[text.length - 1] == 'p' && text != 'ap') {
        return text.substring(0, text.length - 1).toUpperCase() + '+';
      } else {
        return text.toUpperCase();
      }
    },
    invokeRegister: function() {
      this.loginVisible = false;
      this.registerVisible = true;
    },
    editRow: function (record) {
      this.currentUpdate = record;
      this.currentAchievements = this.currentUpdate.achievements;
      this.modifyAchivementVisible = true;
    },
    finishEditRow: function() {
      this.currentUpdate.achievements = this.currentAchievements;
      this.computeRecord(this.currentUpdate);
      if (this.username == '未登录') return
      axios
        .post(
          "https://www.diving-fish.com/api/maimaidxprober/player/update_record", this.currentUpdate
        )
        .then(() => {
          this.$message.success("修改已同步");
        });
    },
    register: function() {
      if (this.registerForm.password !== this.registerForm.passwordConfirm) {
        this.$message.error('两次输入的密码不一致')
        return;
      } 
      if (this.registerForm.username.length < 4) {
        this.$message.error('用户名至少长 4 个字符')
        return;
      }
      axios
        .post("https://www.diving-fish.com/api/maimaidxprober/register", {
          username: this.registerForm.username,
          password: this.registerForm.password,
          records: this.records
        }).then(() => {
          this.$message.success("注册成功，数据已同步完成")
          this.username = this.registerForm.username;
          this.registerVisible = false;
        }).catch(err => {
          this.$message.error(err.response.data.message);
        })
    },
    sync: function () {
      // console.log(this.records);
      axios
        .post(
          "https://www.diving-fish.com/api/maimaidxprober/player/update_records", this.records
        )
        .then(() => {
          this.$message.success("数据已同步完成");
        });
    },
    sendFeedback: function () {
      axios
        .post("https://www.diving-fish.com/api/maimaidxprober/feedback", {
          message: this.feedbackText,
        })
        .then(() => {
          this.$message.success("您的反馈我们已收到，谢谢！");
          this.feedbackVisible = false;
        });
    },
    fetchMusicData: function () {
      axios
        .get("https://www.diving-fish.com/api/maimaidxprober/music_data")
        .then((resp) => {
          this.music_data = resp.data;
          axios.get(
            "https://www.diving-fish.com/api/maimaidxprober/player/records"
          )
          .then((resp) => {
            const data = resp.data;
            this.username = data.username;
            this.merge(data.records);
          });
        });
    },
    login: function () {
      axios
        .post("https://www.diving-fish.com/api/maimaidxprober/login", {
          username: this.loginForm.username,
          password: this.loginForm.password,
        })
        .then(() => {
          this.$message.success("登录成功，加载乐曲数据中……");
          axios
            .get(
              "https://www.diving-fish.com/api/maimaidxprober/player/records"
            )
            .then((resp) => {
              const data = resp.data;
              this.username = data.username;
              this.merge(data.records);
              this.loginVisible = false;
            });
        })
        .catch((err) => {
          this.$message.error(err.response.data.message);
        });
    },
    screenshot: function () {
      const saveFile = function (data, filename) {
        var save_link = document.createElementNS(
          "http://www.w3.org/1999/xhtml",
          "a"
        );
        save_link.href = data;
        save_link.download = filename;

        var event = document.createEvent("MouseEvents");
        event.initMouseEvent(
          "click",
          true,
          false,
          window,
          0,
          0,
          0,
          0,
          0,
          false,
          false,
          false,
          false,
          0,
          null
        );
        save_link.dispatchEvent(event);
      };
      const dom = document.querySelector("#tableBody");
      html2canvas(dom, {
        height: Math.min(2048, dom.clientHeight),
      }).then((canvas) => {
        const pageData = canvas.toDataURL("image/jpeg", 1.0);
        saveFile(
          pageData.replace("image/jpeg", "image/octet-stream"),
          (this.activeName == "SD" ? "标准乐谱" : "DX乐谱") + ".jpg"
        );
      });
    },
    computeRecord: function (record) {
      record.ds = this.getDS(record.title, record.level_index, record.type);
      record.level_label = this.level_label[record.level_index];
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
        record.rate = 'd'
      } else if (record.achievements < 60) {
        record.rate = 'c'
      } else if (record.achievements < 70) {
        record.rate = 'b'
      } else if (record.achievements < 75) {
        record.rate = 'bb'
      } else if (record.achievements < 80) {
        record.rate = 'bbb'
      } else if (record.achievements < 90) {
        record.rate = 'a'
      } else if (record.achievements < 94) {
        record.rate = 'aa'
      } else if (record.achievements < 97) {
        record.rate = 'aaa'
      } else if (record.achievements < 98) {
        record.rate = 's'
      } else if (record.achievements < 99) {
        record.rate = 'sp'
      } else if (record.achievements < 99.5) {
        record.rate = 'ss'
      } else if (record.achievements < 100) {
        record.rate = 'ssp'
      } else if (record.achievements < 100.5) {
        record.rate = 'sss'
      } else {
        record.rate = 'sssp'
      } 
    },
    merge: function (records) {
      for (let record of records) {
        let flag = true;
        for (let i = 0; i < this.records.length; i++) {
          const ex = this.records[i];
          if (
            ex.title === record.title &&
            ex.type === record.type &&
            ex.level === record.level &&
            ex.level_index == record.level_index
          ) {
            flag = false;
            Vue.set(this.records, i, record);
            // this.records[i] = record;
            break;
          }
        }
        // console.log(flag);
        if (flag) {
          this.records.push(record);
        }
      }
      for (let i = 0; i < this.records.length; i++) {
        this.computeRecord(this.records[i]);
      }
      // console.log(this.records);
    },
    flushData: function () {
      const records = this.pageToRecordList(this.textarea);
      this.merge(records);
      this.textarea = "";
      this.dialogVisible = false;
    },
    getDS: function (title, index, type) {
      for (const music of this.music_data) {
        if (music.type == type && music.title == title) {
          return music.ds[index];
        }
      }
    },
    pageToRecordList: function (pageData) {
      let records = [];
      let doc = new dom().parseFromString(pageData);

      const scores = xpath.select(
        '//div[@class="music_score_block w_120 t_r f_l f_12"]',
        doc
      );
      const labels = ["basic", "advanced", "expert", "master", "remaster"];

      for (const score of scores) {
        let levelNode =
          score.previousSibling.previousSibling.previousSibling.previousSibling
            .previousSibling.previousSibling.previousSibling.previousSibling;
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
        const docId = score.parentNode.parentNode.parentNode.getAttribute("id");
        if (docId) {
          record_data.type = docId.match(/(.*)_/)[1];
          if (record_data.type == "sta") record_data.type = "SD";
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
    },
  },
};
</script>

<style>
#app {
  width: 80%;
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin: 30px auto;
}

.difficulty4 {
  color: #ba67f8;
}

.difficulty3 {
  color: #9e45e2;
}

.difficulty2 {
  color: #f64861;
}

.difficulty1 {
  color: #fb9c2d;
}

.difficulty0 {
  color: #22bb5b;
}
</style>
