<template>
  <div id="app">
    <v-container>
      <h1>舞萌 DX 查分器</h1>
      <v-divider class="mt-4 mb-4" />
      <p>
        <v-btn
          ><a
            href="/maimaidx/prober_guide"
            style="text-decoration: none"
            target="_blank"
            >使用指南</a
          ></v-btn
        >
      </p>
      <p>
        点个 Star 吧！<a href="https://github.com/Diving-Fish/maimaidx-prober"
          ><img
            src="https://img.shields.io/github/stars/Diving-Fish/maimaidx-prober?style=social"
        /></a>
      </p>
      <p>欢迎加入舞萌DX查分器交流群：981682758</p>
      <p>代理工具上线！使用微信客户端导入数据，请查看新版本的使用指南。</p>
      <div
        style="
          display: flex;
          line-height: 64px;
          justify-content: center;
          flex-wrap: wrap;
        "
      >
        <v-dialog width="500px" :fullscreen="mobile" v-model="loginVisible">
          <template #activator="{ on, attrs }">
            <v-btn
              class="mt-3 mr-4"
              v-if="username == '未登录'"
              v-bind="attrs"
              v-on="on"
              color="primary"
              >登录并同步数据</v-btn
            >
          </template>
          <v-card>
            <v-card-title>
              登录
              <v-spacer />
              <v-btn icon @click="loginVisible = false">
                <v-icon>mdi-close</v-icon>
              </v-btn>
            </v-card-title>
            <v-card-text>
              <v-form ref="form" v-model="valid">
                <v-text-field
                  v-model="loginForm.username"
                  label="用户名"
                  :rules="[(u) => !!u || '用户名不能为空']"
                >
                </v-text-field>
                <v-text-field
                  v-model="loginForm.password"
                  label="密码"
                  :rules="[(u) => !!u || '密码不能为空']"
                  type="password"
                >
                </v-text-field>
              </v-form>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn class="mr-4" color="primary" @click="login">登录</v-btn>
              <v-btn @click="invokeRegister">立即注册</v-btn>
              <v-dialog
                width="500"
                :fullscreen="mobile"
                v-model="registerVisible"
              >
                <v-card>
                  <v-card-title>
                    注册
                    <v-spacer />
                    <v-btn icon @click="registerVisible = false">
                      <v-icon>mdi-close</v-icon>
                    </v-btn>
                  </v-card-title>
                  <v-card-subtitle>
                    注册后会自动同步当前已导入的乐曲数据
                  </v-card-subtitle>
                  <v-card-text>
                    <v-form ref="regForm" v-model="valid2">
                      <v-text-field
                        v-model="registerForm.username"
                        label="用户名"
                        :rules="[
                          (u) => !!u || '用户名不能为空',
                          (u) => u.length >= 4 || '用户名至少长 4 个字符',
                        ]"
                      >
                      </v-text-field>
                      <v-text-field
                        v-model="registerForm.password"
                        label="密码"
                        type="password"
                        :rules="[(u) => !!u || '密码不能为空']"
                      >
                      </v-text-field>
                      <v-text-field
                        v-model="registerForm.passwordConfirm"
                        label="确认密码"
                        type="password"
                        :rules="[
                          (u) => !!u || '密码不能为空',
                          (u) => registerForm.password == u || '密码不一致',
                        ]"
                      >
                      </v-text-field>
                    </v-form>
                  </v-card-text>
                  <v-card-actions>
                    <v-spacer />
                    <v-btn color="primary" @click="register">注册</v-btn>
                  </v-card-actions>
                </v-card>
              </v-dialog>
            </v-card-actions>
          </v-card>
        </v-dialog>
        <v-btn v-if="username !== '未登录'" @click="sync()" color="primary" class="mt-3 mr-4"
          >同步数据</v-btn
        >
        <v-dialog width="1000px" :fullscreen="mobile" v-model="dialogVisible">
          <template #activator="{ on, attrs }">
            <v-btn class="mt-3 mr-4" v-bind="attrs" v-on="on">导入数据</v-btn>
          </template>
          <v-card>
            <v-card-title>
              导入数据
              <v-spacer />
              <v-btn icon @click="dialogVisible = false">
                <v-icon>mdi-close</v-icon>
              </v-btn>
            </v-card-title>
            <v-card-text>
              <v-textarea
                type="textarea"
                label="请将乐曲数据的源代码粘贴到这里"
                v-model="textarea"
                :rows="15"
                outlined
              ></v-textarea>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn color="primary" @click="flushData()">确定</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
        <v-dialog width="500px" :fullscreen="mobile" v-model="feedbackVisible">
          <template #activator="{ on, attrs }">
            <v-btn class="mt-3 mr-4" v-bind="attrs" v-on="on">提交反馈</v-btn>
          </template>
          <v-card>
            <v-card-title>
              反馈
              <v-spacer />
              <v-btn icon @click="feedbackVisible = false">
                <v-icon>mdi-close</v-icon>
              </v-btn>
            </v-card-title>
            <v-card-text>
              <v-textarea
                rows="5"
                placeholder="补充乐曲定数或者对查分器有什么意见和建议都可以写在这里"
                v-model="feedbackText"
              ></v-textarea>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn color="primary" @click="sendFeedback()">确定</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
        <v-dialog v-model="exportVisible" width="500px" :fullscreen="mobile">
          <template #activator="{ on, attrs }">
              <v-btn class="mt-3 mr-4" v-bind="attrs" v-on="on">导出为 CSV</v-btn>
          </template>
          <v-card>
            <v-card-title>
              导出为 CSV
              <v-spacer />
              <v-btn icon @click="exportVisible = false">
                <v-icon>mdi-close</v-icon>
              </v-btn>
            </v-card-title>
            <v-card-text>
              <div style="display: flex">
                <v-select v-model="exportEncoding" label="选择编码" :items="exportEncodings">
                </v-select>
                <v-tooltip bottom>
                  <template v-slot:activator="{ on, attrs }">
                    <v-icon
                      v-bind="attrs"
                      v-on="on"
                      class="ml-4"
                    >
                      mdi-help-circle
                    </v-icon>
                  </template>
                  <span>GBK编码一般用于Excel打开，UTF-8编码则可以供部分其他编辑器直接显示。</span>
                </v-tooltip>
              </div>
            </v-card-text>
            <v-card-actions>
              <v-btn class="mr-4" @click="exportToCSV('sd')">导出标准乐谱</v-btn>
              <v-btn @click="exportToCSV('dx')">导出 DX 乐谱</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
        <v-dialog v-model="logoutVisible" width="500px" v-if="username !== '未登录'" :fullscreen="mobile">
          <template #activator="{ on, attrs }">
            <v-btn class="mt-3 mr-4" v-bind="attrs" v-on="on">登出</v-btn>
          </template>
          <v-card>
            <v-card-title>
              确认
              <v-spacer />
              <v-btn icon @click="logoutVisible = false">
                <v-icon>mdi-close</v-icon>
              </v-btn>
            </v-card-title>
            <v-card-text>
              您确定要登出吗？
            </v-card-text>
            <v-card-actions>
              <v-btn class="mr-4" @click="logout" color="primary">登出</v-btn>
              <v-btn @click="logoutVisible = false">取消</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </div>
      <v-dialog
        width="500px"
        :fullscreen="mobile"
        v-model="modifyAchivementVisible"
      >
        <v-card>
          <v-card-title>
            修改完成率
            <v-spacer />
            <v-btn icon @click="modifyAchivementVisible = false">
              <v-icon>mdi-close</v-icon>
            </v-btn>
          </v-card-title>
          <v-card-subtitle>
            修改{{ currentUpdate.title }}（{{
              currentUpdate.level_label
            }}）的完成率为
          </v-card-subtitle>
          <v-card-text>
            <v-text-field v-model="currentAchievements" />
          </v-card-text>
          <v-card-actions>
            <v-btn color="primary" @click="finishEditRow()">确定</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <div id="tableBody" style="margin-top: 2em">
        <v-card>
          <v-card-title
            >成绩表格
            <v-spacer />
            <v-text-field
              v-model="searchKey"
              append-icon="mdi-magnify"
              label="查找乐曲"
              single-line
              hide-details
              class="mb-4"
            ></v-text-field>
          </v-card-title>
          <v-card-subtitle
            >底分: {{ sdRa }} + {{ dxRa }} = {{ sdRa + dxRa }}</v-card-subtitle
          >
          <v-card-text>
            <v-tabs v-model="tab">
              <v-tab key="sd">标准乐谱</v-tab>
              <v-tab key="dx">DX 乐谱</v-tab>
            </v-tabs>
            <v-tabs-items v-model="tab">
              <v-tab-item key="sd">
                <chart-table
                  @edit="editRow"
                  :search="searchKey"
                  :items="sdData"
                  :limit="25"
                  :loading="loading"
                  sort-by="achievements"
                >
                </chart-table>
              </v-tab-item>
              <v-tab-item key="dx">
                <chart-table
                  @edit="editRow"
                  :search="searchKey"
                  :items="dxData"
                  :limit="15"
                  :loading="loading"
                  sort-by="achievements"
                >
                </chart-table>
              </v-tab-item>
            </v-tabs-items>
          </v-card-text>
        </v-card>
      </div>
      <v-card>
        <v-card-title>更新记录</v-card-title>
        <v-card-text>
          2021/02/26 发布 1.0 版本，添加了登出按钮，并优化了一些成绩导入方式。提供了代理服务器供便捷导入成绩。<br />
          2021/02/17 废弃了目前在使用的移动端（Vuetify さいこう！），导出为 csv
          增加了一个二次确认窗口。以及优化了所有的对话框。<br />
          2021/02/15 添加了导出为 csv
          的功能。在导入的页面源代码有问题时新增了报错提示。<br />
          2021/02/10 更改了UI。废弃了微信扫码登录的功能和导出为截图的功能。<br />
          2020/12/12
          大家都在买东西，我在加功能。增加了使用微信扫码导入数据的功能。<br />
          2020/09/26 修正了ENENGY SYNERGY MATRIX的乐曲定数，补充了セイクリッド
          ルイン的定数。增加了评级标签和FC/FS标签<br />
          2020/09/10
          教师节快乐！增加了登录、注册和数据同步的功能，增加了修改单曲完成率的功能，不需要再反复导入数据了<br />
          2020/09/02 增加了导出为截图的功能，增加了Session High⤴ 和
          バーチャルダム ネーション 的 Master 难度乐曲定数<br />
          2020/08/31 发布初版
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script>
import axios from "axios";
import Vue from "vue";
import ChartTable from "../components/ChartTable.vue";
import GBK from "../plugins/gbk";
const xpath = require("xpath"),
  dom = require("xmldom").DOMParser
