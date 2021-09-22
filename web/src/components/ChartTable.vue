<template>
  <v-data-table
    :items-per-page="limit"
    :footer-props="{ 'items-per-page-options': [limit, -1] }"
    :headers="headers"
    :loading="loading"
    :items="items"
    :search="search"
    sort-by="rank"
  >
    <template #item.title="{ item }">
      <a v-if="item.type == 'DX'" dark color="blue" style="cursor: default">DX</a>
      {{ item.title }}
      <v-chip v-if="item.fc" :color="getFC(item.fc)" dark>{{
        getName(item.fc)
      }}</v-chip>
      <v-chip v-if="item.fs" :color="getFS(item.fs)" dark>{{
        getName(item.fs)
      }}</v-chip>
    </template>
    <template #item.level="{ item }">
      <v-chip :color="getLevel(item.level_index)" dark>
        {{ item.level_label }} {{ item.level }}
      </v-chip>
    </template>
    <template #item.achievements="{ item }">
      {{ item.achievements.toFixed(4) }}%
      <v-chip :color="getRate(item.rate)" outlined class="ml-1">{{
        item.rate.replace("p", "+").toUpperCase()
      }}</v-chip>
    </template>
    <template #item.ra="{ item }">
      <span style="color: #4caf50" v-if="item.rank <= limit">{{
        item.ra
      }}</span>
      <span v-else>{{ item.ra }}</span>
    </template>
    <template #item.tag="{ item }">
      <v-tooltip top v-if="getTag(item).exists">
        <template v-slot:activator="{ on, attrs }">
          <v-chip :color="getTag(item).color" v-bind="attrs" v-on="on">{{
            getTag(item).value
          }}</v-chip>
        </template>
        在有数据的同难度歌曲中，<br />
        这首歌曲的 SSS 比例排名为 {{ getTag(item).rank_text }}<br />
        SSS 人数为：{{ getTag(item).rate_text }}({{
          getTag(item).rate
        }}%)<br />
        平均达成率为：{{ getTag(item).ac }}%
      </v-tooltip>
      <v-tooltip top v-else>
        <template v-slot:activator="{ on, attrs }">
          <v-chip :color="getTag(item).color" v-bind="attrs" v-on="on">{{
            getTag(item).value
          }}</v-chip>
        </template>
        数据太少啦……多拉点人用查分器如何？
      </v-tooltip>
    </template>
    <template #header.tag="">
      相对难度
      <v-tooltip top>
        <template v-slot:activator="{ on, attrs }">
          <v-icon v-bind="attrs" v-on="on">
            mdi-information-outline
          </v-icon>
        </template>
        <span>相对难度是指某一张谱面的 SSS 比例在同等级谱面中的排名</span>
      </v-tooltip>
    </template>
    <template #item.dxScore="{ item }">
      {{ item.dxScore }}
    </template>
    <template #item.dxScore_perc="{ item }">
      <v-tooltip top>
        <template v-slot:activator="{ on, attrs }">
          <span  v-bind="attrs" v-on="on">{{ item.dxScore_perc.toFixed(2) }}%
          <v-chip
            v-if="item.dxScore_perc >= 85"
            :color="getDXScore(item).color"
            outlined
            class="ml-1"
            >☆{{ getDXScore(item).star }}</v-chip
          ></span>
        </template>
        DX分数比例为 {{ item.dxScore }}/{{ getDXScore(item).total }}<br/>
        <span v-if="item.dxScore_perc < 97">
          距离下一个星级（☆{{ getDXScore(item).star + 1 }}，{{getDXScore(item).next}}）还差{{
            getDXScore(item).next-item.dxScore
          }}分</span
        >
      </v-tooltip>
    </template>
    <template #item.actions="{ item }">
      <v-icon small @click="modify(item)">mdi-pencil</v-icon>
    </template>
  </v-data-table>
</template>

<script>
export default {
  props: {
    items: Array,
    search: String,
    loading: Boolean,
    limit: Number,
    chart_stats: Object,
  },
  data: () => {
    return {
      headers: [
        { text: "排名", value: "rank" },
        { text: "乐曲名", value: "title" },
        { text: "难度", value: "level", sortable: false },
        { text: "定数", value: "ds" },
        { text: "达成率", value: "achievements" },
        { text: "DX Rating", value: "ra" },
        { text: "相对难度", value: "tag" },
        { text: "编辑", value: "actions", sortable: false },
      ],
    };
  },
  watch: {
    search(n) {
      this.search = n;
    },
  },
  methods: {
    getLevel(index) {
      return ["#22bb5b", "#fb9c2d", "#f64861", "#9e45e2", "#ba67f8"][index];
    },
    getFC(str) {
      if (str.startsWith("fc")) return "green";
      return "orange";
    },
    getFS(str) {
      if (str.startsWith("fsd")) return "orange";
      return "blue";
    },
    getName(str) {
      const map = {
        fc: "FC",
        fcp: "FC+",
        fs: "FS",
        fsp: "FS+",
        fsd: "FSDX",
        fsdp: "FSDX+",
        ap: "AP",
        app: "AP+",
      };
      return map[str];
    },
    getRate(str) {
      if (str.startsWith("sssp")) return "red";
      if (str.startsWith("sss")) return "blue darken-1";
      if (str.startsWith("ssp")) return "amber darken-2";
      return "";
    },
    getTag(item) {
      // console.log(this.chart_stats)
      if (!this.chart_stats[item.song_id]) {
        return {
          exists: false,
          value: "Data Not Enough",
          color: "grey",
        };
      }
      let elem = this.chart_stats[item.song_id][item.level_index];
      let tag = elem.tag;
      let color = "";
      if (tag == undefined) {
        tag = "Data Not Enough";
        color = "grey";
      }
      let color_dict = {
        "Very Easy": "green",
        Easy: "light-green",
        Medium: "blue",
        Hard: "deep-orange",
        "Very Hard": "red",
      };
      color = color_dict[tag];
      return {
        exists: elem.v != undefined,
        value: tag,
        color: color,
        rank_text: elem.v + 1 + "/" + elem.t,
        ac: elem.avg ? elem.avg.toFixed(2) : "0.00",
        rate_text: elem.sssp_count + "/" + elem.count,
        rate: ((elem.sssp_count * 100) / elem.count).toFixed(2),
      };
    },
    getDXScore(item) {
      let star =
        5 - [97, 95, 93, 90, 85, 0].findIndex((v) => item.dxScore_perc >= v);
      let color = "";
      if (star >= 5) color = "yellow";
      else if (star >= 3) color = "orange";
      else if (star >= 1) color = "green";
      let total = Math.round((item.dxScore / item.dxScore_perc) * 100);
      let next = Math.ceil(([85, 90, 93, 95, 97, 100][star] * total) / 100);
      return {
        star: star,
        color: color,
        total: total,
        next: next,
      };
    },
    modify(item) {
      if (item.block) {
        this.$message.error("您无法修改此谱面的完成率");
        return;
      }
      this.$emit("edit", item);
    },
  },
};
</script>
