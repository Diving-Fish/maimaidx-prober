<template>
  <v-dialog width="500px" :fullscreen="$vuetify.breakpoint.mobile" v-if="visible" v-model="open">
    <template #activator="{ on, attrs }">
      <v-btn class="mt-3 mr-4" v-bind="attrs" v-on="on">投票箱</v-btn>
    </template>
    <v-card :loading="loading">
      <v-card-title>
        舞萌投票箱
        <v-tooltip bottom>
          <template #activator="{ on, attrs }">
            <v-icon v-bind="attrs" v-on="on">mdi-information</v-icon>
          </template>
          <span>投出你更喜欢的一首歌吧！<br>
          你可以喜欢它的谱面、它的音乐、它的一切！<br>
          如果你没有打过或者听过，请点击【跳过】~<br>
          如果你觉得两首歌都不行，你可以点击【给爷整乐了】</span>
        </v-tooltip>
        <v-spacer />
        <v-btn icon @click="open = false">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      <v-card-text>
        先别管投票箱了，来看看最新最热的<a href="/maimaidx/vote-2025">舞萌 DX 2025 人气乐曲投票</a>吧！
      </v-card-text>
      <v-card-actions class="mt-4">
        <v-checkbox v-model="auto_open" label="自动打开"></v-checkbox>
      </v-card-actions>
      <!-- <v-alert
        dense
        v-if="alert.message !== ''"
        :type="alert.type"
        class="ml-4 mr-4"
      >{{ alert.message }}</v-alert>
      <div v-if="remain > 0">
        <v-card-text v-if="$vuetify.breakpoint.mobile">
          <v-row>
            <v-col cols="8">
              <div style="text-align: center;">
                <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block;">{{ left_music.title }}</span>
              </div>
              <v-img :src="`https://www.diving-fish.com/covers/${padNumber(left_music.id)}.png`" aspect-ratio="1"></v-img>
            </v-col>
            <v-col cols="4" class="text-center" style="display: flex; align-items: center; justify-content: center;">
              <v-btn :disabled="loading" color="primary" @click="vote(1)">
                <v-icon>mdi-thumb-up</v-icon>
              </v-btn>
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="8">
              <div style="text-align: center;">
                <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block;">{{ right_music.title }}</span>
              </div>
              <v-img :src="`https://www.diving-fish.com/covers/${padNumber(right_music.id)}.png`" aspect-ratio="1"></v-img>
            </v-col>
            <v-col cols="4" class="text-center" style="display: flex; align-items: center; justify-content: center;">
              <v-btn :disabled="loading" color="primary" @click="vote(2)">
                <v-icon>mdi-thumb-up</v-icon>
              </v-btn>
            </v-col>
          </v-row>
          <v-card-actions class="mt-4">
            <v-checkbox v-model="auto_open" label="自动打开"></v-checkbox>
          </v-card-actions>
          <v-card-actions>
            <v-btn :disabled="loading" class="mr-4" @click="vote(0)">跳过</v-btn>
            <v-btn :disabled="loading" class="mr-4" color="warning" @click="vote(3)">给爷整乐了</v-btn>
          </v-card-actions>
        </v-card-text>
        <v-card-text v-if="!$vuetify.breakpoint.mobile">
          <v-row>
            <v-col cols="6" style="padding-bottom: 0">
              <div style="text-align: center;">
                <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block;">{{ left_music.title }}</span>
              </div>
            </v-col>
            <v-col cols="6" style="padding-bottom: 0">
              <div style="text-align: center;">
                <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block;">{{ right_music.title }}</span>
              </div>
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6">
              <v-img :src="`https://www.diving-fish.com/covers/${padNumber(left_music.id)}.png`" aspect-ratio="1"></v-img>
            </v-col>
            <v-col cols="6">
              <v-img :src="`https://www.diving-fish.com/covers/${padNumber(right_music.id)}.png`" aspect-ratio="1"></v-img>
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6" class="text-center">
              <v-btn :disabled="loading" color="primary" @click="vote(1)">
                <v-icon>mdi-thumb-up</v-icon>
              </v-btn>
            </v-col>
            <v-col cols="6" class="text-center">
              <v-btn :disabled="loading" color="primary" @click="vote(2)">
                <v-icon>mdi-thumb-up</v-icon>
              </v-btn>
            </v-col>
          </v-row>
          <v-card-actions class="mt-4">
            <v-checkbox v-model="auto_open" label="自动打开"></v-checkbox>
            <v-spacer />
            <v-btn :disabled="loading" class="mr-4" @click="vote(0)">跳过</v-btn>
            <v-btn :disabled="loading" class="mr-4" color="warning" @click="vote(3)">给爷整乐了</v-btn>
          </v-card-actions>
        </v-card-text>
      </div>
      <div v-if="remain <= 0" style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
        <span class="mb-4">投了五组啦，休息一下明天再来吧！</span>
        <a href="/maimaidx/vote-result" target="_blank">查看投票结果</a>
        <v-btn @click="getNewVote(true)" class="mt-2 mb-4">我偏要继续</v-btn>
      </div> -->
    </v-card>
  </v-dialog>
