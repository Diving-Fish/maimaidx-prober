<template>
  <div
    :style="
      ($vuetify.breakpoint.mobile ? 'display: block' : 'display: flex') +
      '; margin: 0px 16px'
    "
  >
    <v-range-slider
      v-show="useDs"
      thumb-label
      :hide-details="!$vuetify.breakpoint.mobile"
      v-model="ds_model"
      min="1"
      :max="dsMax"
      step="0.1"
      label="定数"
      @end="end_move_ds"
    >
    </v-range-slider>
    <v-range-slider
      v-show="!useDs"
      thumb-label
      :hide-details="!$vuetify.breakpoint.mobile"
      v-model="level_model"
      min="0"
      :max="maxLevelIndex"
      label="等级"
      @end="end_move_level"
    >
      <template v-slot:thumb-label="props">
        {{ level_item[props.value] }}
      </template>
    </v-range-slider>
    <v-checkbox
      label="使用定数筛选"
      v-model="useDs"
      hide-details
      :style="
        $vuetify.breakpoint.mobile
          ? 'margin: -12px 0px'
          : 'margin: 0px 0px 0px 16px'
      "
      @change="change"
    ></v-checkbox>
  </div>
</template>

<script>
// 乐曲数据加载完成前的兜底上界，也是滑块的初始上界。
const DEFAULT_MAX_DS = 15.5;

export default {
  props: {
    // 乐曲数据里的最高定数。滑块上界跟着它动态走，否则新版本抬高定数上限
    // （中二节奏已经出现 15+ / 15.7）之后，最难的谱面会被默认筛选范围直接筛掉。
    maxDs: { type: Number, default: DEFAULT_MAX_DS },
  },
  data: () => {
    return {
      useDs: false,
      ds: [1, DEFAULT_MAX_DS],
      level: [0, 22],
      ds_model: [1, DEFAULT_MAX_DS],
      level_model: [0, 22],
      level_item: [
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "7+",
        "8",
        "8+",
        "9",
        "9+",
        "10",
        "10+",
        "11",
        "11+",
        "12",
        "12+",
        "13",
        "13+",
        "14",
        "14+",
        "15",
        "15+",
      ],
      level_min: [
        1, 2, 3, 4, 5, 6, 7, 7.6, 8, 8.6, 9, 9.6, 10, 10.6, 11, 11.6, 12, 12.6,
        13, 13.6, 14, 14.6, 15, 15.5,
      ],
      // 最后一档（15+）的上界由 levelMaxRanges 用实际最高定数补上
      level_max: [
        1.9, 2.9, 3.9, 4.9, 5.9, 6.9, 7.5, 7.9, 8.5, 8.9, 9.5, 9.9, 10.5, 10.9,
        11.5, 11.9, 12.5, 12.9, 13.5, 13.9, 14.5, 14.9, 15.5, DEFAULT_MAX_DS,
      ],
    };
  },
  computed: {
    // level 字符串 → 在 level_item 中的序号，只建一次。
    // 用于把 f() 里的「slice + indexOf」降为 O(1) 查表，避免逐条记录新建数组。
    levelOrder: function () {
      const map = {};
      for (let i = 0; i < this.level_item.length; i++) {
        map[this.level_item[i]] = i;
      }
      return map;
    },
    dsMax: function () {
      return Number.isFinite(this.maxDs) && this.maxDs > 1
        ? this.maxDs
        : DEFAULT_MAX_DS;
    },
    // 等级 → 定数区间的上界表，最高一档跟着数据里的最高定数走
    levelMaxRanges: function () {
      const ranges = this.level_max.slice();
      ranges[ranges.length - 1] = this.dsMax;
      return ranges;
    },
    // 数据里最高定数所落在的等级档位，等级滑块的上界。
    // 例如中二节奏最高 15.7 → 15+，舞萌 DX 最高 15.0 → 15（不出现用不到的 15+）。
    maxLevelIndex: function () {
      const idx = this.levelMaxRanges.findIndex((max) => max >= this.dsMax);
      return idx === -1 ? this.levelMaxRanges.length - 1 : idx;
    },
  },
  watch: {
    // 乐曲数据是异步加载的：上界变化时，仍然拉满的滑块跟着抬到新的上界，
    // 否则默认筛选范围会把最高定数的谱面挡在表格外面。
    dsMax: function (n, o) {
      if (this.ds[1] >= o) {
        this.ds = [this.ds[0], n];
        this.ds_model = this.ds.slice();
      }
    },
    maxLevelIndex: function (n, o) {
      if (this.level[1] >= o) {
        this.level = [this.level[0], n];
        this.level_model = this.level.slice();
      }
    },
  },
  methods: {
    f(item) {
      if (this.useDs) {
        return item.ds >= this.ds[0] && item.ds <= this.ds[1];
      }
      const idx = this.levelOrder[item.level];
      return idx !== undefined && idx >= this.level[0] && idx <= this.level[1];
    },
    end_move_level(param) {
      this.level = param.slice();
    },
    end_move_ds(param) {
      this.ds = param.slice();
    },
    change(param) {
      // console.log(param);
      if (param) {
        this.ds = [
          this.level_min[this.level[0]],
          this.levelMaxRanges[this.level[1]],
        ];
        this.ds_model = this.ds.slice();
      } else {
        this.level = [
          this.dsToLevelIndex(this.ds[0]),
          this.dsToLevelIndex(this.ds[1]),
        ];
        this.level_model = this.level.slice();
      }
    },
    dsToLevelIndex(ds) {
      const idx = this.levelMaxRanges.findIndex((l) => l >= ds);
      return idx === -1 ? this.maxLevelIndex : idx;
    },
  },
};
</script>
