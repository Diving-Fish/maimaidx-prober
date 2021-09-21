<template>
  <div>
    <div class="hdr" v-if="login">
      {{ username }}，欢迎回来
      <v-dialog
        v-model="visible"
        width="600"
        :fullscreen="$vuetify.breakpoint.mobile"
      >
        <template #activator="{ on, attrs }">
          <v-btn v-on="on" v-bind="attrs" class="ml-3"> 编辑个人资料 </v-btn>
        </template>
        <v-card>
          <v-card-title>
            个人资料
            <v-spacer />
            <v-btn icon @click="visible = false">
              <v-icon>mdi-close</v-icon>
            </v-btn>
          </v-card-title>
          <v-form style="padding: 12px 24px" ref="profile" v-model="valid">
            <v-text-field
              label="昵称"
              v-model="nickname"
              counter="8"
              :rules="[
                (u) => !!u || '昵称不能为空',
                (u) => u.length <= 8 || '昵称不能超过 8 个字符',
              ]"
            ></v-text-field>
            <v-text-field label="绑定 QQ 号" v-model="bind_qq"
              ><template v-slot:prepend>
                <v-tooltip bottom>
                  <template v-slot:activator="{ on }">
                    <v-icon v-on="on"> mdi-help-circle-outline </v-icon>
                  </template>
                  绑定 QQ 号后，您可以直接输入 b40 以在千雪 bot
                  查询您自己的成绩。
                </v-tooltip>
              </template></v-text-field
            >
            <v-row align="center">
              <v-col cols="3">
                <v-subheader> 段位 </v-subheader>
              </v-col>
              <v-col cols="9">
                <v-select
                  v-model="select"
                  :items="ratings"
                  item-text="label"
                  item-value="ra"
                  :hint="`段位分为 ${select.ra}`"
                  persistent-hint
                  return-object
                  single-line
                ></v-select>
              </v-col>
            </v-row>
            <v-row align="center">
              <v-col cols="3">
                <v-subheader> 牌子设置 </v-subheader>
              </v-col>
              <v-col vols="5">
                <v-select
                  v-model="plate_upload.version"
                  :items="versions"
                ></v-select>
              </v-col>
              <v-col vols="4">
                <v-select
                  v-show="plate_upload.version != '无'"
                  v-model="plate_upload.plate_type"
                  :items="this.current_item"
                  item-text="label"
                  item-value="value"
                  :hint="(plate_upload.version && plate_upload.plate_type) ? `${v2n[plate_upload.version]}${t2n[plate_upload.plate_type]}` : ''"
                  persistent-hint
                ></v-select>
              </v-col>
            </v-row>
            <v-checkbox v-model="privacy" label="禁止其他人查询我的成绩" />
            <v-dialog
              v-model="delVisible"
              width="600"
              :fullscreen="$vuetify.breakpoint.mobile"
            >
              <template #activator="{ on, attrs }">
                <v-btn v-on="on" v-bind="attrs" color="warning">
                  删除所有数据
                </v-btn>
              </template>
              <v-card>
                <v-card-title>删除数据</v-card-title>
                <v-card-text>
                  您确定要删除您的所有数据记录吗？您仍可以再次通过数据导入重新导入数据。
                </v-card-text>
                <v-card-actions class="pb-4">
                  <v-btn color="warning" @click="delete_records()">确定</v-btn>
                  <v-btn @click="visible = false">取消</v-btn>
                </v-card-actions>
              </v-card>
            </v-dialog>
          </v-form>
          <v-card-actions class="pb-4">
            <v-btn color="primary" @click="submit">保存</v-btn>
            <v-btn @click="visible = false">取消</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </div>
  </div>
</template>

