<template>
  <div id="mainPage">
    <v-container fluid :style="$vuetify.breakpoint.mobile ? 'padding:0px' : ''">
      <v-container id="tableBody" style="" px-0 py-0>
        <v-card elevation="0">
          <v-card-title
            >成绩表格
            <v-spacer />
            <v-checkbox
              label="使用高级设置"
              v-model="proSetting"
              class="mr-4"
              @click="$refs.proSettings.reset()"
            ></v-checkbox>
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
          <pro-settings
            v-show="proSetting"
            ref="proSettings"
            @setHeaders="setHeaders"
          ></pro-settings>
          <v-card-text>
            <v-tabs v-model="tab">
              <v-tab key="sd">旧乐谱</v-tab>
              <v-tab key="dx">DX 2021</v-tab>
            </v-tabs>
            <v-tabs-items v-model="tab">
              <v-tab-item key="sd">
                <chart-table
                  @cover="coverRow"
                  @edit="editRow"
                  :search="searchKey"
                  :items="sdDisplay"
                  :limit="25"
                  :loading="loading"
                  :headers="headers"
                  sort-by="achievements"
                  :key="JSON.stringify(headers)"
                >
                </chart-table>
              </v-tab-item>
              <v-tab-item key="dx">
                <chart-table
                  @cover="coverRow"
                  @edit="editRow"
                  :search="searchKey"
                  :items="dxDisplay"
                  :limit="15"
                  :loading="loading"
                  :headers="headers"
                  sort-by="achievements"
                  :key="JSON.stringify(headers)"
                >
                </chart-table>
              </v-tab-item>
            </v-tabs-items>
          </v-card-text>
        </v-card>
      </v-container>
      <v-divider class="mb-4" />
      <div
        style="
          display: flex;
          line-height: 64px;
          justify-content: center;
          flex-wrap: wrap;
        "
      >
        <v-btn class="mt-3 mr-4" href="/maimaidx/prober_guide" target="_blank" color="primary"
          >数据导入指南</v-btn
        >
        <v-dialog
          width="1000px"
          :fullscreen="$vuetify.breakpoint.mobile"
          v-model="dialogVisible"
        >
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
        <v-dialog
          width="500px"
          :fullscreen="$vuetify.breakpoint.mobile"
          v-model="feedbackVisible"
        >
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
        <v-dialog
          v-model="exportVisible"
          width="500px"
          :fullscreen="$vuetify.breakpoint.mobile"
        >
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
        <v-dialog
          v-model="allModeVisible"
          width="500px"
          :fullscreen="$vuetify.breakpoint.mobile"
        >
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
        v-model="modifyAchievementVisible"
      >
        <v-card>
          <v-card-title>
            修改完成率
            <v-spacer />
            <v-btn icon @click="modifyAchievementVisible = false">
              <v-icon>mdi-close</v-icon>
            </v-btn>
          </v-card-title>
          <v-card-subtitle>
            修改
            <i
              >{{ currentUpdate.type == "DX" ? "[DX] " : ""
              }}<b>{{ currentUpdate.title }}</b> [{{
                currentUpdate.level_label
              }}]</i
            >
            的完成率为
          </v-card-subtitle>
          <v-card-text>
            <v-form
              ref="modifyAchievementForm"
              @keydown.enter.native="finishEditRow"
            >
              <v-text-field
                label="达成率"
                v-model="currentAchievements"
                :rules="[
                  (u) =>
                    (isFinite(+u) && +u >= 0 && +u <= 101) ||
                    '请输入合法达成率',
                ]"
              />
            </v-form>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn color="primary" @click="finishEditRow()">确定</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-dialog
        width="500px"
        :fullscreen="$vuetify.breakpoint.mobile"
        v-model="coverVisible"
      >
        <v-card>
          <v-card-title>
            查看封面
            <v-spacer />
            <v-btn icon @click="coverVisible = false">
              <v-icon>mdi-close</v-icon>
            </v-btn>
          </v-card-title>
          <v-card-subtitle>
            <i
              ><b>{{ coverItem.title }}</b></i
            >
          </v-card-subtitle>
          <v-row
            class="ma-0"
            align="center"
            justify="center"
            v-if="coverLoading"
          >
            <v-progress-circular
              color="grey"
              indeterminate
            ></v-progress-circular>
          </v-row>
          <v-card-text>
            <v-img
              :src="`https://www.diving-fish.com/covers/${coverItem.song_id}.jpg`"
              contain
              :height="coverLoading ? 0 : undefined"
              @load="coverLoading = false"
            ></v-img>
          </v-card-text>
        </v-card>
      </v-dialog>
      
      <!-- <div
        class="mid"
        :style="$vuetify.breakpoint.mobile ? '' : 'display: flex'"
      >
        <message
          @resize="$refs.advertisement.resize()"
          :style="`flex: 1; ${
            $vuetify.breakpoint.mobile
              ? ''
              : 'min-width: 500px; margin-right: 16px'
          }`"
          class="mbe-2"
        ></message>
        <advertisement ref="advertisement" class="mbe-2"></advertisement>
      </div> -->
    </v-container>
  </div>
</template>

<script>
import api from '../plugins/uni_api.js';
import {mapState} from 'vuex';
import axios from "axios";
import Vue from "vue";
import ChartTable from "../components/ChartTable.vue";
import GBK from "../plugins/gbk";
import FilterSlider from "../components/FilterSlider.vue";
import ProSettings from "../components/ProSettings.vue";
// import Advertisement from "../components/Advertisement.vue";
// import Message from "../components/Message.vue";
import watchVisible from "../plugins/watchVisible";
const xpath = require("xpath"),
  dom = require("xmldom").DOMParser;
export default {
  name: "App",
  components: {
    ChartTable,
    FilterSlider,
    ProSettings,
  },
  data: function () {
    return {
      tab: "",
      chart_stats: {},
      currentUpdate: {},
      currentAchievements: 0,
      username: "未登录",
      activeName: "SD",
      textarea: "",
      searchKey: "",
      level_label: ["Basic", "Advanced", "Expert", "Master", "Re:MASTER"],
      feedbackText: "",
      feedbackVisible: false,
      dialogVisible: false,
      modifyAchievementVisible: false,
      coverVisible: false,
      coverLoading: true,
      coverItem: {},
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
      proSetting: false,
      headers: [
        { text: "排名", value: "rank" },
        { text: "乐曲名", value: "title" },
        { text: "难度", value: "level", sortable: false },
        { text: "定数", value: "ds" },
        { text: "达成率", value: "achievements" },
        { text: "DX Rating", value: "ra" },
        { text: "相对难度", value: "tag" },
        { text: "操作", value: "actions", sortable: false },
      ],
    };
  },
  computed: {
    sdDisplay: function () {
      const that = this;
      return this.sdData.filter((elem) => {
        return (
          that.$refs.filterSlider.f(elem) &&
          (!that.proSetting || that.$refs.proSettings.f(elem))
        );
      });
    },
    dxDisplay: function () {
      const that = this;
      return this.dxData.filter((elem) => {
        return (
          that.$refs.filterSlider.f(elem) &&
          (!that.proSetting || that.$refs.proSettings.f(elem))
        );
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
    },
    ...mapState([
      'records', 'music_data', 'music_data_dict', 'chart_combo'
    ])
  },
  created: function () {
    history.replaceState("", "", window.location.pathname);
    this.fetchMusicData();
  },
  watch: {
    // loginVisible: watchVisible("loginVisible", "Login"),
    // registerVisible: watchVisible("registerVisible", "Register"),
    dialogVisible: watchVisible("dialogVisible", "Import"),
    feedbackVisible: watchVisible("feedbackVisible", "Feedback"),
    exportVisible: watchVisible("exportVisible", "Export"),
    logoutVisible: watchVisible("logoutVisible", "Logout"),
    allModeVisible: watchVisible("allModeVisible", "AllMode"),
    modifyAchievementVisible: watchVisible(
      "modifyAchievementVisible",
      "ModifyAchievement"
    ),
    coverVisible: watchVisible("coverVisible", "Cover"),
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
    coverRow: function (record) {
      this.coverVisible = true;
      if (record.song_id != this.coverItem.song_id) this.coverLoading = true;
      this.coverItem = record;
    },
    editRow: function (record) {
      this.currentUpdate = record;
      this.currentAchievements = this.currentUpdate.achievements;
      this.modifyAchievementVisible = true;
    },
    finishEditRow: function () {
      if (!this.$refs.modifyAchievementForm.validate()) return;
      this.currentUpdate.achievements = parseFloat(this.currentAchievements);
      this.computeRecord(this.currentUpdate);
      if (this.username != "未登录") {
        axios
          .post(
            "https://www.diving-fish.com/api/maimaidxprober/player/update_record",
            this.currentUpdate
          )
          .then(() => {
            this.$message.success("修改已同步");
          })
          .catch(() => {
            this.$message.error("修改失败！");
          });
      } else {
        this.$message.success("修改成功");
      }
      this.modifyAchievementVisible = false;
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
        })
        .catch(() => {
          this.$message.error("数据同步失败！");
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
        })
        .catch(() => {
          this.$message.error("反馈发送失败！");
        });
    },
    fetchMusicData: function () {
      this.loading = true;
      this.$message.info("正在获取乐曲信息……");
      api.fetch_all().then(
        () => {
          for (let i = 0; i < this.records.length; i++) {
            this.computeRecord(this.records[i]);
          }
          this.loading = false;
        }
      );
    },
    computeRecord: function (record) {
      if (this.music_data_dict[record.song_id])
        record.ds = this.music_data_dict[record.song_id].ds[record.level_index];
      if (record.ds) {
        let arr = ("" + record.ds).split(".");
        if (["7", "8", "9"].indexOf(arr[1]) != -1) {
          record.level = arr[0] + "+";
        } else {
          record.level = arr[0];
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
      if (!this.chart_stats[record.song_id]) {
        record.tag = 0.5;
      } else {
        let elem = this.chart_stats[record.song_id][record.level_index];
        if (elem.t) {
          record.tag = (elem.v + 0.5) / elem.t;
        } else {
          record.tag = 0.5;
        }
      }
      if (!this.chart_combo[record.song_id]) {
        record.dxScore_perc = 0;
      } else {
        record.dxScore_perc =
          (record.dxScore /
            (this.chart_combo[record.song_id][record.level_index] * 3)) *
          100;
      }
    },
    mergeOnAllMode: function () {
      this.allModeVisible = false;
      let oldRecords = new Set(
        this.records.map((r) => +r.song_id * 10 + r.level_index)
      );
      for (const music of this.music_data) {
        //console.log(music);
        for (let j = 0; j < music.ds.length; j++) {
          const record = {
            song_id: music.id,
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
          if (
            !oldRecords.has(Number(record.song_id) * 10 + record.level_index)
          ) {
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
      return this.music_data_dict[record.song_id].basic_info.is_new;
    },
    merge: function (records) {
      // console.log(records);
      let oldRecords = Object.fromEntries(
        this.records.map((r, i) => [+r.song_id * 10 + r.level_index, i])
      );
      for (let record of records) {
        let i = oldRecords[+record.song_id * 10 + record.level_index];
        if (typeof i != "undefined") {
          Vue.set(this.records, i, record);
        } else {
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
          const docId =
            name.parentNode.parentNode.parentNode.getAttribute("id");
          if (docId) {
            if (docId.slice(0, 3) == "sta") record_data.type = "SD";
            else record_data.type = "DX";
          } else {
            record_data.type =
              name.parentNode.parentNode.nextSibling.nextSibling
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
      this.$message.success("已登出");
      setTimeout("window.location.reload()", 1000);
    },
    setHeaders: function (headers) {
      this.headers = headers;
    },
  },
};
</script>

<style>
#mainPage {
  margin: auto;
  padding: 30px;
}
#tableBody {
  margin-bottom: 2em;
  max-width: calc(100vw - 60px);
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
