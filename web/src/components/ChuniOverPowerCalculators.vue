<template>
  <v-dialog v-model="visible" :fullscreen="$vuetify.breakpoint.mobile" :width="700">
    <template #activator="{ on, attrs }">
      <v-btn class="mt-3 mr-4" v-bind="attrs" v-on="on">单曲 OP 计算器</v-btn>
    </template>
    <v-card>
      <v-card-title>单曲 OVER POWER 计算器
        <v-spacer/>
        <v-btn icon @click="visible = false">
          <v-icon>mdi-close</v-icon>
        </v-btn>
        <v-container class="pa-1">
          <v-text-field label="定数" v-model="ds_input" :rules="[
                  (u) =>
                    (isFinite(+u) && +u >= 0 && +u <= 15.5) || '请输入合法数据',
                ]"></v-text-field>
          <v-text-field label="分数" v-model="score_input" :rules="[
                  (u) =>
                    (isFinite(+u) && +u >= 0 && +u <= 1010000) || '请输入合法数据',
                ]"></v-text-field>
          <v-container class="pa-0">
            <v-radio-group v-model="combo_status" row>
              <v-radio label="已完成" value="finished"></v-radio>
              <v-radio label="已达成 FULL COMBO" value="full_combo"></v-radio>
              <v-radio label="已达成 ALL JUSTICE" value="all_justice"></v-radio>
              <v-radio label="已理论" value="all_justice_critical"></v-radio>
            </v-radio-group>
            <v-row no-gutters>
              <v-col cols="2">
                <v-btn @click="calculateOP">计算</v-btn>
              </v-col>
              <v-col cols="2">
                <v-btn @click="clear">清空</v-btn>
              </v-col>
              <v-col cols="3">
                <p class="text-md-body-1">计算结果：{{ calc_result }}</p>
              </v-col>
            </v-row>
          </v-container>
        </v-container>
      </v-card-title>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  data: () => {
    return {
      visible: false,
      ds_input: "",
      score_input: "",
      combo_status: "finished",
      calc_result: "0",
    }
  },
  methods: {
    clear() {
      this.ds_input = "";
      this.score_input = "";
      this.combo_status = "finished";
      this.calc_result = "0";
    },
    calculateOP() {
      let result = 0;
      switch (true) {
        case this.score_input >=1007500:
          result = (Number(this.ds_input)+2)*5+(this.score_input-1007500)*0.0015;
          switch (true) {
            case this.combo_status === "full_combo":
              result += 0.5;
              break;
            case this.combo_status === "all_justice":
              result += 0.5+0.5;
              break;
            case this.combo_status === "all_justice_critical":
              result += 0.5+0.5+0.25;
              break;
          }
          break;
        case this.score_input >=975000:
          result = this.raCalculate(Number(this.ds_input),Number(this.score_input))*5;
          break;
        default:
          result = 0;
      }
      this.calc_result = result;
    },
    raCalculate: function(ds,score) {
      let result = 0;
      switch (true) {
        case score >= 1009000:
          result = ds+2.15;
          break;
        case score >= 1007500:
          result = ds+2+parseInt((score-1007500)/100)*0.01;
          break;
        case score >= 1005000:
          result = ds+1.5+parseInt((score-1005000)/500)*0.1;
          break;
        case score >= 1000000:
          result = ds+1+parseInt((score-1000000)/1000)*0.1;
          break;
        case score >= 975000:
          result = ds+parseInt((score-975000)/2500)*0.1;
          break;
        case score >= 925000:
          result = ds-3;
          break;
        case score >= 900000:
          result = ds-5;
          break;
        case score >= 800000:
          result = (ds-5)/2;
          break;
        default:
          result = 0;
          break;
      }
      return result;
    }
  },
  name: "ChuniOverPowerCalculators"
}
</script>

<style scoped>

</style>