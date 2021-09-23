<template>
  <v-sheet style="display: box; margin: 0px 16px">
    <v-row dense>
      <v-col cols="3" class="px-0 py-0">
        <v-subheader style="float: right">
          连击筛选
          <v-icon
            @click="
              fc_filter.length === fc_filter_items.length
                ? (fc_filter = [])
                : (fc_filter = fc_filter_items.map((i) => i.value))
            "
            class="ml-4"
          >
            mdi-check-all
          </v-icon></v-subheader
        >
      </v-col>
      <v-col cols="9" class="px-0 py-0">
        <v-slide-group
          multiple
          v-model="fc_filter"
          class="ml-4 py-2"
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
      <v-col cols="3" class="px-0 py-0">
        <v-subheader style="float: right">
          同步率筛选
          <v-icon
            @click="
              fs_filter.length === fs_filter_items.length
                ? (fs_filter = [])
                : (fs_filter = fs_filter_items.map((i) => i.value))
            "
            class="ml-4"
          >
            mdi-check-all
          </v-icon></v-subheader
        >
      </v-col>
      <v-col cols="9" class="px-0 py-0">
        <v-slide-group
          multiple
          v-model="fs_filter"
          class="ml-4 py-2"
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
      <v-col cols="3" class="px-0 py-0">
        <v-subheader style="float: right">
          难度筛选
          <v-icon
            @click="
              diff_filter.length === diff_filter_items.length
                ? (diff_filter = [])
                : (diff_filter = diff_filter_items.map((i) => i.value))
            "
            class="ml-4"
          >
            mdi-check-all
          </v-icon></v-subheader
        >
      </v-col>
      <v-col cols="9" class="px-0 py-0">
        <v-slide-group
          multiple
          v-model="diff_filter"
          class="ml-4 py-2"
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
      <v-col cols="3" class="px-0 py-0">
        <v-subheader style="float: right">
          达成率筛选
          <v-icon
            @click="
              rate_filter.length === rate_filter_items.length
                ? (rate_filter = [])
                : (rate_filter = rate_filter_items.map((i) => i.value))
            "
            class="ml-4"
          >
            mdi-check-all
          </v-icon></v-subheader
        >
      </v-col>
      <v-col cols="9" class="px-0 py-0">
        <v-slide-group
          multiple
          v-model="rate_filter"
          class="ml-4 py-2"
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
    <v-row align="center">
      <v-col cols="6">
        <v-select
          v-model="headers"
          :items="headers_items"
          label="选择分数表列"
          multiple
          @change="setHeaders"
          return-object
        >
          <template v-slot:prepend-item>
            <v-list-item
              ripple
              @click="
                headers = [
                  { text: '排名', value: 'rank' },
                  { text: '乐曲名', value: 'title' },
                  { text: '难度', value: 'level', sortable: false },
                  { text: '定数', value: 'ds' },
                  { text: '达成率', value: 'achievements' },
                  { text: 'DX Rating', value: 'ra' },
                  { text: '相对难度', value: 'tag' },
                  { text: '编辑', value: 'actions', sortable: false },
                ]
              "
            >
              <v-list-item-content>
                <v-list-item-title> 恢复默认 </v-list-item-title>
              </v-list-item-content>
            </v-list-item>
            <v-divider class="mt-2"></v-divider>
          </template>
          <template v-slot:selection="{ item, index }">
            {{
              2 >= index
                ? index === headers.length - 1
                  ? item.text
                  : item.text + ","
                : index == 3
                ? "..."
                : ""
            }}
          </template>
        </v-select>
      </v-col>
      <v-col cols="3">
        <v-checkbox
          label="使用暗色主题"
          v-model="darkTheme"
          @change="toggleDarkTheme"
        ></v-checkbox>
      </v-col>
    </v-row>
  </v-sheet>
</template>

<script>
export default {
  data: () => {
    return {
      darkTheme: false,
      fc_filter: [0, "fc", "fcp", "ap", "app"],
      fs_filter: [0, "fs", "fsp", "fsd", "fsdp"],
      diff_filter: [0, 1, 2, 3, 4],
      rate_filter: [
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
      ],
      fc_filter_items: [
        { text: "空", value: 0 },
        { text: "FC", value: "fc" },
        { text: "FC+", value: "fcp" },
        { text: "AP", value: "ap" },
        { text: "AP+", value: "app" },
      ],
      fs_filter_items: [
        { text: "空", value: 0 },
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
      headers_items: [
        { text: "排名", value: "rank" },
        { text: "乐曲名", value: "title" },
        { text: "难度", value: "level", sortable: false },
        { text: "定数", value: "ds" },
        { text: "达成率", value: "achievements" },
        { text: "DX Rating", value: "ra" },
        { text: "相对难度", value: "tag" },
        { text: "DX分数", value: "dxScore" },
        { text: "DX分数比例", value: "dxScore_perc" },
        { text: "编辑", value: "actions", sortable: false },
      ],
      headers_values: [
        "rank",
        "title",
        "level",
        "ds",
        "achievements",
        "ra",
        "tag",
        "dxScore",
        "dxScore_perc",
        "actions",
      ],
    };
  },
  methods: {
    f(item) {
      return (
        this.fc_filter.findIndex((i) => i == item.fc) !== -1 &&
        this.fs_filter.findIndex((i) => i == item.fs) !== -1 &&
        this.diff_filter.findIndex((i) => i == item.level_index) !== -1 &&
        this.rate_filter.findIndex((i) => i == item.rate) !== -1
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
  },
  created: function () {
    this.darkTheme = +localStorage.darkTheme;
  },
  beforeCreate: function () {
    if (+localStorage.darkTheme) {
      document
        .querySelector("body")
        .setAttribute("style", "background: #121212; color: #FFFFFF;");
    }
    this.$vuetify.theme.dark = +localStorage.darkTheme;
  },
};
</script>