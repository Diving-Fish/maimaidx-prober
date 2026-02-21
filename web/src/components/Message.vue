<template>
  <v-card id="tdMessage">
    <v-card-title> 今日留言 </v-card-title>
    <v-card-subtitle class="pb-0"> 吹水，扩列，或者……？ </v-card-subtitle>
    <v-window v-model="window" class="elevation-1" style="margin: 12px 12px">
      <v-window-item v-for="message in messages" :key="message.message">
        <v-card flat style="padding: 12px">
          <strong style="font-size: 16px">{{
            message.nickname ? message.nickname : message.username
          }}</strong>
          <v-card-text style="padding: 4px">
            {{ message.text }}
          </v-card-text>
          <v-card-actions style="display: flex; justify-content: space-between">
            <v-btn icon small :disabled="window == 0" @click="window--">
              <v-icon>mdi-chevron-left</v-icon>
            </v-btn>
            <v-btn
              icon
              small
              :disabled="window == messages.length - 1"
              @click="window++"
            >
              <v-icon>mdi-chevron-right</v-icon>
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-window-item>
    </v-window>
    <div style="display: flex; padding: 0 12px 12px 12px">
      <v-form ref="msgForm" style="width: 100%">
        <v-text-field
          dense
          placeholder="说两句..."
          :rules="[
            (u) => !!u || '可不能空着噢',
            (u) => u.length <= 60 || '一条消息最多发送 60 个字符',
          ]"
          v-model="buffer"
        >
        </v-text-field>
      </v-form>
      <v-dialog
        v-model="vsb"
        :fullscreen="$vuetify.breakpoint.mobile"
        width="500"
      >
        <v-card>
          <v-card-title>
            要使用什么样的马甲呢？
            <v-spacer />
            <v-btn icon @click="vsb = false">
              <v-icon>mdi-close</v-icon>
            </v-btn>
            <v-form ref="msgNickForm" style="width: 100%">
              <v-text-field
                label="马甲"
                placeholder="空着的话会用你的用户名"
                :rules="[(u) => u.length <= 20 || '马甲最多长 20 个字符']"
                v-model="nickname"
              >
              </v-text-field>
            </v-form>
          </v-card-title>

          <v-card-actions>
            <v-spacer />
            <v-btn icon @click="sumbitMessage()">
              <v-icon>mdi-comment-outline</v-icon>
            </v-btn>
          </v-card-actions>
        </v-card>
        <template #activator="{ on, attrs }">
          <v-btn icon small class="ml-3" v-on="on" v-bind="attrs">
            <v-icon>mdi-comment-outline</v-icon>
          </v-btn>
        </template>
      </v-dialog>
    </div>
    <div id="tdMessageFoot">
    </div>
  </v-card>
</template>

<script>
import axios from "axios";
import watchVisible from '../plugins/watchVisible';
export default {
  data: function () {
    return {
      messages: [],
      window: 0,
      buffer: "",
      vsb: false,
      nickname: ""
    };
  },
  created: function () {
    this.getMessages();
  },
  watch: {
    vsb: watchVisible("vsb", "Message"),
    window() {
      this.resize();
    }
  },
  methods: {
    sumbitMessage: function() {
      if (!this.$refs.msgNickForm.validate()) return;
      this.vsb = false;
      if (!this.$refs.msgForm.validate()) return;
      axios.post("/api/maimaidxprober/message", {
          "nickname": this.nickname,
          "text": this.buffer
      }).then(resp => {
          this.messages = resp.data.sort((a, b) => {return b.ts - a.ts});
          this.window = this.messages.length - 1;
          this.resize();
      })
      this.buffer = "";
      this.nickname = "";
    },
    getMessages: function() {
      axios.get("/api/maimaidxprober/message").then((resp) => {
        this.messages = resp.data;
        this.resize();
      });
    },
    resize() {
      const that = this;
      setTimeout(function() {that.$emit('resize')}, 150);
    }
  },
};
</script>

<style>
</style>