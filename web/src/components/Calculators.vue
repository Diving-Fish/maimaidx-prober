<template>
  <v-dialog
    v-model="visible"
    :width="700"
    :fullscreen="$vuetify.breakpoint.mobile"
  >
    <template #activator="{ on, attrs }">
      <v-btn class="mt-3 mr-4" v-bind="attrs" v-on="on">计算工具</v-btn>
    </template>
    <v-card>
      <v-card-title>
        计算工具
        <v-spacer />
        <v-btn icon @click="visible = false">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      <v-card-subtitle v-show="current_song">
        当前为
        <i
          >{{ current_song.type == "DX" ? "[DX] " : ""
          }}<b>{{ current_song.title }}</b> [{{
            current_song.level_label
          }}]</i
        >
        的数据
      </v-card-subtitle>
      <v-card-text>
        <v-tabs v-model="tab">
          <v-tab key="score">分数线/绝赞分布计算</v-tab>
          <v-tab key="rating">rating线计算</v-tab>
        </v-tabs>
        <v-tabs-items v-model="tab">
          <v-tab-item key="score">
            <v-container class="pa-1">
              <v-row>
                <v-col v-for="(item, key) in notes" :key="key">
                  <v-text-field
                    :label="key + '总数'"
                    v-model="note_total[key]"
                    :rules="[
                      (u) =>
                        (isFinite(+u) && +u >= 0 && !(+u % 1)) ||
                        '请输入0或正整数',
                    ]"
                    :disabled="manual_input"
                    @change="clear_current_song"
                    @keydown="clear_current_song"
                  ></v-text-field>
                </v-col>
              </v-row>

              <v-row no-gutters class="mt-0 flex-nowrap">
                <v-col class="col-score-table"
                  ><v-select
                    :items="score_modes"
                    v-model="score_mode"
                    label="分数模式"
                    item-text="name"
                    dense
                    tile
                    hide-details
                    return-object
                  ></v-select
                ></v-col>
                <v-col
                  class="col-score-table"
                  v-for="(item, judge) in judges"
                  :key="judge"
                >
                  <v-card
                    class="pa-2 d-flex align-center fill-height"
                    :color="item.color"
                    dark
                    tile
                  >
                    {{ judge }}
                  </v-card>
                </v-col>
              </v-row>
              <v-divider></v-divider>
              <v-row
                no-gutters
                class="mt-0"
                v-for="(item, note) in score_normal"
                :key="note"
              >
                <v-col class="col-score-table"
                  ><v-card class="pa-2 d-flex align-center fill-height" tile>{{
                    note
                  }}</v-card></v-col
                >
                <v-col
                  class="col-score-table"
                  v-for="(score, judge) in item"
                  :key="judge"
                >
                  <v-card
                    class="pa-2 d-flex align-center fill-height"
                    :color="judges[judge].color"
                    dark
                    tile
                    >{{ score }}</v-card
                  >
                </v-col>
              </v-row>
              <v-row no-gutters class="mt-0 flex-nowrap">
                <v-col class="col-score-table">
                  <v-card class="pa-2 d-flex align-center fill-height" tile
                    >Break</v-card
                  >
                </v-col>
                <v-col class="col-score-table">
                  <v-row no-gutters class="mt-0">
                    <v-col>
                      <v-card
                        class="pa-2"
                        :color="break_judges.CRITICAL_PERFECT.color"
                        dark
                        tile
                        >{{ score_break.CRITICAL_PERFECT }}</v-card
                      >
                    </v-col>
                  </v-row>
                  <v-row no-gutters class="mt-0">
                    <v-col>
                      <v-card
                        class="pa-2"
                        :color="break_judges.PERFECT_A.color"
                        dark
                        tile
                        >{{ score_break.PERFECT_A }}</v-card
                      >
                    </v-col>
                  </v-row>
                  <v-row no-gutters class="mt-0">
                    <v-col>
                      <v-card
                        class="pa-2"
                        :color="break_judges.PERFECT_B.color"
                        dark
                        tile
                        >{{ score_break.PERFECT_B }}</v-card
                      >
                    </v-col>
                  </v-row>
                </v-col>
                <v-col class="col-score-table">
                  <v-row no-gutters class="mt-0">
                    <v-col>
                      <v-card
                        class="pa-2"
                        :color="break_judges.GREAT_A.color"
                        dark
                        tile
                        >{{ score_break.GREAT_A }}</v-card
                      >
                    </v-col>
                  </v-row>
                  <v-row no-gutters class="mt-0">
                    <v-col>
                      <v-card
                        class="pa-2"
                        :color="break_judges.GREAT_B.color"
                        dark
                        tile
                        >{{ score_break.GREAT_B }}</v-card
                      >
                    </v-col>
                  </v-row>
                  <v-row no-gutters class="mt-0">
                    <v-col>
                      <v-card
                        class="pa-2"
                        :color="break_judges.GREAT_C.color"
                        dark
                        tile
                        >{{ score_break.GREAT_C }}</v-card
                      >
                    </v-col>
                  </v-row>
                </v-col>
                <v-col class="col-score-table">
                  <v-card
                    class="pa-2 d-flex align-center fill-height"
                    :color="break_judges.GOOD.color"
                    dark
                    tile
                    >{{ score_break.GOOD }}</v-card
                  >
                </v-col>
                <v-col class="col-score-table">
                  <v-card
                    class="pa-2 d-flex align-center fill-height"
                    :color="break_judges.MISS.color"
                    dark
                    tile
                    >{{ score_break.MISS }}</v-card
                  >
                </v-col>
              </v-row>
              <v-row>
                <v-col>
                  <v-text-field
                    label="目标达成率"
                    v-model="score_input"
                    :rules="[
                      (u) =>
                        (isFinite(+u) && +u >= 0 && +u <= 101) ||
                        '请输入合法达成率',
                    ]"
                  ></v-text-field>
                </v-col>
                <v-col
                  v-if="
                    isFinite(+score_input) &&
                    +score_input >= 0 &&
                    +score_input <= 101 &&
                    note_total.Break
                  "
                >
                  达成{{ (+score_input).toFixed(4) }}%容错为{{
                    ((101 - +score_input) / 100 / (0.2 / score_max)).toFixed(3)
                  }}个Tap GREAT <br />
                  BREAK 50落相当于{{
                    (
                      (0.01 * 0.25) /
                      +note_total.Break /
                      (0.2 / score_max)
                    ).toFixed(3)
                  }}个Tap GREAT <br />
                  BREAK 粉2000相当于{{
                    (
                      (0.01 * 0.6) / +note_total.Break / (0.2 / score_max) +
                      5
                    ).toFixed(3)
                  }}个Tap GREAT
                </v-col>
              </v-row>
              <v-expansion-panels accordion>
                <v-expansion-panel>
                  <v-expansion-panel-header
                    ><span>绝赞分布计算 </span></v-expansion-panel-header
                  >
                  <v-expansion-panel-content>
                    <v-form ref="judge_form" v-model="judge_valid">
                      <v-row
                        no-gutters
                        v-for="(note_item, note) in notes"
                        :key="note"
                        class="mt-0"
                      >
                        <v-col
                          class="col-score-table"
                          v-for="(judge_item, judge) in judges_full"
                          :key="judge"
                          ><v-text-field
                            dense
                            :background-color="judges_full[judge].color"
                            v-model="judge_input[note][judge]"
                            :label="note_item.short + ' ' + judge_item.short"
                            :disabled="
                              !manual_input &&
                              (judge == 'CRITICAL_PERFECT' ||
                                (judge == 'PERFECT' && note != 'Break'))
                            "
                            :rules="[
                              (u) =>
                                (isFinite(+u) && +u >= 0 && !(+u % 1)) ||
                                '请输入0或正整数',
                            ]"
                          ></v-text-field
                        ></v-col>
                      </v-row>
                    </v-form>
                    <v-row class="mt-0 align-center">
                      <v-checkbox
                        label="手动填充所有栏"
                        v-model="manual_input"
                      ></v-checkbox>
                      <v-spacer />
                      <v-btn color="primary" @click="calc_break_distribution"
                        >计算可能的绝赞分布</v-btn
                      >
                    </v-row>
                    <v-data-table
                      class="mt-2"
                      dense
                      :headers="total_list_headers"
                      :items-per-page="10"
                      :footer-props="{ 'items-per-page-options': [10, -1] }"
                      :items="total_list"
                      item-key="id"
                      no-data-text="没有符合条件的结果"
                    >
                      <template #item.total_score="{ item }">
                        {{ item.total_score.toFixed(8) }}%
                      </template></v-data-table
                    >
                  </v-expansion-panel-content>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-container>
          </v-tab-item>
          <v-tab-item key="rating">
            <v-container class="pa-1">
              <v-radio-group v-model="rating_mode" row>
                <v-radio label="按定数计算" value="from_ds"></v-radio>
                <v-radio
                  label="按达成率计算"
                  value="from_achievements"
                ></v-radio>
                <v-radio label="按Rating计算" value="from_rating"></v-radio>
              </v-radio-group>
              <v-text-field
                v-if="rating_mode == 'from_ds'"
                label="定数"
                v-model="ds_input"
                :rules="[
                  (u) =>
                    (isFinite(+u) && +u >= 0 && +u <= 15) || '请输入合法数据',
                ]"
              ></v-text-field>
              <v-text-field
                v-else-if="rating_mode == 'from_achievements'"
                label="达成率"
                v-model="achievements_input"
                :rules="[
                  (u) =>
                    (isFinite(+u) && +u >= 0 && +u <= 101) || '请输入合法数据',
                ]"
              ></v-text-field>
              <v-text-field
                v-else
                label="目标Rating"
                v-model="rating_input"
                :rules="[
                  (u) =>
                    (isFinite(+u) && +u >= 0 && +u <= 300) || '请输入合法数据',
                ]"
              ></v-text-field>
              <v-data-table
                class="mt-2"
                dense
                :headers="rating_list_headers"
                :items-per-page="-1"
                :items="rating_list"
                hide-default-footer
                sort-by="achievements"
                sort-desc
                item-key="id"
                no-data-text="没有符合条件的结果"
                mobile-breakpoint="0"
              >
                <template #item.ds="{ item }">
                  {{ item.ds.toFixed(1) }}
                </template>
                <template #item.achievements="{ item }">
                  {{ item.achievements.toFixed(4) }}%
                </template></v-data-table
              >
            </v-container>
          </v-tab-item>
        </v-tabs-items>
      </v-card-text>
      <v-footer v-if="current_song">
        <v-card-subtitle class="pa-1">
          当前为
          <i
            >{{ current_song.type == "DX" ? "[DX] " : ""
            }}<b>{{ current_song.title }}</b> [{{
              current_song.level_label
            }}]</i
          >
          的数据
        </v-card-subtitle>
      </v-footer>
    </v-card>
  </v-dialog>
