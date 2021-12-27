import axios from 'axios';
import store from '../plugins/vuex';
import { Message } from 'element-ui';

const api = {
  login: function (form) {
    return new Promise((resolve, reject) => {
      axios
        .post("https://www.diving-fish.com/api/maimaidxprober/login", {
          username: form.username,
          password: form.password,
        })
        .then(() => {
          Message.success("登录成功，加载乐曲数据中……");
          this.fetch_profile();
          this.fetch_records();
          resolve();
        })
        .catch((err) => {
          Message.error("登录失败！");
          Message.error(err.response.data.message);
          reject(err);
        });
    })
  },
  register: function (form) {

  },
  fetch_music_data: function () {

  },
  fetch_records: function () {
    return new Promise((resolve, reject) => {
      axios
        .get(
          "https://www.diving-fish.com/api/maimaidxprober/player/records"
        )
        .then((resp) => {
          const data = resp.data;
          store.commit('change_username', username);
          store.commit('merge_records', data.records);
          resolve(data);
        })
        .catch((err) => {
          reject(err);
          Message.error("加载乐曲失败！");
        });
    })
  },
  fetch_profile: function () {

  }
}

export default api;