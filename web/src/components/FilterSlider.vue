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
      :value="ds"
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
      :value="level"
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
      :style="
        $vuetify.breakpoint.mobile
          ? 'margin: -12px 0px'
          : 'margin: 0px 0px 0px 16px'
      "
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
        "15"
      ],
    };
  },
  methods: {
    f(item) {
      const allow_levels = this.level_item.slice(this.level[0], this.level[1] + 1);
      if (this.useDs) {
        return (item.ds >= this.ds[0] && item.ds <= this.ds[1])
      } else {
        return (allow_levels.indexOf(item.level) !== -1)
      }
    },
    end_move_level(param) {
      this.level = param;
    },
    end_move_ds(param) {
      this.ds = param;
    }
  },
};
</script>