<template>
  <v-dialog
    v-model="visible"
    :width="masOnly ? 600 : 1000"
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
          <v-icon color="green">mdi-check-bold</v-icon>{{total_1}}/{{filtered_length}}
          <v-icon color="blue">mdi-check-bold</v-icon>{{total_2}}/{{filtered_length}}
          <v-icon color="purple">mdi-check-bold</v-icon>{{total_4}}/{{filtered_length}}
          <v-icon color="orange">mdi-check-bold</v-icon>{{total_8}}/{{filtered_length}}
        </div>
        <v-data-table
          :headers="masOnly ? headerMas : headers"
          :items="filtered"
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
          <template #item.rem_pq="{ item }">
            <span v-if="item.rem_pq === -1">
              <v-icon color="grey" v-if="item.rem_pq & 1">mdi-close-circle</v-icon>
            </span>
            <span v-else>
              <v-icon color="green" v-if="item.rem_pq & 1">mdi-check-bold</v-icon>
              <v-icon color="blue" v-if="item.rem_pq & 2">mdi-check-bold</v-icon>
              <v-icon color="purple" v-if="item.rem_pq & 4"
                >mdi-check-bold</v-icon
              >
              <v-icon color="orange" v-if="item.rem_pq & 8"
                >mdi-check-bold</v-icon
              >
            </span>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
import Vue from 'vue';
import watchVisible from '../plugins/watchVisible';
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
        { text: "Master", value: "mst_pq" }
      ],
      headerMas: [
        { text: "曲名", value: "title", width: 250 },
        // { text: "Basic", value: "bas_pq"},
        // { text: "Advanced", value: "adv_pq"},
        // { text: "Expert", value: "exp_pq"},
        { text: "Master", value: "mst_pq" }
      ],
      masOnly: true,
    };
  },
  methods: {
    records_filter: function (song_id, diff) {
      let ret = this.records.filter((elem) => {
        return (
          elem.song_id == song_id && elem.level_index == diff
        );
      });
      // console.log(ret)
      return ret;
    },
    sum_pq: function (song_id, diff) {
      let r = this.records_filter(song_id, diff);
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
      this.versions.push('ALL FiNALE');
      (async () => {
        const l = ["bas_pq", "adv_pq", "exp_pq", "mst_pq"];
        for (let i = 0; i < 4; i++) {
          for (let data of this.music_data) {
            data[l[i]] = this.sum_pq(data.id, i);
            // console.log(data[l[i]]);
          }
        }
        for (let data of this.music_data) {
          if (data.level.length == 5) {
            data['rem_pq'] = this.sum_pq(data.id, 4);
          } else {
            data['rem_pq'] = -1;
          }
        }
      })();
      console.log(this.available_plates())
      // console.log(this.music_data);
    },
    filter_version: function(version) {
      if (version == "ALL FiNALE") {
        return this.music_data.filter((elem) => {
          return ["maimai PLUS","maimai GreeN","maimai GreeN PLUS","maimai ORANGE","maimai ORANGE PLUS","maimai PiNK",
          "maimai PiNK PLUS","maimai MURASAKi","maimai MURASAKi PLUS","maimai MiLK","maimai MiLK PLUS","maimai FiNALE"].indexOf(elem.basic_info.from) != -1;
        });
      }
      return this.music_data.filter((elem) => {
        return elem.basic_info.from == version;
      });
    },
    available_plates: function () {
      // a method called by others.
      // Just verify master level.
      let res = {};
      for (const ver of this.versions) {
        if (ver == "maimai でらっくす BUDDiES")
          continue;
        let d = this.filter_version(ver).filter((elem) => elem.title != 'ジングルベル')
          .map((elem) => {
            return elem.mst_pq;
          });
        if (ver == "ALL FiNALE") {
          d = d.concat(this.filter_version(ver).filter((elem) => elem.title != 'ジングルベル')
            .map((elem) => {
              return elem.rem_pq;
            }));
        }
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
      let res2 = []
      for (const key in res) {
        if (key.startsWith('maimai でらっくす')) {
          res2[key + ' PLUS'] = res[key];
        }
      }
      return Object.assign(res2, res);
    },
  },
  watch:{
    visible: watchVisible("visible", "PlateQualifier"),
    version: function (newVal, oldVal) {
      if (newVal == oldVal) return;
      if (newVal == 'ALL FiNALE') {
        this.headers.push({ text: "Re:MASTER", value: "rem_pq" })
        this.headerMas.push({ text: "Re:MASTER", value: "rem_pq" })
      } else if (oldVal == 'ALL FiNALE') {
        Vue.delete(this.headers, 5)
        Vue.delete(this.headerMas, 2)
      }
    },
  },
  computed: {
    filtered_length: function() {
      let len = this.filtered.length * (this.masOnly ? 1 : 4);
      if (this.version == 'ALL FiNALE') {
        for (const data of this.filtered) {
          if (data.level.length == 5) len++;
        }
      }
      return len;
    },
    filtered: function () {
      return this.filter_version(this.version);
    },
    total_8: function () {
      let sum = 0;
      for (const md of this.filtered) {
        if (md.mst_pq & 8) sum++;
        if (!this.masOnly) {
          if (md.bas_pq & 8) sum++;
          if (md.adv_pq & 8) sum++;
          if (md.exp_pq & 8) sum++;
        }
        if (this.version == 'ALL FiNALE' && (md.rem_pq & 8) && md.rem_pq !== -1) sum++;
      }
      return sum;
    },
    total_4: function () {
      let sum = 0;
      for (const md of this.filtered) {
        if (md.mst_pq & 4) sum++;
        if (!this.masOnly) {
          if (md.bas_pq & 4) sum++;
          if (md.adv_pq & 4) sum++;
          if (md.exp_pq & 4) sum++;
        }
        if (this.version == 'ALL FiNALE' && (md.rem_pq & 4) && md.rem_pq !== -1) sum++;
      }
      return sum;
    },
    total_2: function () {
      let sum = 0;
      for (const md of this.filtered) {
        if (md.mst_pq & 2) sum++;
        if (!this.masOnly) {
          if (md.bas_pq & 2) sum++;
          if (md.adv_pq & 2) sum++;
          if (md.exp_pq & 2) sum++;
        }
        if (this.version == 'ALL FiNALE' && (md.rem_pq & 2) && md.rem_pq !== -1) sum++;
      }
      return sum;
    },
    total_1: function () {
      let sum = 0;
      for (const md of this.filtered) {
        if (md.mst_pq & 1) sum++;
        if (!this.masOnly) {
          if (md.bas_pq & 1) sum++;
          if (md.adv_pq & 1) sum++;
          if (md.exp_pq & 1) sum++;
        }
        if (this.version == 'ALL FiNALE' && (md.rem_pq & 1) && md.rem_pq !== -1) sum++;
      }
      return sum;
    },
  },
};
</script>