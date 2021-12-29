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
        <v-tab-item><main-page ref="mainpage" @pq="init_pq" /></v-tab-item>
        <v-tab-item><calculators /></v-tab-item>
        <v-tab-item eager><plate-qualifier /></v-tab-item> <!-- eager: force loading plate qualifier; for usage in profile component -->
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
import MainPage from "./pages/MainPage.vue";
import UserComponent from "./components/UserComponent.vue";
import ViewBadge from "./components/ViewBadge.vue";
import Tutorial from "./components/Tutorial.vue";
import UpdateLog from "./components/UpdateLog.vue";
import Calculators from './components/Calculators.vue';
import PlateQualifier from './components/PlateQualifier.vue';
import { mapState } from 'vuex';
export default {
  components: { MainPage, UserComponent, ViewBadge, Tutorial, UpdateLog, Calculators, PlateQualifier},
  data() {
    return {
      selected: 0,
      tab: "成绩表格",
    };
  },
  methods: {
    init_pq: function() {
      this.$refs.pq.init();
    },
  },
  computed: mapState(["username"])
};
</script>

<style>
.tab-container {
  align-items: start !important;
  justify-content: center !important;
}
</style>