export default {
  name: "App",
  components: {
    ChartTable,
  },
  data: function () {
    return {
      tab: "",
      loginForm: {
        username: "",
        password: "",
      },
      registerForm: {
        username: "",
        password: "",
        passwordConfirm: "",
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
      ws: null,
      loading: false,
      valid: false,
      valid2: false,
      exportVisible: false,
      exportEncoding: 'GBK',
      exportEncodings: ['GBK', 'UTF-8'],
      logoutVisible: false
    };
  },
  computed: {
    sdDisplay: function () {
      return this.sdData.filter((elem) => {
        return elem.title.indexOf(this.searchKey) !== -1;
      });
    },
    dxDisplay: function () {
      return this.dxData.filter((elem) => {
        return elem.title.indexOf(this.searchKey) !== -1;
      });
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
    mobile: function () {
      return (
        navigator.userAgent.match(
          /(phone|pad|pod|iPhone|iPod|ios|iPad|Android|Mobile|BlackBerry|IEMobile|MQQBrowser|JUC|Fennec|wOSBrowser|BrowserNG|WebOS|Symbian|Windows Phone)/i
        ) !== null
      );
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
    qrDialogVisible: function (to) {
      if (!to) {
        console.log("cancelled by user.");
        this.qrcode = "";
        this.ws.close();
        this.ws = null;
      }
    },
  },
  methods: {
    rawToString: function (text) {
      if (text[text.length - 1] == "p" && text != "ap") {
        return text.substring(0, text.length - 1).toUpperCase() + "+";
      } else {
        return text.toUpperCase();
      }
    },
    invokeRegister: function () {
      this.loginVisible = false;
      this.registerVisible = true;
    },
    editRow: function (record) {
      this.currentUpdate = record;
      this.currentAchievements = this.currentUpdate.achievements;
      this.modifyAchivementVisible = true;
    },
    finishEditRow: function () {
      this.currentUpdate.achievements = this.currentAchievements;
      this.computeRecord(this.currentUpdate);
      if (this.username != "未登录") {
        axios
          .post(
            "https://www.diving-fish.com/api/maimaidxprober/player/update_record",
            this.currentUpdate
          )
          .then(() => {
            this.$message.success("修改已同步");
          });
      } else {
        this.$message.success("修改成功");
      }
      this.modifyAchivementVisible = false;
    },
    register: function () {
      if (!this.$refs.regForm.validate()) return;
      axios
        .post("https://www.diving-fish.com/api/maimaidxprober/register", {
          username: this.registerForm.username,
          password: this.registerForm.password,
          records: this.records,
        })
        .then(() => {
          this.$message.success("注册成功，数据已同步完成");
          this.username = this.registerForm.username;
          this.registerVisible = false;
        })
        .catch((err) => {
          this.$message.error(err.response.data.message);
        });
    },
    sync: function () {
      // console.log(this.records);
      axios
        .post(
          "https://www.diving-fish.com/api/maimaidxprober/player/update_records",
          this.records
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
          axios
            .get(
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
      if (!this.$refs.form.validate()) return;
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
    },
    merge: function (records) {
      // console.log(records);
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
      this.sync();
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
        this.$message.error(
          "导入页面信息出错，请确认您导入的是【记录】-【乐曲成绩】-【歌曲类别】。"
        );
      }
    },
    exportToCSV: function (type) {
      let text = "排名,曲名,难度,等级,定数,达成率, DX Rating\n";
      const escape = function (value) {
        if (value.indexOf(",") == -1) {
          return value;
        } else {
          return `"${value}"`;
        }
      };
      for (const m of this[type + "Data"]) {
        text += `${m.rank},${escape(m.title)},${m.level_label},${m.level},${
          m.ds
        },${m.achievements},${m.ra}\n`;
      }
      const blob = new Blob([this.exportEncoding === 'GBK' ? new Uint8Array(GBK.encode(text)) : text]);
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = type == "sd" ? "标准乐谱.csv" : "DX 乐谱.csv";
      a.click();
    },
    logout: function() {
      const setCookie = function(cname, cvalue, exdays) {
          var d = new Date();
          d.setTime(d.getTime() + (exdays*24*60*60*1000));
          var expires = "expires="+d.toUTCString();
          document.cookie = cname + "=" + cvalue + "; " + expires + ";path=/";
      }
      setCookie("jwt_token", "", -1);
      this.logoutVisible = false;
      window.location.reload();
    }
  },
};
</script>

<style>
#app {
  margin: 30px auto;
}
#tableBody {
  margin-bottom: 2em;
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