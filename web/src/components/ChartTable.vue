<template>
  <v-data-table
    :items-per-page="limit"
    :footer-props="{ 'items-per-page-options': [limit, -1] }"
    :headers="headers"
    :loading="loading"
    :items="items"
    :search="search"
    sort-by="rank"
    :custom-filter="chartFilter"
    no-data-text="没有数据"
    loading-text="加载中……"
    no-results-text="没有符合条件的条目"
  >
    <template #item.title="{ item }">
      <v-tooltip top :disabled="!music_data_dict[item.song_id]">
        <template v-slot:activator="{ on, attrs }">
          <span v-bind="attrs" v-on="on">
            <a
              v-if="item.type == 'DX'"
              dark
              color="blue"
              style="cursor: default"
              >DX</a
            >
      {{ item.title }}
      <v-chip v-if="item.fc" :color="getFC(item.fc)" dark>{{
        getName(item.fc)
      }}</v-chip>
      <v-chip v-if="item.fs" :color="getFS(item.fs)" dark>{{
        getName(item.fs)
      }}</v-chip>
          </span>
        </template>
        <span v-if="music_data_dict[item.song_id]">
          id: {{ music_data_dict[item.song_id].id }} <br />
          Artist: {{ music_data_dict[item.song_id].basic_info.artist }} <br />
          Version: {{ music_data_dict[item.song_id].basic_info.from }} <br />
          Genre: {{ music_data_dict[item.song_id].basic_info.genre }} <br />
          BPM: {{ music_data_dict[item.song_id].basic_info.bpm }} <br />
        </span>
      </v-tooltip>
    </template>
    <template #item.level="{ item }">
      <v-tooltip top :disabled="!music_data_dict[item.song_id]">
        <template v-slot:activator="{ on, attrs }">
          <v-chip
            v-bind="attrs"
            v-on="on"
            :color="getLevel(item.level_index)"
            dark
          >
        {{ item.level_label }} {{ item.level }}
      </v-chip>
        </template>
        <span v-if="music_data_dict[item.song_id]">
          Charter: {{ music_data_dict[item.song_id].charts[item.level_index].charter }} <br />
          Tap: {{ music_data_dict[item.song_id].charts[item.level_index].notes[0] }} <br />
          Hold: {{ music_data_dict[item.song_id].charts[item.level_index].notes[1] }} <br />
          Slide: {{ music_data_dict[item.song_id].charts[item.level_index].notes[2] }} <br />
          <span v-if="music_data_dict[item.song_id].type=='DX'">
            Touch: {{ music_data_dict[item.song_id].charts[item.level_index].notes[3] }} <br />
            Break: {{ music_data_dict[item.song_id].charts[item.level_index].notes[4] }} <br />
          </span>
          <span v-else>
            Break: {{ music_data_dict[item.song_id].charts[item.level_index].notes[3] }} <br />
          </span>
        </span>
      </v-tooltip>
    </template>
    <template #item.achievements="{ item }">
      {{ item.achievements.toFixed(4) }}%
      <v-chip :color="getRate(item.rate)" outlined class="ml-1">{{
        item.rate.replace("p", "+").toUpperCase()
      }}</v-chip>
    </template>
    <template #item.ra="{ item }">
      <v-tooltip top>
        <template v-slot:activator="{ on, attrs }">
          <span
            style="color: #4caf50"
            v-if="item.rank <= limit"
            v-bind="attrs"
            v-on="on"
            >{{ item.ra }}</span
          >
          <span v-else v-bind="attrs" v-on="on">{{ item.ra }}</span>
        </template>
        <span v-if="!getMoreRa(item).length">已达成本曲最高DX rating。</span>
        <span v-else v-for="(j, key) in getMoreRa(item)" :key="key">
          {{ j.ra }}(+{{ j.ra - item.ra }})：{{ j.achievements.toFixed(4) }}(+{{
            (j.achievements - item.achievements).toFixed(4)
          }})<br />
        </span>
      </v-tooltip>
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
      <v-tooltip top v-if="item.dxScore">
        <template v-slot:activator="{ on, attrs }">
          <span v-bind="attrs" v-on="on"
            >{{ item.dxScore_perc.toFixed(2) }}%
          <v-chip
            v-if="item.dxScore_perc >= 85"
            :color="getDXScore(item).color"
            outlined
            class="ml-1"
            >☆{{ getDXScore(item).star }}</v-chip
            ></span
          >
        </template>
        DX分数比例为 {{ item.dxScore }}/{{ getDXScore(item).total }}<br />
        <span v-if="item.dxScore_perc < 97">
          距离下一个星级（☆{{ getDXScore(item).star + 1 }}，{{
            getDXScore(item).next
          }}）还差{{ getDXScore(item).next - item.dxScore }}分</span
        >
      </v-tooltip>
      <span v-else> {{ item.dxScore_perc.toFixed(2) }}% </span>
    </template>
    <template #item.actions="{ item }">
      <v-tooltip top>
        <template v-slot:activator="{ on, attrs }">
          <v-icon v-bind="attrs" v-on="on" @click="cover(item)">mdi-image-outline</v-icon>
        </template>
        查看封面
      </v-tooltip>
      <v-tooltip top>
        <template v-slot:activator="{ on, attrs }">
          <v-icon v-bind="attrs" v-on="on" @click="modify(item)">mdi-pencil-box-outline</v-icon>
        </template>
        编辑分数
      </v-tooltip>
      <v-tooltip top>
        <template v-slot:activator="{ on, attrs }">
          <v-icon v-bind="attrs" v-on="on" @click="calculator(item)">mdi-calculator-variant-outline</v-icon>
        </template>
        填入计算器
      </v-tooltip>
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
    headers: Array,
    music_data_dict: Object,
  },
  data: () => {
    return {};
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
      if (!this.$store.state.chart_stats[item.song_id]) {
        return {
          exists: false,
          value: "Data Not Enough",
          color: "grey",
        };
      }
      let elem = this.$store.state.chart_stats[item.song_id][item.level_index];
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
    get_idx(ach) {
      return [
        50, 60, 70, 75, 80, 90, 94, 97, 98, 99, 99.5, 100, 100.5, 200,
      ].findIndex((i) => ach < i);
    },
    get_l(idx) {
      return [0, 5, 6, 7, 7.5, 8.5, 9.5, 10.5, 12.5, 12.7, 13, 13.2, 13.5, 14][
        idx
      ];
    },
    get_min_ach(idx) {
      return [0, 50, 60, 70, 75, 80, 90, 94, 97, 98, 99, 99.5, 100, 100.5, 101][
        idx
      ];
    },
    get_ra(ds, ach) {
      return Math.floor(
        (ds * this.get_l(this.get_idx(ach)) * Math.min(100.5, ach)) / 100
      );
    },
    getMoreRa(item) {
      let ds = item.ds;
      let idx = this.get_idx(item.achievements);
      let ach4 = Math.round(item.achievements * 10000);
      let min_idx = Math.max(idx, 7);
      let min_ach4 = Math.round(this.get_min_ach(min_idx) * 10000);
      let max_idx = Math.min(min_idx + 3, 13);
      let max_ach4 = Math.round(this.get_min_ach(max_idx + 1) * 10000);
      let more_ra = [];
      for (let curr_ach4 = min_ach4; curr_ach4 < max_ach4; curr_ach4 += 2500) {
        // console.log(curr_ach4, JSON.stringify(more_ra));
        let curr_min_ra = this.get_ra(ds, curr_ach4 / 10000);
        if (curr_min_ra > this.get_ra(ds, (curr_ach4 - 1) / 10000)) {
          if (curr_ach4 > ach4)
            more_ra.push({
              ra: curr_min_ra,
              achievements: curr_ach4 / 10000,
            });
        }
        let curr_max_ra = this.get_ra(ds, (curr_ach4 + 2499) / 10000);
        if (curr_max_ra > curr_min_ra) {
          let l = curr_ach4,
            r = curr_ach4 + 2499,
            ans = r;
          while (r >= l) {
            let mid = Math.floor((r + l) / 2);
            if (this.get_ra(ds, mid / 10000) > curr_min_ra) {
              ans = mid;
              r = mid - 1;
            } else {
              l = mid + 1;
            }
          }
            if (curr_ach4 > ach4)
              more_ra.push({
                ra: curr_max_ra,
                achievements: ans / 10000,
              });
        }
      }
      return more_ra;
    },
    modify(item) {
      if (item.block) {
        this.$message.error("您无法修改此谱面的完成率");
        return;
      }
      this.$emit("edit", item);
    },
    cover(item) {
      this.$emit("cover", item);
    },
    calculator(item) {
      this.$emit("calculator", item);
    },
    chartFilter(value, search, item) {
      if (!item.search_index)
        item.search_index = [
          "^" + item.title + "$",
          "^" + this.music_data_dict[item.song_id].id + "$",
          "id" + this.music_data_dict[item.song_id].id + "$",
          "^" + this.music_data_dict[item.song_id].basic_info.artist + "$",
          "bpm" + this.music_data_dict[item.song_id].basic_info.bpm + "$",
          "^" + this.music_data_dict[item.song_id].basic_info.bpm + "$",
          "^" + this.music_data_dict[item.song_id].charts[item.level_index].charter + "$",
          "^" + item.ra + "$",
          "^" + item.ds + "$",
        ].map((info) => info.toLocaleLowerCase());
      return (
        search != null &&
        item.search_index.some(
          (info) => info.indexOf(search.toLocaleLowerCase()) !== -1
        )
      );
    },
  },
};
</script>
