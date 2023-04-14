<template>
  <v-sheet style="display: box; margin: 0px 16px">
    <v-row dense>
      <v-col cols="4" class="px-0 py-0">
        <v-subheader>
          连击筛选
          <v-icon
            @click="
              fc_filter.length === fc_filter_items.length
                ? (fc_filter = [])
                : (fc_filter = fc_filter_items.map((i) => i.value))
            "
            class="ml-2"
          >
            mdi-check-all
          </v-icon></v-subheader
        >
      </v-col>
      <v-col cols="8" class="px-0 py-0">
        <v-slide-group
          multiple
          v-model="fc_filter"
          class="ml-2 py-2"
          show-arrows
        >
          <v-slide-item
            v-for="(item, key) in fc_filter_items"
            :key="key"
            :value="item.value"
            class="mr-2"
            v-slot="{ active, toggle }"
          >
            <v-chip
              :color="getFC(item.value)"
              :outlined="!active"
              dark
              @click="toggle"
            >
              {{ item.text }}
            </v-chip>
          </v-slide-item>
        </v-slide-group>
      </v-col>
    </v-row>
    <v-row dense>
      <v-col cols="4" class="px-0 py-0">
        <v-subheader>
          同步率筛选
          <v-icon
            @click="
              fs_filter.length === fs_filter_items.length
                ? (fs_filter = [])
                : (fs_filter = fs_filter_items.map((i) => i.value))
            "
            class="ml-2"
          >
            mdi-check-all
          </v-icon></v-subheader
        >
      </v-col>
      <v-col cols="8" class="px-0 py-0">
        <v-slide-group
          multiple
          v-model="fs_filter"
          class="ml-2 py-2"
          show-arrows
        >
          <v-slide-item
            v-for="(item, key) in fs_filter_items"
            :key="key"
            :value="item.value"
            class="mr-2"
            v-slot="{ active, toggle }"
          >
            <v-chip
              :color="getFS(item.value)"
              :outlined="!active"
              dark
              @click="toggle"
            >
              {{ item.text }}
            </v-chip>
          </v-slide-item>
        </v-slide-group>
      </v-col>
    </v-row>
    <v-row dense>
      <v-col cols="4" class="px-0 py-0">
        <v-subheader>
          难度筛选
          <v-icon
            @click="
              diff_filter.length === diff_filter_items.length
                ? (diff_filter = [])
                : (diff_filter = diff_filter_items.map((i) => i.value))
            "
            class="ml-2"
          >
            mdi-check-all
          </v-icon></v-subheader
        >
      </v-col>
      <v-col cols="8" class="px-0 py-0">
        <v-slide-group
          multiple
          v-model="diff_filter"
          class="ml-2 py-2"
          show-arrows
        >
          <v-slide-item
            v-for="(item, key) in diff_filter_items"
            :key="key"
            :value="item.value"
            class="mr-2"
            v-slot="{ active, toggle }"
          >
            <v-chip
              :color="getLevel(item.value)"
              :outlined="!active"
              dark
              @click="toggle"
            >
              {{ item.text }}
            </v-chip>
          </v-slide-item>
        </v-slide-group>
      </v-col>
    </v-row>
    <v-row dense>
      <v-col cols="4" class="px-0 py-0">
        <v-subheader>
          达成率筛选
          <v-icon
            @click="
              rate_filter.length === rate_filter_items.length
                ? (rate_filter = [])
                : (rate_filter = rate_filter_items.map((i) => i.value))
            "
            class="ml-2"
          >
            mdi-check-all
          </v-icon></v-subheader
        >
      </v-col>
      <v-col cols="8" class="px-0 py-0">
        <v-slide-group
          multiple
          v-model="rate_filter"
          class="ml-2 py-2"
          show-arrows
        >
          <v-slide-item
            v-for="(item, key) in rate_filter_items"
            :key="key"
            :value="item.value"
            class="mr-2"
            v-slot="{ active, toggle }"
          >
            <v-chip
              :color="getRate(item.value)"
              :outlined="!active"
              dark
              @click="toggle"
            >
              {{ item.text }}
            </v-chip>
          </v-slide-item>
        </v-slide-group>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="6">
        <v-select
          v-model="version"
          :items="versions"
          label="版本"
          clearable
          hide-details
        />
      </v-col>
      <v-col cols="6">
        <v-select
          v-model="genre"
          :items="genres"
          label="歌曲类别"
          clearable
          hide-details
        />
      </v-col>
    </v-row>
    <v-row align="center">
      <v-col cols="7">
        <v-select
          v-model="headers"
          :items="headers_items"
          label="选择分数表列"
          multiple
          @change="setHeaders"
          return-object
          hide-details
        >
          <template v-slot:prepend>
            <v-tooltip bottom>
              <template v-slot:activator="{ on, attrs }">
            <v-icon
              @click="(headers = headers_default), setHeaders()"
              :disabled="headers == headers_default"
                  v-bind="attrs"
                  v-on="on"
            >
              mdi-refresh
            </v-icon>
          </template>
              恢复默认表列
            </v-tooltip>
          </template>
          <template v-slot:append-outer>
            <v-tooltip bottom>
              <template v-slot:activator="{ on, attrs }">
                <v-icon
                  @click="setHeadersDefault(headers)"
                  :disabled="headers == headers_default"
                  color="orange"
                  v-bind="attrs"
                  v-on="on"
                >
                  mdi-content-save
                </v-icon>
              </template>
              保存为默认表列
            </v-tooltip>
          </template>
          <template v-slot:selection="{ index }">
            <span v-if="index == 0">{{ headers.length }}个列已选</span>
          </template>
        </v-select>
      </v-col>
      <v-col cols="5" class="px-0 py-0">
        <v-checkbox
          label="使用暗色主题"
          v-model="darkTheme"
          hide-details
          @change="toggleDarkTheme"
        ></v-checkbox>
      </v-col>
    </v-row>
  </v-sheet>
