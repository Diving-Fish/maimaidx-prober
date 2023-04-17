<template>
  <div>
    <v-dialog
      width="600px"
      :fullscreen="$vuetify.breakpoint.mobile"
      v-model="snackbar"
    >
      <v-card>
        <div style="display: flex">
          <v-spacer />
          <v-btn icon @click="snackbar = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </div>
        <div
          :style="`width: ${width}px; height: ${width + 150}px; padding: 10px`"
        >
          <div
            :style="`width: ${width - 20}px; height: ${
              $vuetify.breakpoint.mobile ? width + 60 : width - 80
            }px`"
            ref="chart_div"
          ></div>
          <div
            :style="`width: ${width - 20}px; padding-left: 20px`"
            v-if="item"
            class="dialog"
          >
            <p>
              <span>平均达成率：{{ chart_stat.avg.toFixed(2) }}% (</span>
              <span
                :style="
                  chart_stat.avg - diff_stat.achievements >= 0
                    ? 'color: #4CAF50'
                    : 'color: #F44336'
                "
                >{{ chart_stat.avg - diff_stat.achievements >= 0 ? "+" : ""
                }}{{
                  (chart_stat.avg - diff_stat.achievements).toFixed(2)
                }}%</span
              >
              <span>)</span>
              <v-tooltip top>
                <template v-slot:activator="{ on, attrs }">
                  <v-icon v-bind="attrs" v-on="on" color="grey lighten-1"
                    >mdi-help-circle</v-icon
                  >
                </template>
                <span
                  >括号内为此谱面与难度为 {{ item.level}} 的谱面达成率平均值的差</span
                >
              </v-tooltip>
            </p>
            <p>平均 DX 分数：{{ chart_stat.avg_dx.toFixed(1) }}</p>
            <p>
              谱面成绩标准差：
              <span v-if="chart_stat.std_dev < 3.6">正常</span>
              <span v-else-if="chart_stat.std_dev < 4.2" style="color: #ffc107"
                >较高</span
              >
              <span v-else-if="chart_stat.std_dev < 4.8" style="color: #ff9800"
                >高</span
              >
              <span v-else style="color: #f44336">极高</span>
              <span> ({{ chart_stat.std_dev.toFixed(2) }})</span>
              <v-tooltip top>
                <template v-slot:activator="{ on, attrs }">
                  <v-icon v-bind="attrs" v-on="on" color="grey lighten-1"
                    >mdi-help-circle</v-icon
                  >
                </template>
                <span
                  >标准差越大，成绩分布越分散，可能说明是个人差曲或者越级较多（只统计距离平均成绩差距低于
                  10% 的成绩）</span
                >
              </v-tooltip>
            </p>
          </div>
        </div>
      </v-card>
    </v-dialog>
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
      <template #item.cover="{ item }">
        <v-img
          :src="`https://www.diving-fish.com/covers/${getCoverPathById(
            item.song_id
          )}`"
          width="72px"
          class="rounded"
          contain
        ></v-img>
      </template>
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
            Charter:
            {{ music_data_dict[item.song_id].charts[item.level_index].charter }}
            <br />
            Tap:
            {{
              music_data_dict[item.song_id].charts[item.level_index].notes[0]
            }}
            <br />
            Hold:
            {{
              music_data_dict[item.song_id].charts[item.level_index].notes[1]
            }}
            <br />
            Slide:
            {{
              music_data_dict[item.song_id].charts[item.level_index].notes[2]
            }}
            <br />
            <span v-if="music_data_dict[item.song_id].type == 'DX'">
              Touch:
              {{
                music_data_dict[item.song_id].charts[item.level_index].notes[3]
              }}
              <br />
              Break:
              {{
                music_data_dict[item.song_id].charts[item.level_index].notes[4]
              }}
              <br />
            </span>
            <span v-else>
              Break:
              {{
                music_data_dict[item.song_id].charts[item.level_index].notes[3]
              }}
              <br />
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
            {{ j.ra }}(+{{ j.ra - item.ra }})：{{
              j.achievements.toFixed(4)
            }}(+{{ (j.achievements - item.achievements).toFixed(4) }})<br />
          </span>
        </v-tooltip>
      </template>
      <template #item.fit_diff="{ item }">
        <v-tooltip top>
          <template v-slot:activator="{ on, attrs }">
            <span
              v-bind="attrs"
              v-on="on"
              style="cursor: pointer"
              @click="showChart(item)"
              >{{ item.fit_diff.toFixed(2) }}</span
            >
          </template>
          点击以查看该谱面的统计信息
        </v-tooltip>
      </template>
      <template #header.fit_diff="">
        拟合难度
        <!-- <v-tooltip top>
        <template v-slot:activator="{ on, attrs }">
          <v-icon v-bind="attrs" v-on="on">
            mdi-information-outline
          </v-icon>
        </template>
        <span>相对难度是指某一张谱面的 SSS 比例在同等级谱面中的排名</span>
      </v-tooltip> -->
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
            <v-icon v-bind="attrs" v-on="on" @click="cover(item)"
              >mdi-image-outline</v-icon
            >
          </template>
          查看封面
        </v-tooltip>
        <v-tooltip top>
          <template v-slot:activator="{ on, attrs }">
            <v-icon v-bind="attrs" v-on="on" @click="modify(item)"
              >mdi-pencil-box-outline</v-icon
            >
          </template>
          编辑分数
        </v-tooltip>
        <v-tooltip top>
          <template v-slot:activator="{ on, attrs }">
            <v-icon v-bind="attrs" v-on="on" @click="calculator(item)"
              >mdi-calculator-variant-outline</v-icon
            >
          </template>
          填入计算器
        </v-tooltip>
      </template>
    </v-data-table>
  </div>
</template>

<script>
export default {
  props: {
    items: Array,
    search: String,
    loading: Boolean,
    limit: Number,
    chart_stats: Object,
    headers: Array,
    music_data_dict: Object,
  },
  data: () => {
    return {
      chart: null,
      snackbar: false,
      width: 600,
      height: 720,
      item: null,
      chart_stat: null,
      diff_stat: null,
    };
  },
  created: function () {
    if (this.$vuetify.breakpoint.mobile) {
      this.width = screen.width;
      this.height = screen.height;
    }
  },
  watch: {
    search(n) {
      this.search = n;
    },
  },
  methods: {
    getCoverPathById: function (songId) {
      let i = parseInt(songId);
      if (i > 10000) i -= 10000;
      return (i + "").padStart(4, "0") + ".png";
    },
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
      return {
        value: this.chart_stats.charts[item.song_id][item.level_index].fit_diff,
      };
    },
    showChart(item) {
      this.item = item;
      this.chart_stat = this.chart_stats.charts[item.song_id][item.level_index];
      this.diff_stat = this.chart_stats.diff_data[item.level];
      const ach_name_map = [
        "D",
        "C",
        "B",
        "BB",
        "BBB",
        "A",
        "AA",
        "AAA",
        "S",
        "S+",
        "SS",
        "SS+",
        "SSS",
        "SSS+",
      ];
      const fc_name_map = ["Not FC", "FC", "FC+", "AP", "AP+"];
      const ach_data = () => {
        let data = [];
        for (let i = 0; i < 14; i++) {
          data.push({
            value: this.chart_stat.dist[i] / this.chart_stat.cnt,
            name: ach_name_map[i],
          });
        }
        return data;
      };
      const fc_data = () => {
        let data = [];
        for (let i = 0; i < 5; i++) {
          data.push({
            value: this.chart_stat.fc_dist[i] / this.chart_stat.cnt,
            name: fc_name_map[i],
          });
        }
        return data;
      };
      this.snackbar = true;
      let option = {
        title: {
          text: `${item.title} ${item.type} ${item.level_label}`,
          left: "center",
        },
        tooltip: {
          trigger: "item",
        },
        legend: {
          orient: "horizontal",
          bottom: 20,
        },
        series: [
          {
            name: "达成率等级",
            type: "pie",
            radius: "40%",
            data: ach_data(),
            top: "-10%",
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: "rgba(0, 0, 0, 0.5)",
              },
            },
            labelLine: {
              normal: {
                length: 60,
              },
            },
            itemStyle: {
              normal: {
                color: function (colors) {
                  var colorList = [
                    "#B0BEC5",
                    "#90A4AE",
                    "#607D8B",
                    "#546E7A",
                    "#455A64",
                    "#FF8A65",
                    "#FF5722",
                    "#E64A19",
                    "#FFD54F",
                    "#FFA000",
                    "#4DB6AC",
                    "#00796B",
                    "#64B5F6",
                    "#1976D2",
                  ];
                  return colorList[colors.dataIndex];
                },
              },
            },
            tooltip: {
              trigger: "item",
              formatter: (params) => {
                const diff =
                  Math.round(
                    (params.value - this.diff_stat.dist[params.dataIndex]) *
                      10000
                  ) / 100;
                return `${params.seriesName} <br /> <b>${
                  params.data.name
                }</b> ${(params.value * 100).toFixed(2)}% 
                 (<span style="${
                   diff >= 0 ? "color: #4CAF50" : "color: #F44336"
                 }">${diff >= 0 ? "+" : ""}${diff}%</span>)
                 <br />同难度平均值：${
                   Math.round(this.diff_stat.dist[params.dataIndex] * 10000) /
                   100
                 }% <br />`;
              },
            },
          },
          {
            name: "全连等级",
            type: "pie",
            radius: ["40%", "50%"],
            data: fc_data(),
            top: "-10%",
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: "rgba(0, 0, 0, 0.5)",
              },
            },
            itemStyle: {
              normal: {
                color: function (colors) {
                  var colorList = [
                    "#607D8B",
                    "#4CAF50",
                    "#43A047",
                    "#FF9800",
                    "#FB8C00",
                  ];
                  return colorList[colors.dataIndex];
                },
              },
            },
            tooltip: {
              trigger: "item",
              formatter: (params) => {
                const diff =
                  (params.value - this.diff_stat.fc_dist[params.dataIndex]) *
                  100;
                return `${params.seriesName} <br /> <b>${
                  params.data.name
                }</b> ${(params.value * 100).toFixed(2)}% 
                 (<span style="${
                   diff >= 0 ? "color: #4CAF50" : "color: #F44336"
                 }">${diff >= 0 ? "+" : ""}${diff.toFixed(2)}%</span>)
                 <br />同难度平均值：${
                   Math.round(
                     this.diff_stat.fc_dist[params.dataIndex] * 10000
                   ) / 100
                 }% <br />`;
              },
            },
          },
        ],
      };
      if (this.chart === null) {
        let that = this;
        setTimeout(() => {
          that.chart = this.$echarts.init(this.$refs.chart_div);
          that.chart.setOption(option);
        }, 100);
      } else {
        this.chart.setOption(option);
      }
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
          "^" +
            this.music_data_dict[item.song_id].charts[item.level_index]
              .charter +
            "$",
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

<style scoped>
.dialog p {
  margin-bottom: 8px;
  font-size: 15px;
}
</style>