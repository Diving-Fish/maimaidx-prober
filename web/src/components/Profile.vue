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
            <v-checkbox v-model="privacy" label="禁止其他人查询我的成绩" />
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
  data: () => {
    return {
      valid: false,
      login: false,
      username: "",
      visible: false,
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
    };
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
  },
  created: function () {
    axios
      .get("https://www.diving-fish.com/api/maimaidxprober/player/profile")
      .then((resp) => {
        this.login = true;
        this.username = resp.data.username;
        this.privacy = resp.data.privacy;
        this.bind_qq = resp.data.bind_qq;
        this.ra = resp.data.additional_rating;
        for (let elem of this.ratings) {
          if (elem.ra == resp.data.additional_rating) {
            this.select = elem;
            break;
          }
        }
        this.nickname = resp.data.nickname;
      })
      .catch(() => {});
  },
};
</script>

<style scoped>
.hdr {
  display: flex;
  align-items: center;
}
</style>