<template>
  <div id="app">
    <v-container>
      <div :style="$vuetify.breakpoint.mobile ? '' : 'display: flex; align-items: flex-end; justify-content: space-between'">
        <h1>舞萌 DX 查分器</h1>
        <profile />
      </div>
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
      <p class="mb-2">点个 Star 吧！</p>
      <a href="https://github.com/Diving-Fish/maimaidx-prober"
        ><img
          src="https://img.shields.io/github/stars/Diving-Fish/maimaidx-prober?style=social"
      /></a>
      <view-badge class="ml-3" />
      <p class="mt-3">欢迎加入舞萌DX查分器交流群：981682758</p>
      <p>代理工具上线！使用微信客户端导入数据，请查看新版本的使用指南。</p>
      <p style="color: #f44336">
        迁移了数据库以加快网站的响应速度及后续开发。如遇任何无法导入成绩或出错的情况，请及时添加讨论群进行反馈。
      </p>
      <div
        style="
          display: flex;
          line-height: 64px;
          justify-content: center;
          flex-wrap: wrap;
        "
      >
        <v-dialog width="500px" :fullscreen="$vuetify.breakpoint.mobile" v-model="loginVisible">
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
                :fullscreen="$vuetify.breakpoint.mobile"
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
        <v-dialog width="1000px" :fullscreen="$vuetify.breakpoint.mobile" v-model="dialogVisible">
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
        <v-dialog width="500px" :fullscreen="$vuetify.breakpoint.mobile" v-model="feedbackVisible">
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
        <v-dialog v-model="exportVisible" width="500px" :fullscreen="$vuetify.breakpoint.mobile">
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
                <v-select
                  v-model="exportEncoding"
                  label="选择编码"
                  :items="exportEncodings"
                >
                </v-select>
                <v-tooltip bottom>
                  <template v-slot:activator="{ on, attrs }">
                    <v-icon v-bind="attrs" v-on="on" class="ml-4">
                      mdi-help-circle
                    </v-icon>
                  </template>
                  <span
                    >GBK编码一般用于Excel打开，UTF-8编码则可以供部分其他编辑器直接显示。</span
                  >
                </v-tooltip>
              </div>
            </v-card-text>
            <v-card-actions>
              <v-btn class="mr-4" @click="exportToCSV('sd')"
                >导出标准乐谱</v-btn
              >
              <v-btn @click="exportToCSV('dx')">导出 DX 乐谱</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
        <plate-qualifier ref="pq" :music_data="music_data" :records="records" />
        <v-dialog
          v-model="logoutVisible"
          width="500px"
          v-if="username !== '未登录'"
          :fullscreen="$vuetify.breakpoint.mobile"
        >
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
            <v-card-text> 您确定要登出吗？ </v-card-text>
            <v-card-actions>
              <v-btn class="mr-4" @click="logout" color="primary">登出</v-btn>
              <v-btn @click="logoutVisible = false">取消</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
        <v-dialog v-model="allModeVisible" width="500px" :fullscreen="$vuetify.breakpoint.mobile">
          <template #activator="{ on, attrs }">
            <v-btn
              class="mt-3 mr-4"
              v-bind="attrs"
              v-on="on"
              color="deep-orange"
              dark
              >解锁全曲</v-btn
            >
          </template>
          <v-card>
            <v-card-title>
              确认
              <v-spacer />
              <v-btn icon @click="allModeVisible = false">
                <v-icon>mdi-close</v-icon>
              </v-btn>
            </v-card-title>
            <v-card-text
              >解锁全曲可以让您看到所有谱面的定数数据和相对难度，但您无法对这些谱面进行修改。确定解锁全曲？
            </v-card-text>
            <v-card-actions>
              <v-btn class="mr-4" @click="mergeOnAllMode" color="primary"
                >解锁</v-btn
              >
              <v-btn @click="allModeVisible = false">取消</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </div>
      <v-dialog
        width="500px"
        :fullscreen="$vuetify.breakpoint.mobile"
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
          <filter-slider ref="filterSlider"></filter-slider>
          <v-card-text>
            <v-tabs v-model="tab">
              <v-tab key="sd">旧乐谱</v-tab>
              <v-tab key="dx">DX 2021</v-tab>
            </v-tabs>
            <v-tabs-items v-model="tab">
              <v-tab-item key="sd">
                <chart-table
                  @edit="editRow"
                  :search="searchKey"
                  :items="sdDisplay"
                  :limit="25"
                  :loading="loading"
                  :chart_stats="chart_stats"
                  sort-by="achievements"
                >
                </chart-table>
              </v-tab-item>
              <v-tab-item key="dx">
                <chart-table
                  @edit="editRow"
                  :search="searchKey"
                  :items="dxDisplay"
                  :limit="15"
                  :loading="loading"
                  :chart_stats="chart_stats"
                  sort-by="achievements"
                >
                </chart-table>
              </v-tab-item>
            </v-tabs-items>
          </v-card-text>
        </v-card>
      </div>
      <div class="mid" :style="$vuetify.breakpoint.mobile ? '' : 'display: flex'">
        <message @resize="$refs.advertisement.resize()" :style="`flex: 1; ${$vuetify.breakpoint.mobile ? '' : 'min-width: 500px; margin-right: 16px'}`" class="mbe-2"></message>
        <advertisement ref="advertisement" class="mbe-2"></advertisement>
      </div>
      <v-card>
        <v-card-title>更新记录</v-card-title>
        <v-card-text>
          2021/09/06
          更新了查询牌子的功能。<br />
          2021/07/16
          更新了天界 2 的歌曲数据，以及相对难度从现在开始按照 SSS 的人数进行排名了。<br />
          2021/03/18
          加载动画和按难度/定数筛选，你们要的筛选来了。顺便加了个可以看全曲的功能。<br />
          2021/02/26 发布 1.0
          版本，添加了登出按钮，并优化了一些成绩导入方式。提供了代理服务器供便捷导入成绩。<br />
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
import ViewBadge from "../components/ViewBadge.vue";
import GBK from "../plugins/gbk";
import FilterSlider from "../components/FilterSlider.vue";
import Advertisement from "../components/Advertisement.vue";
import Message from '../components/Message.vue';
import Profile from '../components/Profile.vue';
import PlateQualifier from '../components/PlateQualifier.vue';
const xpath = require("xpath"),
  dom = require("xmldom").DOMParser;