<script>
import axios from "axios";
export default {
  props: {
    available_plates: Function,
  },
  data: () => {
    return {
      valid: false,
      login: false,
      username: "",
      visible: false,
      delVisible: false,
      select: { label: "真传拾段", ra: 2100 },
      ratings: [
        { label: "初学者", ra: 0 },
        { label: "实习生", ra: 250 },
        { label: "初出茅庐", ra: 500 },
        { label: "修行中", ra: 750 },
        { label: "初段", ra: 1000 },
        { label: "二段", ra: 1200 },
        { label: "三段", ra: 1400 },
        { label: "四段", ra: 1500 },
        { label: "五段", ra: 1600 },
        { label: "六段", ra: 1700 },
        { label: "七段", ra: 1800 },
        { label: "八段", ra: 1850 },
        { label: "九段", ra: 1900 },
        { label: "十段", ra: 1950 },
        { label: "真传", ra: 2000 },
        { label: "真传壹段", ra: 2010 },
        { label: "真传贰段", ra: 2020 },
        { label: "真传叁段", ra: 2030 },
        { label: "真传肆段", ra: 2040 },
        { label: "真传伍段", ra: 2050 },
        { label: "真传陆段", ra: 2060 },
        { label: "真传柒段", ra: 2070 },
        { label: "真传捌段", ra: 2080 },
        { label: "真传玖段", ra: 2090 },
        { label: "真传拾段", ra: 2100 },
      ],
      bind_qq: "",
      nickname: "",
      privacy: false,
      plate: "",
      plate_upload: {
        version: "无",
        plate_type: 0,
      },
      v2n: {},
      plates_info: {},
      versions_src: [
        "maimai PLUS",
        "maimai GreeN",
        "maimai GreeN PLUS",
        "maimai ORANGE",
        "maimai ORANGE PLUS",
        "maimai PiNK",
        "maimai PiNK PLUS",
        "maimai MURASAKi",
        "maimai MURASAKi PLUS",
        "maimai MiLK",
        "MiLK PLUS",
        "maimai FiNALE",
        "maimai でらっくす",
      ],
      t2n: { 1: "極", 2: "将", 4: "舞舞", 8: "神", "神": 8, "舞舞": 4, "将": 2, "極": 1},
      versions: []
    };
  },
  watch: {
    visible: function () {
      this.plates_info = this.available_plates();
      this.versions = ["无"].concat(this.versions_src.filter(elem => {return this.plates_info[elem] > 0}))
    },
    'plate_upload.version': function(to) {
      if (!(to in this.plates_info)) return;
      if ((this.plates_info[to] & this.plate_upload.plate_type) == 0)
        this.plate_upload.plate_type = 0;
    }
  },
  computed: {
    current_item() {
      let items = [];
      for (const i of [1, 2, 4, 8]) {
        if (this.plates_info[this.plate_upload.version] & i) {
          items.push({ value: i, label: this.t2n[i] });
          //console.log(items)
        }
      }
      return items;
    },
  },
  methods: {
    submit() {
      if (!this.$refs.profile.validate()) return;
      axios
        .post("https://www.diving-fish.com/api/maimaidxprober/player/profile", {
          username: this.username,
          privacy: this.privacy,
          bind_qq: this.bind_qq,
          additional_rating: this.select.ra,
          nickname: this.nickname,
          plate: this.plate_upload,
        })
        .then((resp) => {
          this.visible = false;
          this.$message.success("修改成功");
          this.username = resp.data.username;
          this.privacy = resp.data.privacy;
          this.bind_qq = resp.data.bind_qq;
          for (let elem of this.ratings) {
            if (elem.ra == resp.data.additional_rating) {
              this.select = elem;
              break;
            }
          }
          this.nickname = resp.data.nickname;
        });
    },
    delete_records() {
      axios
        .delete(
          "https://www.diving-fish.com/api/maimaidxprober/player/delete_records"
        )
        .then((resp) => {
          this.$message.success("已删除" + resp.data.message + "条数据");
          setTimeout("window.location.reload()", 1500);
        });
    },
    fetch() {
      axios
        .get("https://www.diving-fish.com/api/maimaidxprober/player/profile")
        .then((resp) => {
          this.login = true;
          this.username = resp.data.username;
          this.privacy = resp.data.privacy;
          this.bind_qq = resp.data.bind_qq;
          this.ra = resp.data.additional_rating;
          this.plate = resp.data.plate;
          this.nickname = resp.data.nickname;
          for (let elem of this.ratings) {
            if (elem.ra == resp.data.additional_rating) {
              this.select = elem;
              break;
            }
          }
          if (this.plate) {
            this.plate_upload.version = this.v2n[this.plate[0]];
            this.plate_upload.plate_type = this.t2n[this.plate.substr(1)];
          }
        })
        .catch(() => {});
    },
  },
  created: function () {
    for (const elem of [
      ["maimai PLUS", "真"],
      ["maimai GreeN", "超"],
      ["maimai GreeN PLUS", "檄"],
      ["maimai ORANGE", "橙"],
      ["maimai ORANGE PLUS", "暁"],
      ["maimai PiNK", "桃"],
      ["maimai PiNK PLUS", "櫻"],
      ["maimai MURASAKi", "紫"],
      ["maimai MURASAKi PLUS", "菫"],
      ["maimai MiLK", "白"],
      ["MiLK PLUS", "雪"],
      ["maimai FiNALE", "輝"],
      ["maimai でらっくす", "熊"],
      ["maimai でらっくす PLUS", "華"],
      ["maimai でらっくす Splash", "爽"],
    ]) {
      this.v2n[elem[1]] = elem[0];
      this.v2n[elem[0]] = elem[1];
    }
    this.fetch();
  },
};
</script>

<style scoped>
.hdr {
  display: flex;
  align-items: center;
}
</style>