</template>

<script>
import axios from 'axios';
export default {
  props: {
    visible: Boolean,
    music_data: Object
  },
  data: () => {
    return {
      open: false,
      token: '',
      left_music: {id: '0'},
      right_music: {id: '0'},
      auto_open: true,
      remain: 5,
      loading: false,
      alert: {
        message: '',
        type: 'success'
      }
    }
  },
  watch: {
    music_data: function() {
      this.auto_open = !(localStorage.getItem('maiprober_vote_auto_open2') === 'false');
      this.remain = localStorage.getItem('maiprober_vote_remain');
      const timestamp = localStorage.getItem('maiprober_vote_timestamp');
      if (this.remain === null || timestamp === null || Date.now() - timestamp > 86400000) {
        this.remain = 5;
      }
      if (this.auto_open && this.remain > 0) {
        this.open = true;
      }
      this.getNewVote();
    },
    auto_open: function() {
      localStorage.setItem('maiprober_vote_auto_open2', this.auto_open);
    }
  },
  methods: {
    getNewVote: function(param) {
      if (param !== undefined)
      {
        this.remain = 5; 
      }
      axios.get("https://www.diving-fish.com/api/maimaidxprober/vote_box").then((response) => {
        this.left_music = this.music_data[response.data.left];
        this.right_music = this.music_data[response.data.right];
        this.token = response.data.token;
      });
    },

    vote: function(val) {
      this.loading = true;
      axios.post("https://www.diving-fish.com/api/maimaidxprober/vote_box", {
        token: this.token,
        vote: val
      }).then((response) => {
        const left_res = response.data.result[0];
        const right_res = response.data.result[1];
        if (val == 1) {
          this.alert.type = 'success';
          this.alert.message = `你投给了 ${this.left_music.title}， 它现在处于第 ${left_res} 位；与此同时，${this.right_music.title} 现在处于第 ${right_res} 位`;
        } else if (val == 2) {
          this.alert.type = 'success';
          this.alert.message = `你投给了 ${this.right_music.title}， 它现在处于第 ${right_res} 位；与此同时，${this.left_music.title} 现在处于第 ${left_res} 位`;
        } else if (val == 0) {
          this.alert.type = 'info';
          this.alert.message = `你似乎没有游玩过这些曲目呢~ 多做一些尝试吧！`;
        } else if (val == 3) {
          this.alert.type = 'success';
          this.alert.message = `你觉得 ${this.left_music.title} 和 ${this.right_music.title} 都不行！它们现在分别处于 ${left_res} 和 ${right_res} 位`;
        }
        this.remain -= 1;
        localStorage.setItem('maiprober_vote_remain', this.remain);
        localStorage.setItem('maiprober_vote_timestamp', Date.now());
        if (this.remain > 0) {
          this.getNewVote();
        } 
      }).catch(err => {
        this.$message.error(err.response.data.message);
        this.getNewVote();
      }).finally(() => {
        this.loading = false;
      });
    },
    
    padNumber: function(number) {
      return number.toString().padStart(5, '0')
    },
  }
};
</script>

<style></style>