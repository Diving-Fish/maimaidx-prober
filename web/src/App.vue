<template>
  <v-app>
    <v-app-bar>
      <v-app-bar-title class="title">舞萌 DX 查分器</v-app-bar-title>
      <v-divider style="margin-left: 4em" inset vertical />
      <v-tabs v-model="tab" class="ml-8">
        <v-tab style="font-size: 16px">成绩表格</v-tab>
        <v-tab style="font-size: 16px">计算器</v-tab>
        <v-tab :disabled="username == ''" style="font-size: 16px">极/将/神/舞舞查询</v-tab>
        <v-tab style="font-size: 16px">使用说明</v-tab>
        <v-tab style="font-size: 16px">更新记录</v-tab>
      </v-tabs>
      <v-spacer />
      <v-divider class="mr-8" inset vertical />
      <user-component :username="username" />
    </v-app-bar>
    <v-container fluid class="mt-2 fill-height tab-container" :style="$vuetify.breakpoint.mobile ? 'padding:0px' : ''">
      <v-tabs-items v-model="tab">
        <v-tab-item><main-page ref="mainpage" @pq="init_pq" :music_data="music_data" :records="records" /></v-tab-item>
        <v-tab-item><calculators /></v-tab-item>
        <v-tab-item><plate-qualifier ref="pq" :music_data="music_data" :records="records" /></v-tab-item>
        <v-tab-item><tutorial /></v-tab-item>
        <v-tab-item><update-log /></v-tab-item>
      </v-tabs-items>
    </v-container>
    <v-footer style="justify-content: center; padding: 10px">
      <a href="https://github.com/Diving-Fish/maimaidx-prober"
        ><img
          src="https://img.shields.io/github/stars/Diving-Fish/maimaidx-prober?style=social"
      /></a>
      <view-badge class="ml-3" />
      <a class="ml-3" href="https://space.bilibili.com/10322617"
        ><img
          src="https://shields.io/badge/bilibili-%E6%B0%B4%E9%B1%BC%E5%96%B5%E5%96%B5%E5%96%B5-00A1D6?logo=bilibili&style=flat"
      /></a>
    </v-footer>
  </v-app>
</template>

<script>
import axios from "axios";
import MainPage from "./pages/MainPage.vue";
import UserComponent from "./components/UserComponent.vue";
import ViewBadge from "./components/ViewBadge.vue";
import Tutorial from "./components/Tutorial.vue";
import UpdateLog from "./components/UpdateLog.vue";
import Calculators from './components/Calculators.vue';
import PlateQualifier from './components/PlateQualifier.vue';
export default {
  components: { MainPage, UserComponent, ViewBadge, Tutorial, UpdateLog, Calculators, PlateQualifier},
  data() {
    return {
      selected: 0,
      username: "",
      tab: "成绩表格",
      music_data: [],
      records: []
    };
  },
  methods: {
    init_pq: function() {
      this.$refs.pq.init();
    },
    login: function (form) {
      axios
        .post("https://www.diving-fish.com/api/maimaidxprober/login", {
          username: form.username,
          password: form.password,
        })
        .then(() => {
          this.$message.success("登录成功，加载乐曲数据中……");
          this.loading = true;
          this.loginVisible = false;
          this.$refs.profile.fetch();
          axios
            .get(
              "https://www.diving-fish.com/api/maimaidxprober/player/records"
            )
            .then((resp) => {
              const data = resp.data;
              this.username = data.username;
              this.merge(data.records);
              this.loading = false;
            })
            .catch(() => {
              this.$message.error("加载乐曲失败！");
            });
        })
        .catch((err) => {
          this.$message.error("登录失败！");
          this.$message.error(err.response.data.message);
        });
    },
    register: function (form) {
      axios
        .post("https://www.diving-fish.com/api/maimaidxprober/register", {
          username: form.username,
          password: form.password,
          records: this.$refs.mainpage.records,
        })
        .then(() => {
          this.$message.success("注册成功，数据已同步完成");
          this.username = form.username;
          this.registerVisible = false;
          // setTimeout("window.location.reload()", 1000);
        })
        .catch((err) => {
          this.$message.error("注册失败！");
          this.$message.error(err.response.data.message);
        });
    },
  },
};
</script>

<style>
.tab-container {
  align-items: start !important;
  justify-content: center !important;
}
</style>