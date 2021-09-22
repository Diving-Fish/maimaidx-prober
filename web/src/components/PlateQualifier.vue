<template>
  <v-dialog
    v-model="visible"
    :width="masOnly ? 500 : 1000"
    :fullscreen="$vuetify.breakpoint.mobile"
  >
    <template #activator="{ on, attrs }">
      <v-btn class="mt-3 mr-4" v-bind="attrs" v-on="on">牌子查询</v-btn>
    </template>
    <v-card>
      <v-card-title>
        极将神牌辅助查询工具
        <v-spacer />
        <v-btn icon @click="visible = false">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      <v-card-text>
        <!-- <v-chip>{{ versions }}</v-chip> -->
        <v-row>
          <v-col :cols="6"
            ><v-select v-model="version" :items="versions" label="选择版本"
          /></v-col>
          <v-col :cols="6"
            ><v-checkbox v-model="masOnly" label="仅查看Master"
          /></v-col>
        </v-row>
        <div>
          <v-icon color="green">mdi-check-bold</v-icon>=Full Combo
          <v-icon color="blue">mdi-check-bold</v-icon>=SSS
          <v-icon color="purple">mdi-check-bold</v-icon>=Full Sync DX
          <v-icon color="orange">mdi-check-bold</v-icon>=All Perfect
        </div>
        <div class="mt-2">
          <v-icon color="green">mdi-check-bold</v-icon>{{total_1}}/{{filted.length * (masOnly ? 1 : 4)}}
          <v-icon color="blue">mdi-check-bold</v-icon>{{total_2}}/{{filted.length * (masOnly ? 1 : 4)}}
          <v-icon color="purple">mdi-check-bold</v-icon>{{total_4}}/{{filted.length * (masOnly ? 1 : 4)}}
          <v-icon color="orange">mdi-check-bold</v-icon>{{total_8}}/{{filted.length * (masOnly ? 1 : 4)}}
        </div>
        <v-data-table
          :headers="masOnly ? headerMas : headers"
          :items="filted"
          sort-by="mst_pq"
          sort-desc=""
          :mobile-breakpoint="masOnly ? 0 : 600"
        >
          <template #item.bas_pq="{ item }">
            <v-icon color="green" v-if="item.bas_pq & 1">mdi-check-bold</v-icon>
            <v-icon color="blue" v-if="item.bas_pq & 2">mdi-check-bold</v-icon>
            <v-icon color="purple" v-if="item.bas_pq & 4"
              >mdi-check-bold</v-icon
            >
            <v-icon color="orange" v-if="item.bas_pq & 8"
              >mdi-check-bold</v-icon
            >
          </template>
          <template #item.adv_pq="{ item }">
            <v-icon color="green" v-if="item.adv_pq & 1">mdi-check-bold</v-icon>
            <v-icon color="blue" v-if="item.adv_pq & 2">mdi-check-bold</v-icon>
            <v-icon color="purple" v-if="item.adv_pq & 4"
              >mdi-check-bold</v-icon
            >
            <v-icon color="orange" v-if="item.adv_pq & 8"
              >mdi-check-bold</v-icon
            >
          </template>
          <template #item.exp_pq="{ item }">
            <v-icon color="green" v-if="item.exp_pq & 1">mdi-check-bold</v-icon>
            <v-icon color="blue" v-if="item.exp_pq & 2">mdi-check-bold</v-icon>
            <v-icon color="purple" v-if="item.exp_pq & 4"
              >mdi-check-bold</v-icon
            >
            <v-icon color="orange" v-if="item.exp_pq & 8"
              >mdi-check-bold</v-icon
            >
          </template>
          <template #item.mst_pq="{ item }">
            <v-icon color="green" v-if="item.mst_pq & 1">mdi-check-bold</v-icon>
            <v-icon color="blue" v-if="item.mst_pq & 2">mdi-check-bold</v-icon>
            <v-icon color="purple" v-if="item.mst_pq & 4"
              >mdi-check-bold</v-icon
            >
            <v-icon color="orange" v-if="item.mst_pq & 8"
              >mdi-check-bold</v-icon
            >
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  props: {
    music_data: Array,
    records: Array,
  },
  data: () => {
    return {
      visible: false,
      versions: [],
      version: "",
      headers: [
        { text: "曲名", value: "title", width: 250 },
        { text: "Basic", value: "bas_pq" },
        { text: "Advanced", value: "adv_pq" },
        { text: "Expert", value: "exp_pq" },
        { text: "Master", value: "mst_pq" },
      ],
      headerMas: [
        { text: "曲名", value: "title", width: 250 },
        // { text: "Basic", value: "bas_pq"},
        // { text: "Advanced", value: "adv_pq"},
        // { text: "Expert", value: "exp_pq"},
        { text: "Master", value: "mst_pq" },
      ],
      masOnly: true,
    };
  },
  methods: {
    records_filter: function (title, type, diff) {
      let ret = this.records.filter((elem) => {
        return (
          elem.title == title && elem.type == type && elem.level_index == diff
        );
      });
      // console.log(ret)
      return ret;
    },
    sum_pq: function (title, type, diff) {
      let r = this.records_filter(title, type, diff);
      if (r.length == 0) return 0;
      let a = 0;
      if (["fsd", "fsdp"].indexOf(r[0].fs) != -1) a += 4;
      if (["ap", "app"].indexOf(r[0].fc) != -1) a += 8;
      if (r[0].achievements >= 100) a += 2;
      if (["fc", "fcp", "ap", "app"].indexOf(r[0].fc) != -1) a += 1;
      // console.log(a);
      return a;
    },
    init: function () {
      this.versions = Array.from(
        new Set(
          this.music_data.map((elem) => {
            return elem.basic_info.from;
          })
        )
      );
      const l = ["bas_pq", "adv_pq", "exp_pq", "mst_pq"];
      for (let i = 0; i < 4; i++) {
        for (let data of this.music_data) {
          data[l[i]] = this.sum_pq(data.title, data.type, i);
          // console.log(data[l[i]]);
        }
      }
      // console.log(this.available_plates())
      // console.log(this.music_data);
    },
    available_plates: function () {
      // a method called by others.
      // Just verify master level.
      let res = {};
      for (const ver of this.versions) {
        if (ver == "maimai でらっくす PLUS" || ver == "maimai でらっくす Splash")
          continue;
        const d = this.music_data
          .filter((elem) => {
            return elem.basic_info.from == ver;
          })
          .map((elem) => {
            return elem.mst_pq;
          });
        res[ver] = 15;
        for (const v of d) {
          for (const i of [1, 2, 4, 8]) {
            if ((v & i) == 0 && res[ver] & i) res[ver] -= i;
          }
        }
      }
      res["maimai PLUS"] &= res["maimai"];
      if (res["maimai PLUS"] & 2) res["maimai PLUS"] -= 2; // SSS plate not available in maimai PLUS version
      delete res.maimai;
      return res;
    },
  },
  computed: {
    filted: function () {
      return this.music_data.filter((elem) => {
        return elem.basic_info.from == this.version;
      });
    },
    total_8: function () {
      let sum = 0;
      for (const md of this.filted) {
        if (md.mst_pq & 8) sum++;
        if (!this.masOnly) {
          if (md.bas_pq & 8) sum++;
          if (md.adv_pq & 8) sum++;
          if (md.exp_pq & 8) sum++;
        }
      }
      return sum;
    },
    total_4: function () {
      let sum = 0;
      for (const md of this.filted) {
        if (md.mst_pq & 4) sum++;
        if (!this.masOnly) {
          if (md.bas_pq & 4) sum++;
          if (md.adv_pq & 4) sum++;
          if (md.exp_pq & 4) sum++;
        }
      }
      return sum;
    },
    total_2: function () {
      let sum = 0;
      for (const md of this.filted) {
        if (md.mst_pq & 2) sum++;
        if (!this.masOnly) {
          if (md.bas_pq & 2) sum++;
          if (md.adv_pq & 2) sum++;
          if (md.exp_pq & 2) sum++;
        }
      }
      return sum;
    },
    total_1: function () {
      let sum = 0;
      for (const md of this.filted) {
        if (md.mst_pq & 1) sum++;
        if (!this.masOnly) {
          if (md.bas_pq & 1) sum++;
          if (md.adv_pq & 1) sum++;
          if (md.exp_pq & 1) sum++;
        }
      }
      return sum;
    },
  },
};
</script>