</template>

<script>
import watchVisible from '../plugins/watchVisible';
export default {
  data: () => {
    return {
      visible: false,
      tab: "",
      current_song: false,
      manual_input: false,
      note_total: {
        Tap: 0,
        Hold: 0,
        Slide: 0,
        Touch: 0,
        Break: 0,
      },
      notes: {
        Tap: { weight: 1, short: "Ta." },
        Hold: { weight: 2, short: "Ho." },
        Slide: { weight: 3, short: "Sl." },
        Touch: { weight: 1, short: "To." },
        Break: { weight: 5, short: "Br." },
      },
      judges: {
        PERFECT: { weight: 1, color: "orange" },
        GREAT: { weight: 0.8, color: "pink lighten-1" },
        GOOD: { weight: 0.5, color: "green" },
        MISS: { weight: 0, color: "grey" },
      },
      judges_full: {
        CRITICAL_PERFECT: { weight: 1, short: "CP", color: "amber lighten-1" },
        PERFECT: { weight: 1, short: "PF", color: "orange lighten-1" },
        GREAT: { weight: 0.8, short: "GR", color: "pink lighten-2" },
        GOOD: { weight: 0.5, short: "GD", color: "green lighten-1" },
        MISS: { weight: 0, short: "MS", color: "grey lighten-1" },
      },
      break_judges: {
        CRITICAL_PERFECT: { weight: 1, ex_weight: 1, color: "amber" },
        PERFECT: { weight: 1, ex_weight: 0, color: "orange" },
        PERFECT_A: { weight: 1, ex_weight: 0.75, color: "orange" },
        PERFECT_B: { weight: 1, ex_weight: 0.5, color: "orange" },
        GREAT: { weight: 0, ex_weight: 0.4, color: "pink lighten-1" },
        GREAT_A: { weight: 0.8, ex_weight: 0.4, color: "pink lighten-1" },
        GREAT_B: { weight: 0.6, ex_weight: 0.4, color: "pink lighten-1" },
        GREAT_C: { weight: 0.5, ex_weight: 0.4, color: "pink lighten-1" },
        GOOD: { weight: 0.4, ex_weight: 0.3, color: "green" },
        MISS: { weight: 0, ex_weight: 0, color: "grey" },
      },
      score_mode: { name: "0+", score: 0, ex_score: 0 },
      score_modes: [
        { name: "0+", score: 0, ex_score: 0 },
        { name: "100-", score: 1, ex_score: 0 },
        { name: "101-", score: 1, ex_score: 1 },
      ],
      score_input: "",
      judge_input: {
        Tap: { CRITICAL_PERFECT: 0, PERFECT: 0, GREAT: 0, GOOD: 0, MISS: 0 },
        Hold: { CRITICAL_PERFECT: 0, PERFECT: 0, GREAT: 0, GOOD: 0, MISS: 0 },
        Slide: { CRITICAL_PERFECT: 0, PERFECT: 0, GREAT: 0, GOOD: 0, MISS: 0 },
        Touch: { CRITICAL_PERFECT: 0, PERFECT: 0, GREAT: 0, GOOD: 0, MISS: 0 },
        Break: { CRITICAL_PERFECT: 0, PERFECT: 0, GREAT: 0, GOOD: 0, MISS: 0 },
      },
      judge_valid: false,
      total_list: [],
      total_list_headers: [
        { text: "达成率", value: "total_score" },
        { text: "PF (0.75%)", value: "PERFECT_A" },
        { text: "PF (0.5%)", value: "PERFECT_B" },
        { text: "GR (2000)", value: "GREAT_A" },
        { text: "GR (1500)", value: "GREAT_B" },
        { text: "GR (1250)", value: "GREAT_C" },
      ],
      rating_mode: "from_ds",
      ds_input: "",
      rating_input: "",
      achievements_input: "",
      rating_list_headers: [
        { text: "定数", value: "ds" },
        { text: "达成率", value: "achievements" },
        { text: "Rating", value: "rating" },
      ],
    };
  },
  methods: {
    clear_current_song: function () {
      this.current_song = false;
    },
    update_judge_input: function () {
      if (!this.manual_input) {
        for (let note in this.notes) {
          let CP = this.note_total[note];
          for (let judge in this.judges_full)
            if (judge != "CRITICAL_PERFECT")
              CP -= this.judge_input[note][judge];
          this.judge_input[note]["CRITICAL_PERFECT"] = CP;
        }
      } else {
        for (let note in this.notes) {
          let sum = 0;
          for (let judge in this.judges_full)
            sum += +this.judge_input[note][judge];
          this.note_total[note] = sum;
          this.clear_current_song();
        }
      }
    },
    calc_break_distribution: function () {
      if (!this.$refs.judge_form.validate()) {
        this.total_list = [];
        this.$message.error("判定表数据不合法！");
        return;
      }

      // PERFECT_A: 0.75% extra
      // PERFECT_B: 0.5% extra
      let PF_list = [];
      for (
        let PERFECT_A = 0;
        PERFECT_A <= +this.judge_input.Break.PERFECT;
        PERFECT_A++
      ) {
        let PERFECT_B = +this.judge_input.Break.PERFECT - PERFECT_A;
        PF_list.push({ PERFECT_A, PERFECT_B });
      }

      // GREAT_A: 2000/2500 base
      // GREAT_B: 1500/2500 base
      // GREAT_C: 1250/2500 base
      let GR_list = [];
      for (let GREAT_A = 0; GREAT_A <= +this.judge_input.Break.GREAT; GREAT_A++)
        for (
          let GREAT_B = 0;
          GREAT_A + GREAT_B <= +this.judge_input.Break.GREAT;
          GREAT_B++
        ) {
          let GREAT_C = +this.judge_input.Break.GREAT - GREAT_A - GREAT_B;
          GR_list.push({ GREAT_A, GREAT_B, GREAT_C });
        }

      let base_score = 0,
        extra_score = 0;

      for (let note in this.notes)
        for (let judge in this.judges_full) {
          if (note == "Break") {
            base_score +=
              +this.judge_input[note][judge] *
              this.notes[note].weight *
              this.break_judges[judge].weight;
            extra_score +=
              this.judge_input[note][judge] *
              this.break_judges[judge].ex_weight;
          } else {
            base_score +=
              +this.judge_input[note][judge] *
              this.notes[note].weight *
              this.judges_full[judge].weight;
          }
        }

      let total_list = [],
        id = 0;
      for (let { PERFECT_A, PERFECT_B } of PF_list)
        for (let { GREAT_A, GREAT_B, GREAT_C } of GR_list) {
          let base_score_ =
            base_score + GREAT_A * 4 + GREAT_B * 3 + GREAT_C * 2.5;
          let extra_score_ = extra_score + PERFECT_A * 0.75 + PERFECT_B * 0.5;
          let total_score =
            (base_score_ / this.score_max) * 100 +
            extra_score_ / this.ex_score_max;
          if (
            !(
              isFinite(+this.score_input) &&
              +this.score_input >= 0 &&
              this.score_input !== ""
            ) ||
            Math.abs(total_score - +this.score_input) <= 0.0001
          ) {
            total_list.push({
              id,
              total_score,
              PERFECT_A,
              PERFECT_B,
              GREAT_A,
              GREAT_B,
              GREAT_C,
            });
            id++;
          }
        }
      total_list.sort((a, b) => b.total_score - a.total_score);
      if (total_list.length) {
        this.$message.success(`计算完成，共找到${total_list.length}条结果`);
      } else {
        this.$message.warning(`计算完成，未找到符合条件的结果`);
      }
      this.total_list = total_list;
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
    fill(item) {
      Object.assign(this.note_total, item.note_total);
      this.current_song = item.current_song;
      this.ds_input = item.current_song.ds;
      this.rating_input = item.current_song.ra;
      this.achievements_input = item.current_song.achievements;
      this.visible = item.visible;
      this.manual_input = false;
      for (let note in this.notes)
        for (let judge in this.judges_full)
          this.judge_input[note][judge] =
            judge == "CRITICAL_PERFECT" ? this.note_total[note] : 0;
    },
  },
  watch: {
    visible: watchVisible("visible", "Calculators"),
    note_total: {
      handler() {
        if (!this.manual_input) this.update_judge_input();
      },
      deep: true,
    },
    judge_input: {
      handler() {
        this.update_judge_input();
      },
      deep: true,
    },
    manual_input: function () {
      if (!this.manual_input) {
        for (let note in this.notes)
          if (note != "Break") {
            this.judge_input[note]["CRITICAL_PERFECT"] =
              +this.judge_input[note]["CRITICAL_PERFECT"] +
              +this.judge_input[note]["PERFECT"];
            this.judge_input[note]["PERFECT"] = 0;
          }
      }
    },
  },
  computed: {
    score_max: function () {
      let sum = 0;
      for (let note in this.notes)
        sum += +this.note_total[note] * this.notes[note].weight;
      return sum;
    },
    ex_score_max: function () {
      return +this.note_total.Break;
    },
    score_normal: function () {
      let score_normal = {};
      for (let note in this.notes)
        if (note != "Break") {
          score_normal[note] = {};
          for (let judge in this.judges) {
            if (!+this.note_total[note]) {
              score_normal[note][judge] = "-";
              continue;
            }
            score_normal[note][judge] =
              (this.notes[note].weight *
                (this.judges[judge].weight - this.score_mode.score)) /
              this.score_max;
            score_normal[note][judge] =
              (score_normal[note][judge] * 100).toFixed(7) + "%";
          }
        }
      return score_normal;
    },
    score_break: function () {
      let score_break = {};
      for (let judge in this.break_judges) {
        if (!this.ex_score_max) {
          score_break[judge] = "-";
          continue;
        }
        score_break[judge] =
          (this.notes["Break"].weight *
            (this.break_judges[judge].weight - this.score_mode.score)) /
            this.score_max +
          (0.01 *
            (this.break_judges[judge].ex_weight - this.score_mode.ex_score)) /
            this.ex_score_max;
        score_break[judge] = (score_break[judge] * 100).toFixed(7) + "%";
      }
      return score_break;
    },
    rating_list: function () {
      if (this.rating_mode == "from_ds") {
        if (this.ds_input === "") return [];
        let ds = +this.ds_input;
        let min_idx = 5;
        let min_ach4 = Math.round(this.get_min_ach(min_idx) * 10000);
        let max_idx = 13;
        let max_ach4 = Math.round(this.get_min_ach(max_idx + 1) * 10000);
        let more_ra = [];
        for (
          let curr_ach4 = min_ach4;
          curr_ach4 < max_ach4;
          curr_ach4 += 2500
        ) {
          // console.log(curr_ach4, JSON.stringify(more_ra));
          let curr_min_ra = this.get_ra(ds, curr_ach4 / 10000);
          if (curr_min_ra > this.get_ra(ds, (curr_ach4 - 1) / 10000)) {
            more_ra.push({
              ds: ds,
              achievements: curr_ach4 / 10000,
              rating: curr_min_ra,
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
            more_ra.push({
              ds: ds,
              achievements: ans / 10000,
              rating: curr_max_ra,
            });
          }
        }
        more_ra.sort((a, b) => b.achievements - a.achievements);
        return more_ra;
      } else if (this.rating_mode == "from_rating") {
        if (this.rating_input === "") return [];
        let rating = +this.rating_input;
        let more_ra = [];
        for (let ds1 = 10; ds1 <= 150; ds1++) {
          let ds = ds1 / 10;
          if (this.get_ra(ds, 101) < rating) continue;
          let l = 0,
            r = 1010000,
            ans = r;
          while (r >= l) {
            let mid = Math.floor((r + l) / 2);
            if (this.get_ra(ds, mid / 10000) >= rating) {
              ans = mid;
              r = mid - 1;
            } else {
              l = mid + 1;
            }
          }
          if (
            !more_ra.length ||
            Math.round(more_ra[more_ra.length - 1].achievements * 10000) != ans
          )
            more_ra.push({
              ds: ds,
              achievements: ans / 10000,
              rating: this.get_ra(ds, ans / 10000),
            });
        }
        more_ra.sort((a, b) => b.achievements - a.achievements);
        return more_ra;
      } else if (this.rating_mode == "from_achievements") {
        if (this.achievements_input === "") return [];
        let more_ra = [];
        for (let ds1 = 10; ds1 <= 150; ds1++) {
          let ds = ds1 / 10;
          more_ra.push({
            ds: ds,
            achievements: +this.achievements_input,
            rating: this.get_ra(ds, +this.achievements_input),
          });
        }
        more_ra.sort((a, b) => b.ds - a.ds);
        return more_ra;
      }
      return [];
    },
  },
};
</script>

<style>
.col-score-table {
  width: 20%;
  word-break: break-all;
}
</style>
