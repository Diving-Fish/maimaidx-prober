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
      max="15"
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
      max="22"
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
export default {
  data: () => {
    return {
      useDs: false,
      ds: [1, 15],
      level: [0, 22],
      ds_model: [1, 15],
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
      ],
      level_min: [
        1, 2, 3, 4, 5, 6, 7, 7.7, 8, 8.7, 9, 9.7, 10, 10.7, 11, 11.7, 12, 12.7,
        13, 13.7, 14, 14.7, 15,
      ],
      level_max: [
        1.9, 2.9, 3.9, 4.9, 5.9, 6.9, 7.6, 7.9, 8.6, 8.9, 9.6, 9.9, 10.6, 10.9,
        11.6, 11.9, 12.6, 12.9, 13.6, 13.9, 14.6, 14.9, 15,
      ],
    };
  },
  methods: {
    f(item) {
      const allow_levels = this.level_item.slice(this.level[0], this.level[1] + 1);
      if (this.useDs) {
        return item.ds >= this.ds[0] && item.ds <= this.ds[1];
      } else {
        return allow_levels.indexOf(item.level) !== -1;
      }
    },
    end_move_level(param) {
      this.level = param;
    },
    end_move_ds(param) {
      this.ds = param;
    },
    change(param) {
      // console.log(param);
      if (param) {
        this.ds = [
          this.level_min[this.level[0]],
          this.level_max[this.level[1]],
        ];
        this.ds_model = this.ds;
      } else {
        this.level[0] = this.level_max.findIndex((l) => l >= this.ds[0]);
        this.level[1] = this.level_max.findIndex((l) => l >= this.ds[1]);
        this.level_model = this.level;
      }
    },
  },
};
</script>