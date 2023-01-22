<template>
  <v-sheet style="display: box; margin: 0px 16px">
    <v-row dense>
      <v-col cols="4" class="px-0 py-0">
        <v-subheader>
          按连击情况筛选
          <v-icon @click="fc_filter.length === fc_filter_items.length ? (fc_filter = []) : (fc_filter = fc_filter_items.map((i) => i.value))" class="ml-2">mdi-check-all</v-icon>
        </v-subheader>
      </v-col>
      <v-col cols="8" class="px-0 py-0">
        <v-slide-group multiple v-model="fc_filter" class="ml-2 py-2" show-arrows>
          <v-slide-item v-for="(item,key) in fc_filter_items" :key="key" :value="item.value" class="mr-2" v-slot="{ active, toggle }">
            <v-chip :color="getFC(item.value)" :outlined="!active" dark @click="toggle">{{ item.text }}</v-chip>
          </v-slide-item>
        </v-slide-group>
      </v-col>
    </v-row>
    <v-row dense>
      <v-col cols="4" class="px-0 py-0">
        <v-subheader>
          按难度筛选
          <v-icon @click="level_filter.length === level_filter_items.length ? (level_filter = []) : (level_filter = level_filter_items.map((i) => i.value))" class="ml-2">mdi-check-all</v-icon>
        </v-subheader>
      </v-col>
      <v-col cols="8" class="px-0 py-0">
        <v-slide-group multiple v-model="level_filter" class="ml-2 py-2" show-arrows>
          <v-slide-item v-for="(item,key) in level_filter_items" :key="key" :value="item.value" class="mr-2" v-slot="{ active, toggle }">
            <v-chip :color="getLevel(item.value)" :outlined="!active" dark @click="toggle">{{ item.text }}</v-chip>
          </v-slide-item>
        </v-slide-group>
      </v-col>
    </v-row>
    <v-row dense>
      <v-col cols="4" class="px-0 py-0">
        <v-subheader>
          按评级筛选
          <v-icon @click="rate_filter.length === rate_filter_items.length ? (rate_filter = []) : (rate_filter = rate_filter_items.map((i) => i.value))" class="ml-2">mdi-check-all</v-icon>
        </v-subheader>
      </v-col>
      <v-col cols="8" class="px-0 py-0">
        <v-slide-group multiple v-model="rate_filter" class="ml-2 py-2" show-arrows>
          <v-slide-item v-for="(item,key) in rate_filter_items" :key="key" :value="item.value" class="mr-2" v-slot="{ active, toggle }">
            <v-chip :color="getRate(item.value)" :outlined="!active" dark @click="toggle">{{ item.text }}</v-chip>
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
    <v-col cols="5" class="px-0 py-0">
      <v-checkbox label="使用暗色主题" v-model="darkTheme" hide-details @change="toggleDarkTheme"></v-checkbox>
    </v-col>
  </v-sheet>
</template>

<script>
export default {
  props: {
    music_data: Array,
    music_data_dict: Object,
  },
  data: ()=>{
    return {
      darkTheme: false,
      fc_filter: [],
      level_filter: [],
      rate_filter: [],
      version: null,
      genre: null,
      fc_filter_items: [
        { text: "空", value: 0},
        { text: "FC", value: "fullcombo"},
        { text: "AJ", value: "alljustice"},
      ],
      level_filter_items: [
        { text: "Basic", value: 0 },
        { text: "Advanced", value: 1 },
        { text: "Expert", value: 2 },
        { text: "Master", value: 3 },
        { text: "Ultima", value: 4 },
        { text: "World's End", value: 5},
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
        { text: "BBB", value: "bbb"},
        { text: "BB", value: "bb"},
        { text: "B", value: "b" },
        { text: "C", value: "c" },
        { text: "D", value: "d" },
      ],
      headers: [],
      headers_default: [
        { text: '排名', value: 'rank' },
        { text: '乐曲名', value: 'title' },
        { text: '难度', value: 'level' },
        { text: '定数', value: 'ds' },
        { text: '分数', value: 'score' },
        { text: 'Rating', value: 'ra' },
      ]
    }
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
          this.level_filter.findIndex((i) => i == item.level_index) !== -1 &&
          this.rate_filter.findIndex((i) => i == this.getRateLabel(item.score)) !== -1 &&
          (!this.version ||
              this.music_data_dict[item.mid] &&
              this.music_data_dict[item.mid].basic_info.from == this.version) &&
          (!this.genre ||
              this.music_data_dict[item.mid] &&
              this.music_data_dict[item.mid].basic_info.genre == this.genre)
      )
    },
    getRateLabel(val) {
      if (val < 500000) {
        return 'd'
      } else if (val < 600000) {
        return 'c'
      } else if (val < 700000) {
        return 'b'
      } else if (val < 800000) {
        return 'bb'
      } else if (val < 900000) {
        return 'bbb'
      } else if (val < 925000) {
        return 'a'
      } else if (val < 950000) {
        return 'aa'
      } else if (val < 975000) {
        return 'aaa'
      } else if (val < 990000) {
        return 's'
      } else if (val < 1000000) {
        return 'sp'
      } else if (val < 1005000) {
        return 'ss'
      } else if (val < 1007500) {
        return 'ssp'
      } else if (val < 1009000) {
        return 'sss'
      } else if (val <= 1010000){
        return 'sssp'
      } else {
        return NaN
      }
    },
    toggleDarkTheme: function (param) {
      localStorage.darkTheme = +param;
      this.$vuetify.theme.dark = this.darkTheme;
    },
    getLevel(index) {
      return ["#22bb5b", "#fb9c2d", "#f64861", "#9e45e2", "#1B1B1B", "cyan"][index];
    },
    getFC(str) {
      if (!str) return "grey";
      if (str.startsWith("fullcombo")) return "green";
      return "orange";
    },
    getRate(str) {
      if (str.startsWith("sssp")) return "red";
      if (str.startsWith("sss")) return "blue darken-1";
      if (str.startsWith("ssp")) return "amber darken-2";
      return "grey";
    },
    reset() {
      this.fc_filter = [0, "fullcombo", "alljustice"];
      this.level_filter = [0, 1, 2, 3, 4, 5];
      this.rate_filter = ["sssp", "sss", "ssp", "ss", "sp", "s", "aaa", "aa", "a", "bbb", "bb", "b", "c", "d"];
    },
    created: function () {
      this.reset()
    }
  },
  name: "ProSettingsChuni"
}
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