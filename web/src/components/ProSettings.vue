<template>
  <div :style="'display: box; margin: 0px 16px'">
    <v-row align="center">
      <v-col>
        <v-select
          v-model="fc_filter"
          :items="fc_filter_items"
          item-value="value"
          label="连击筛选"
          multiple
        >
          <template v-slot:prepend-item>
            <v-list-item
              ripple
              @click="
                fc_filter.length === fc_filter_items.length
                  ? (fc_filter = [])
                  : (fc_filter = ['', 'fc', 'fcp', 'ap', 'app'])
              "
            >
              <v-list-item-content>
                <v-list-item-title>
                  {{
                    fc_filter.length === fc_filter_items.length
                      ? "取消全选"
                      : "全选"
                  }}
                </v-list-item-title>
              </v-list-item-content>
            </v-list-item>
            <v-divider class="mt-2"></v-divider>
          </template>
          <template v-slot:selection="{ item, index }">
            <v-chip v-if="index <= 1" :color="getFC(item.value)" dark>
              {{ item.text }}
            </v-chip>
            <span v-if="index === 2" class="grey--text text-caption">
              (+{{ fc_filter.length - 2 }}...)
            </span>
          </template></v-select
        >
      </v-col>
      <v-col>
        <v-select
          v-model="fs_filter"
          :items="fs_filter_items"
          item-value="value"
          label="同步率筛选"
          multiple
        >
          <template v-slot:prepend-item>
            <v-list-item
              ripple
              @click="
                fs_filter.length === fs_filter_items.length
                  ? (fs_filter = [])
                  : (fs_filter = ['', 'fs', 'fsp', 'fdx', 'fdxp'])
              "
            >
              <v-list-item-content>
                <v-list-item-title>
                  {{
                    fs_filter.length === fs_filter_items.length
                      ? "取消全选"
                      : "全选"
                  }}
                </v-list-item-title>
              </v-list-item-content>
            </v-list-item>
            <v-divider class="mt-2"></v-divider>
          </template>
          <template v-slot:selection="{ item, index }">
            <v-chip v-if="index <= 1" :color="getFS(item.value)" dark>
              {{ item.text }}
            </v-chip>
            <span v-if="index === 2" class="grey--text text-caption">
              (+{{ fs_filter.length - 2 }}...)
            </span>
          </template></v-select
        >
      </v-col>
    </v-row>
    <v-row align="center">
      <v-col>
        <v-select
          v-model="diff_filter"
          :items="diff_filter_items"
          item-value="value"
          label="难度筛选"
          multiple
        >
          <template v-slot:prepend-item>
            <v-list-item
              ripple
              @click="
                diff_filter.length === diff_filter_items.length
                  ? (diff_filter = [])
                  : (diff_filter = [0, 1, 2, 3, 4])
              "
            >
              <v-list-item-content>
                <v-list-item-title>
                  {{
                    diff_filter.length === diff_filter_items.length
                      ? "取消全选"
                      : "全选"
                  }}
                </v-list-item-title>
              </v-list-item-content>
            </v-list-item>
            <v-divider class="mt-2"></v-divider>
          </template>
          <template v-slot:selection="{ item, index }">
            <v-chip v-if="index <= 1" :color="getLevel(item.value)" dark>
              {{ item.text }}
            </v-chip>
            <span v-if="index === 2" class="grey--text text-caption">
              (+{{ diff_filter.length - 2 }}...)
            </span>
          </template></v-select
        >
      </v-col>
      <v-col>
        <v-select
          v-model="rate_filter"
          :items="rate_filter_items"
          item-value="value"
          label="达成率筛选"
          multiple
        >
          <template v-slot:prepend-item>
            <v-list-item
              ripple
              @click="
                rate_filter.length === rate_filter_items.length
                  ? (rate_filter = [])
                  : (rate_filter = [
                      'sssp',
                      'sss',
                      'ssp',
                      'ss',
                      'sp',
                      's',
                      'aaa',
                      'aa',
                      'a',
                      'b',
                      'c',
                      'd',
                    ])
              "
            >
              <v-list-item-content>
                <v-list-item-title>
                  {{
                    rate_filter.length === rate_filter_items.length
                      ? "取消全选"
                      : "全选"
                  }}
                </v-list-item-title>
              </v-list-item-content>
            </v-list-item>
            <v-divider class="mt-2"></v-divider>
          </template>
          <template v-slot:selection="{ item, index }">
            <v-chip v-if="index <= 1" :color="getRate(item.value)" outlined>
              {{ item.text }}
            </v-chip>
            <span v-if="index === 2" class="grey--text text-caption">
              (+{{ rate_filter.length - 2 }}...)
            </span>
          </template></v-select
        >
      </v-col>
    </v-row>
    <v-row align="center">
      <v-col>
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
                <v-list-item-title> "恢复默认" </v-list-item-title>
              </v-list-item-content>
            </v-list-item>
            <v-divider class="mt-2"></v-divider>
          </template>
          <!-- <template v-slot:selection="{ item, index }">
            <v-chip v-if="index <= 1" :color="getLevel(item.value)" dark>
              {{ item.text }}
            </v-chip>
            <span v-if="index === 2" class="grey--text text-caption">
              (+{{ diff_filter.length - 2 }}...)
            </span>
          </template> -->
        </v-select>
      </v-col>
      <v-col>
        <v-checkbox
          label="使用暗色主题"
          v-model="darkTheme"
          @change="toggleDarkTheme"
        ></v-checkbox>
      </v-col>
    </v-row>
  </div>
</template>

<script>
export default {
  data: () => {
    return {
      darkTheme: false,
      fc_filter: ["", "fc", "fcp", "ap", "app"],
      fs_filter: ["", "fs", "fsp", "fsd", "fsdp"],
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
        { text: "空", value: "" },
        { text: "FC", value: "fc" },
        { text: "FC+", value: "fcp" },
        { text: "AP", value: "ap" },
        { text: "AP+", value: "app" },
      ],
      fs_filter_items: [
        { text: "空", value: "" },
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
        this.fc_filter.indexOf(item.fc) !== -1 &&
        this.fs_filter.indexOf(item.fs) !== -1 &&
        this.diff_filter.indexOf(item.level_index) !== -1 &&
        this.rate_filter.indexOf(item.rate) !== -1
      );
    },
    toggleDarkTheme: function (param) {
      console.log(param);
      localStorage.darkTheme = +param;
      this.$vuetify.theme.dark = this.darkTheme;
    },
    getLevel(index) {
      return ["#22bb5b", "#fb9c2d", "#f64861", "#9e45e2", "#ba67f8"][index];
    },
    getFC(str) {
      if (!str || str.startsWith("fc")) return "green";
      return "orange";
    },
    getFS(str) {
      if (str && str.startsWith("fsd")) return "orange";
      return "blue";
    },
    getRate(str) {
      if (str.startsWith("sssp")) return "red";
      if (str.startsWith("sss")) return "blue darken-1";
      if (str.startsWith("ssp")) return "amber darken-2";
      return "";
    },
    setHeaders() {
      this.headers.sort(
        (a, b) => this.headers_values.indexOf(a.value) - this.headers_values.indexOf(b.value)
      );
      console.log(this.headers.map((h) => h.text));
      console.log(this.headers.sort(
        (a, b) => this.headers_values.indexOf(a.value) - this.headers_values.indexOf(b.value)
      ));
      this.$emit("setHeaders", this.headers);
    },
  },
  created: function () {
    if (+localStorage.darkTheme) {
      this.darkTheme = localStorage.darkTheme;
    }
    this.$vuetify.theme.dark = this.darkTheme;
  },
};
</script>