const DEBUG = false;
export default {
  name: "App",
  components: {
    ChartTable,
    ViewBadge,
    FilterSlider,
    Advertisement,
    Message,
    Profile,
    PlateQualifier
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
      chart_stats: {},
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
      exportEncoding: "GBK",
      exportEncodings: ["GBK", "UTF-8"],
      logoutVisible: false,
      allModeVisible: false,
    };
  },
  computed: {
    sdDisplay: function () {
      const that = this;
      return this.sdData.filter((elem) => {
        return that.$refs.filterSlider.f(elem);
      });
    },
    dxDisplay: function () {
      const that = this;
      return this.dxData.filter((elem) => {
        return that.$refs.filterSlider.f(elem);
      });
    },
    sdData: function () {
      let data = this.records
        .filter((elem) => {
          return !this.is_new(elem);
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
          return this.is_new(elem);
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
    }
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
    test: function () {
      this.$refs.filterSlider.f(1);
      return false;
    },
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
          this.records.filter((elem) => {
            return elem.block !== true;
          })
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
      const that = this;
      that.loading = true;
      axios
        .get("https://www.diving-fish.com/api/maimaidxprober/music_data")
        .then((resp) => {
          this.music_data = resp.data;
          Promise.allSettled([
            axios.get(
              "https://www.diving-fish.com/api/maimaidxprober/chart_stats"
            ),
            axios.get(
              DEBUG ? "https://www.diving-fish.com/api/maimaidxprober/player/test_data" : "https://www.diving-fish.com/api/maimaidxprober/player/records"
            ),
          ]).then(([resp1, resp2]) => {
            that.chart_stats = resp1.value.data;
            if (resp2.status !== "rejected") {
              const data = resp2.value.data;
              that.username = data.username;
              that.merge(data.records);
            }
            this.$refs.pq.init();
            that.loading = false;
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
      if (record.ds) {
        let arr = ("" + record.ds).split(".")
        if (["7", "8", "9"].indexOf(arr[1]) != -1) {
          record.level = arr[0] + "+"
        } else {
          record.level = arr[0]
        }
      }
      record.level_label = this.level_label[record.level_index];
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
      if (!this.chart_stats[record.title + record.type]) {
        record.tag = 0.5;
      } else {
        let elem = this.chart_stats[record.title + record.type][
          record.level_index
        ];
        if (elem.t) {
          record.tag = (elem.v + 0.5) / elem.t;
        } else {
          record.tag = 0.5;
        }
      }
    },
    mergeOnAllMode: function () {
      this.allModeVisible = false;
      for (const music of this.music_data) {
        //console.log(music);
        for (let j = 0; j < music.ds.length; j++) {
          const record = {
            title: music.title,
            ds: music.ds[j],
            level: music.level[j],
            level_index: j,
            type: music.type,
            achievements: 0,
            dxScore: 0,
            fc: "",
            fs: "",
            rate: "d",
            ra: 0,
            level_label: this.level_label[j],
            block: true,
          };
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
              break;
            }
          }
          if (flag) {
            this.records.push(record);
          }
        }
      }
      //console.log(this.records);
      for (let i = 0; i < this.records.length; i++) {
        this.computeRecord(this.records[i]);
      }
    },
    is_new: function (record) {
      for (const music of this.music_data) {
        if (record.title == music.title && record.type == music.type) {
          return music.basic_info.is_new;
        }
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
      const blob = new Blob([
        this.exportEncoding === "GBK" ? new Uint8Array(GBK.encode(text)) : text,
      ]);
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = type == "sd" ? "标准乐谱.csv" : "DX 乐谱.csv";
      a.click();
    },
    logout: function () {
      const setCookie = function (cname, cvalue, exdays) {
        var d = new Date();
        d.setTime(d.getTime() + exdays * 24 * 60 * 60 * 1000);
        var expires = "expires=" + d.toUTCString();
        document.cookie = cname + "=" + cvalue + "; " + expires + ";path=/";
      };
      setCookie("jwt_token", "", -1);
      this.logoutVisible = false;
      window.location.reload();
    },
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

.mid {
  justify-content: space-between;
}

.mbe-2 {
  margin-bottom: 2em;
}
</style>