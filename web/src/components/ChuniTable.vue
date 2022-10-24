<template>
  <v-data-table :items-per-page="40" :footer-props="{ 'items-per-page-options': [40, -1] }" :headers="headers"
    :loading="loading" :items="items" :search="search" sort-by="rank" no-data-text="没有数据" loading-text="加载中……"
    no-results-text="没有符合条件的条目">
    <template #item.rank="{ item }">
      <span v-if="item.rank < 0" style="color: #00BCD4">R{{ item.rank + 11 }}</span>
      <span v-else>{{ item.rank }}</span>
    </template>
    <template #item.title="{ item }">
      <v-tooltip top :disabled="!music_data_dict[item.mid]">
        <template v-slot:activator="{ on, attrs }">
          <span v-bind="attrs" v-on="on">
            {{ item.title }}
            <v-chip v-if="item.fc" :color="getFC(item.fc)" dark>{{
                getName(item.fc)
            }}</v-chip>
          </span>
        </template>
        <span v-if="music_data_dict[item.mid]">
          id: {{ music_data_dict[item.mid].id }} <br />
          Artist: {{ music_data_dict[item.mid].basic_info.artist }} <br />
          Version: {{ music_data_dict[item.mid].basic_info.from }} <br />
          Genre: {{ music_data_dict[item.mid].basic_info.genre }} <br />
          BPM: {{ music_data_dict[item.mid].basic_info.bpm }} <br />
        </span>
      </v-tooltip>
    </template>
    <template #item.level="{ item }">
      <v-tooltip top :disabled="!music_data_dict[item.mid]">
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
        <span v-if="music_data_dict[item.mid]">
          Charter: {{ music_data_dict[item.mid].charts[item.level_index].charter }} <br />
          Combo: {{ music_data_dict[item.mid].charts[item.level_index].combo }} <br />
        </span>
      </v-tooltip>
    </template>
    <template #item.score="{ item }">
      {{ item.score }}
      <v-chip :color="getRateColor(getRate(item.score))" outlined class="ml-1">{{
        getRate(item.score).toUpperCase()
      }}</v-chip>
    </template>
  </v-data-table>
</template>
  
<script>

export default {
  props: {
    items: Array,
    search: String,
    loading: Boolean,
    music_data_dict: Object,
  },
  data: () => {
    return {
      headers: [
        { text: '排名', value: 'rank' },
        { text: '乐曲名', value: 'title' },
        { text: '难度', value: 'level' },
        { text: '定数', value: 'ds' },
        { text: '分数', value: 'score' },
        { text: 'Rating', value: 'ra' },
      ]
    };
  },
  watch: {
    search(n) {
      this.search = n;
    },
  },
  methods: {
    getLevel(index) {
      return ["#22bb5b", "#fb9c2d", "#f64861", "#9e45e2", "#1B1B1B", "cyan"][index];
    },
    getFC(str) {
      if (str.startsWith("fullcombo")) return "green";
      return "orange";
    },
    getFS(str) {
      if (str.startsWith("fsd")) return "orange";
      return "blue";
    },
    getName(str) {
      const map = {
        fullcombo: "FC",
        alljustice: "AJ",
      };
      return map[str];
    },
    getRateColor(str) {
      if (str.startsWith("sss")) return "red";
      if (str.startsWith("ss")) return "blue darken-1";
      if (str.startsWith("s")) return "amber darken-2";
      return "";
    },
    getRate(val) {
      if (val < 500000) {
        return 'd'
      } else if (val < 800000) {
        return 'c'
      } else if (val < 900000) {
        return 'b'
      } else if (val < 925000) {
        return 'a'
      } else if (val < 950000) {
        return 'aa'
      } else if (val < 975000) {
        return 'aaa'
      } else if (val < 1000000) {
        return 's'
      } else if (val < 1007500) {
        return 'ss'
      } else if (val < 1009000) {
        return 'sss'
      } else {
        return 'sss+'
      }
    },
    getTag(item) {
      // console.log(this.chart_stats)
      if (!this.chart_stats[item.mid]) {
        return {
          exists: false,
          value: "Data Not Enough",
          color: "grey",
        };
      }
      let elem = this.chart_stats[item.mid][item.level_index];
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
          "^" + this.music_data_dict[item.mid].id + "$",
          "id" + this.music_data_dict[item.mid].id + "$",
          "^" + this.music_data_dict[item.mid].basic_info.artist + "$",
          "bpm" + this.music_data_dict[item.mid].basic_info.bpm + "$",
          "^" + this.music_data_dict[item.mid].basic_info.bpm + "$",
          "^" + this.music_data_dict[item.mid].charts[item.level_index].charter + "$",
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
  