</template>

<script>
export default {
  props: {
    music_data: Array,
    music_data_dict: Object,
  },
  data: () => {
    return {
      darkTheme: false,
      fc_filter: [],
      fs_filter: [],
      diff_filter: [],
      rate_filter: [],
      fc_filter_items: [
        { text: "空", value: 0 }, // 0 instead of "" because of vuetify jank
        { text: "FC", value: "fc" },
        { text: "FC+", value: "fcp" },
        { text: "AP", value: "ap" },
        { text: "AP+", value: "app" },
      ],
      fs_filter_items: [
        { text: "空", value: 0 }, // 0 instead of "" because of vuetify jank
        { text: "FS", value: "fs" },
        { text: "FS+", value: "fsp" },
        { text: "FDX", value: "fsd" },
        { text: "FDX+", value: "fsdp" },
      ],
      diff_filter_items: [
        { text: "Basic", value: 0 },
        { text: "Advanced", value: 1 },
        { text: "Expert", value: 2 },
        { text: "Master", value: 3 },
        { text: "Re:MASTER", value: 4 },
      ],
      rate_filter_items: [
        { text: "SSS+", value: "sssp" },
        { text: "SSS", value: "sss" },
        { text: "SS+", value: "ssp" },
        { text: "SS", value: "ss" },
        { text: "S+", value: "sp" },
        { text: "S", value: "s" },
        { text: "AAA", value: "aaa" },
        { text: "AA", value: "aa" },
        { text: "A", value: "a" },
        { text: "B", value: "b" },
        { text: "C", value: "c" },
        { text: "D", value: "d" },
      ],
      version: null,
      genre: null,
      headers: [],
      headers_default: [
        { text: "排名", value: "rank" },
        { text: "乐曲名", value: "title" },
        { text: "难度", value: "level", sortable: false },
        { text: "定数", value: "ds" },
        { text: "达成率", value: "achievements" },
        { text: "DX Rating", value: "ra" },
        { text: "拟合难度", value: "fit_diff" },
        { text: "操作", value: "actions", sortable: false },
      ],
      headers_items: [
        { text: "排名", value: "rank" },
        { text: "封面", value: "cover", sortable: false},
        { text: "乐曲名", value: "title" },
        { text: "难度", value: "level", sortable: false },
        { text: "定数", value: "ds" },
        { text: "达成率", value: "achievements" },
        { text: "DX Rating", value: "ra" },
        { text: "拟合难度", value: "fit_diff" },
        { text: "DX分数", value: "dxScore" },
        { text: "DX分数比例", value: "dxScore_perc" },
        { text: "操作", value: "actions", sortable: false },
      ],
      headers_values: [
        "rank",
        "cover",
        "title",
        "level",
        "ds",
        "achievements",
        "ra",
        "fit_diff",
        "dxScore",
        "dxScore_perc",
        "actions",
      ],
    };
  },
  computed: {
    versions: function () {
      return Array.from(
        new Set(
          this.music_data.map((elem) => {
            return elem.basic_info.from;
          })
        )
      );
    },
    genres: function () {
      return Array.from(
        new Set(
          this.music_data.map((elem) => {
            return elem.basic_info.genre;
          })
        )
      );
    },
  },
  methods: {
    f(item) {
      return (
        this.fc_filter.findIndex((i) => i == item.fc) !== -1 &&
        this.fs_filter.findIndex((i) => i == item.fs) !== -1 &&
        this.diff_filter.findIndex((i) => i == item.level_index) !== -1 &&
        this.rate_filter.findIndex((i) => i == item.rate) !== -1 &&
        (!this.version ||
          this.music_data_dict[item.song_id] &&
          this.music_data_dict[item.song_id].basic_info.from == this.version) &&
        (!this.genre ||
          this.music_data_dict[item.song_id] &&
          this.music_data_dict[item.song_id].basic_info.genre == this.genre)
      );
    },
    toggleDarkTheme: function (param) {
      localStorage.darkTheme = +param;
      this.$vuetify.theme.dark = this.darkTheme;
    },
    getLevel(index) {
      return ["#22bb5b", "#fb9c2d", "#f64861", "#9e45e2", "#ba67f8"][index];
    },
    getFC(str) {
      if (!str) return "grey";
      if (str.startsWith("fc")) return "green";
      return "orange";
    },
    getFS(str) {
      if (!str) return "grey";
      if (str.startsWith("fsd")) return "orange";
      return "blue";
    },
    getRate(str) {
      if (str.startsWith("sssp")) return "red";
      if (str.startsWith("sss")) return "blue darken-1";
      if (str.startsWith("ssp")) return "amber darken-2";
      return "grey";
    },
    setHeaders() {
      this.headers.sort(
        (a, b) =>
          this.headers_values.indexOf(a.value) -
          this.headers_values.indexOf(b.value)
      );
      this.$emit("setHeaders", this.headers);
    },
    setHeadersDefault(headers) {
      localStorage.headers_default = JSON.stringify(headers);
      this.headers_default = headers;
      this.$message.success(`已保存表列设置`);
    },
    reset() {
      this.fc_filter = [0, "fc", "fcp", "ap", "app"];
      this.fs_filter = [0, "fs", "fsp", "fsd", "fsdp"];
      this.diff_filter = [0, 1, 2, 3, 4];
      this.rate_filter = [
        "sssp",
        "sss",
        "ssp",
        "ss",
        "sp",
        "s",
        "aaa",
        "aa",
        "a",
        "b",
        "c",
        "d",
      ];
      this.headers = this.headers_default;
      console.log(this.headers)
      this.setHeaders();
    },
  },
  created: function () {
    if (localStorage.headers_default) {
      try {
        this.headers_default = JSON.parse(localStorage.headers_default);
        let headers_items_stringified = this.headers_items.map((o) =>
          JSON.stringify(o)
        );
        this.headers_default = this.headers_default.filter(
          (o) => headers_items_stringified.indexOf(JSON.stringify(o)) != -1
        );
      } catch (e) {
        this.headers_default = [
          { text: "排名", value: "rank" },
          { text: "乐曲名", value: "title" },
          { text: "难度", value: "level", sortable: false },
          { text: "定数", value: "ds" },
          { text: "达成率", value: "achievements" },
          { text: "DX Rating", value: "ra" },
          { text: "拟合难度", value: "fit_diff" },
          { text: "操作", value: "actions", sortable: false },
        ];
      }
    }
    this.reset();
    // listen change of system dark mode
    let matchMedia = window.matchMedia("(prefers-color-scheme: dark)")
    matchMedia.addEventListener("change", () => {
      this.darkTheme = matchMedia.matches
      this.toggleDarkTheme(matchMedia.matches);
    });

    this.darkTheme = +localStorage.darkTheme;
  },
  beforeCreate: function () {
    // detect dark mode
    localStorage.darkTheme = +window.matchMedia("(prefers-color-scheme: dark)").matches
    if (+localStorage.darkTheme) {
      document
        .querySelector("body")
        .setAttribute("style", "background: #121212; color: #FFFFFF;");
    }
    this.$vuetify.theme.dark = +localStorage.darkTheme;
  },
};
</script>

<style>
.v-slide-group__next,
.v-slide-group__prev {
  min-width: 32px !important;
}
</style>

<style scoped>
.v-subheader {
  float: right;
  min-width: 102px;
  justify-content: right;
  padding: 0px !important;
}
</style>
