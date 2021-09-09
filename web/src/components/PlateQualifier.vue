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
          <v-col :cols="4"
            ><v-select v-model="version" :items="versions" label="选择版本"
          /></v-col>
          <v-col :cols="4"
            ><v-select
              v-model="plateType"
              :items="plateTypes"
              label="选择牌子种类"
              item-text="label"
              return-object
          /></v-col>
          <v-col :cols="4"
            ><v-checkbox v-model="masOnly" label="仅查看Master"
          /></v-col>
        </v-row>
        <div>
          <v-btn class="mr-4" color="primary" @click="setPlate">设置牌子</v-btn>
          <v-btn class="mr-4" color="primary" @click="clearPlate"
            >清除牌子</v-btn
          >
          目前牌子：{{ plate }}
        </div>
        <div class="mt-4" v-if="plateType.pq == 15">
          <v-icon color="green">mdi-check-bold</v-icon>=Full Combo
          <v-icon color="blue">mdi-check-bold</v-icon>=SSS
          <v-icon color="purple">mdi-check-bold</v-icon>=Full Sync DX
          <v-icon color="orange">mdi-check-bold</v-icon>=All Perfect
        </div>
        <div class="mt-2" v-if="plateType.pq == 15">
          <v-icon color="green" v-if="plateType.pq & 1">mdi-check-bold</v-icon
          >{{ total_1 }}/{{ filted.length * (masOnly ? 1 : 4) }}
          <v-icon color="blue" v-if="plateType.pq & 2">mdi-check-bold</v-icon
          >{{ total_2 }}/{{ filted.length * (masOnly ? 1 : 4) }}
          <v-icon color="purple" v-if="plateType.pq & 4">mdi-check-bold</v-icon
          >{{ total_4 }}/{{ filted.length * (masOnly ? 1 : 4) }}
          <v-icon color="orange" v-if="plateType.pq & 8">mdi-check-bold</v-icon
          >{{ total_8 }}/{{ filted.length * (masOnly ? 1 : 4) }}
        </div>
        <div class="mt-4" v-else>
          <span v-if="plateType.pq & 1"
            ><v-icon color="green">mdi-check-bold</v-icon>=Full Combo
          </span>
          <span v-if="plateType.pq & 2"
            ><v-icon color="blue" v-if="plateType.pq & 2">mdi-check-bold</v-icon
            >=SSS
          </span>
          <span v-if="plateType.pq & 4"
            ><v-icon color="purple" v-if="plateType.pq & 4"
              >mdi-check-bold</v-icon
            >=Full Sync DX
          </span>
          <span v-if="plateType.pq & 8"
            ><v-icon color="orange" v-if="plateType.pq & 8"
              >mdi-check-bold</v-icon
            >=All Perfect
          </span>
          <span v-if="plateType.pq & 1"
            ><v-icon color="green" v-if="plateType.pq & 1"
              >mdi-check-bold</v-icon
            >{{ total_1 }}/{{ filted.length * (masOnly ? 1 : 4) }}
          </span>
          <span v-if="plateType.pq & 2"
            ><v-icon color="blue" v-if="plateType.pq & 2">mdi-check-bold</v-icon
            >{{ total_2 }}/{{ filted.length * (masOnly ? 1 : 4) }}
          </span>
          <span v-if="plateType.pq & 4"
            ><v-icon color="purple" v-if="plateType.pq & 4"
              >mdi-check-bold</v-icon
            >{{ total_4 }}/{{ filted.length * (masOnly ? 1 : 4) }}
          </span>
          <span v-if="plateType.pq & 8"
            ><v-icon color="orange" v-if="plateType.pq & 8"
              >mdi-check-bold</v-icon
            >{{ total_8 }}/{{ filted.length * (masOnly ? 1 : 4) }}
          </span>
        </div>
        <v-data-table
          :headers="masOnly ? headerMas : headers"
          :items="filted"
          sort-by="mst_pq"
          sort-desc=""
          :mobile-breakpoint="masOnly ? 0 : 600"
        >
          <template #item.bas_pq="{ item }">
            <v-icon color="green" v-if="item.bas_pq & 1 && plateType.pq & 1"
              >mdi-check-bold</v-icon
            >
            <v-icon color="blue" v-if="item.bas_pq & 2 && plateType.pq & 2"
              >mdi-check-bold</v-icon
            >
            <v-icon color="purple" v-if="item.bas_pq & 4 && plateType.pq & 4"
              >mdi-check-bold</v-icon
            >
            <v-icon color="orange" v-if="item.bas_pq & 8 && plateType.pq & 8"
              >mdi-check-bold</v-icon
            >
          </template>
          <template #item.adv_pq="{ item }">
            <v-icon color="green" v-if="item.adv_pq & 1 && plateType.pq & 1"
              >mdi-check-bold</v-icon
            >
            <v-icon color="blue" v-if="item.adv_pq & 2 && plateType.pq & 2"
              >mdi-check-bold</v-icon
            >
            <v-icon color="purple" v-if="item.adv_pq & 4 && plateType.pq & 4"
              >mdi-check-bold</v-icon
            >
            <v-icon color="orange" v-if="item.adv_pq & 8 && plateType.pq & 8"
              >mdi-check-bold</v-icon
            >
          </template>
          <template #item.exp_pq="{ item }">
            <v-icon color="green" v-if="item.exp_pq & 1 && plateType.pq & 1"
              >mdi-check-bold</v-icon
            >
            <v-icon color="blue" v-if="item.exp_pq & 2 && plateType.pq & 2"
              >mdi-check-bold</v-icon
            >
            <v-icon color="purple" v-if="item.exp_pq & 4 && plateType.pq & 4"
              >mdi-check-bold</v-icon
            >
            <v-icon color="orange" v-if="item.exp_pq & 8 && plateType.pq & 8"
              >mdi-check-bold</v-icon
            >
          </template>
          <template #item.mst_pq="{ item }">
            <v-icon color="green" v-if="item.mst_pq & 1 && plateType.pq & 1"
              >mdi-check-bold</v-icon
            >
            <v-icon color="blue" v-if="item.mst_pq & 2 && plateType.pq & 2"
              >mdi-check-bold</v-icon
            >
            <v-icon color="purple" v-if="item.mst_pq & 4 && plateType.pq & 4"
              >mdi-check-bold</v-icon
            >
            <v-icon color="orange" v-if="item.mst_pq & 8 && plateType.pq & 8"
              >mdi-check-bold</v-icon
            >
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
import axios from "axios";
export default {
  props: {
    music_data: Array,
    records: Array,
  },
  data: () => {
    return {
      visible: false,
      versions: [],
      plateTypes: [
        { label: "所有", pq: 15 },
        { label: "极", pq: 1 },
        { label: "将", pq: 2 },
        { label: "舞舞", pq: 4 },
        { label: "神", pq: 8 },
      ],
      version: "",
      plateType: { label: "所有", pq: 15 },
      plate: "无",
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
      // console.log(this.music_data);
    },
    setPlate: function () {
      if (!this.masOnly)
        return this.$message.error(
          '因为本工具只需牌子确认即可领取牌子，请勾选"仅查看Master"'
        );
      if (!this.version) return this.$message.error("请选择想领取的牌子版本");
      if (this.plateType.pq == 15)
        return this.$message.error("请选择想领取的牌子种类");
      if (this.version == "maimai")
        return this.$message.error("无印maimai没有牌子");
      if (this.version == "maimai PLUS" && this.plateType.pq == 2)
        return this.$message.error("maimai PLUS 没有将牌");
      if (this.filted.length != this["total_" + this.plateType.pq])
        return this.$message.error(
          `相应达成数量不足（${this["total_" + this.plateType.pq]}/${
            this.filted.length
          }），也请不要作弊实事求是^^`
        );
      axios
        .post("https://www.diving-fish.com/api/maimaidxprober/player/plate", {
          version: this.version,
          plateType: this.plateType.pq,
        })
        .then((resp) => {
          this.$message.success("牌子修改成功！");
          this.plate = resp.data.plate;
        })
        .catch((err) => {
          this.$message.error(err.response.data.message);
        });
    },
    clearPlate: function () {
      axios
        .post("https://www.diving-fish.com/api/maimaidxprober/player/plate", {
          version: false,
          plateType: false,
        })
        .then((resp) => {
          this.$message.success("牌子清除成功！");
          this.plate = resp.data.plate;
        })
        .catch((err) => {
          this.$message.error(err.response.data.message);
        });
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
  created: function () {
    axios
      .get("https://www.diving-fish.com/api/maimaidxprober/player/plate")
      .then((resp) => {
        this.plate = resp.data.plate || "无";
      })
      .catch(() => {});
  },
};
</script>
