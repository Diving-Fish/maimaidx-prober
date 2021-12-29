import axios from 'axios';
import store from '../plugins/vuex';
import { Message } from 'element-ui';

const DEBUG = false;

const api = {
  path: "https://www.diving-fish.com:8092/api/maimaidxprober/",
  login: function (form) {
    return new Promise((resolve, reject) => {
      axios
        .post(api.path + "login", {
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
    return new Promise((resolve, reject) => {
      axios
        .post(api.path + "register", {
          username: form.username,
          password: form.password,
          records: store.state.records,
        })
        .then((data) => {
          Message.success("注册成功，数据已同步完成");
          store.commit('change_username', form.username);
          resolve(data);
          // setTimeout("window.location.reload()", 1000);
        })
        .catch((err) => {
          Message.error("注册失败！");
          Message.error(err.response.data.message);
          reject(err);
        });
    })
  },
  fetch_all: function () {
    return new Promise((resolve, reject) => {
      axios
        .get(api.path + "music_data")
        .then((resp) => {
          store.commit("change_music_data", resp.data);
          Message.success(
            "乐曲信息获取完成，正在获取用户分数及相对难度信息……"
          );
          Promise.allSettled([
            axios.get(
              api.path + "chart_stats"
            ),
            axios.get(
              DEBUG
                ? api.path + "player/test_data"
                : api.path + "player/records"
            ),
          ]).then(([resp1, resp2]) => {
            if (resp1.status === "rejected") {
              Message.error("相对难度信息获取失败，请重新加载！");
              reject();
              return;
            }
            store.commit("change_chart_stats", resp1.value.data);
            if (resp2.status !== "rejected") {
              const data = resp2.value.data;
              store.commit('change_username', data.username);
              store.commit("merge_records", data.records);
              Message.success("用户分数及相对难度信息获取完成");
            } else {
              Message.warning("未获取用户分数");
            }
            resolve();
          });
        })
        .catch(() => {
          Message.error("乐曲信息获取失败，请重新加载！");
          reject();
        });
    })
  },
  fetch_records: function () {
    return new Promise((resolve, reject) => {
      axios
        .get(
          api.path + "player/records"
        )
        .then((resp) => {
          const data = resp.data;
          store.commit('change_username', data.username);
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
    return new Promise((resolve, reject) => {
      axios.get(
        api.path + "player/profile"
      ).then((resp) => {
        const data = resp.data;
        store.commit('change_profile', data);
        resolve(data);
      })
      .catch((err) => {
        reject(err);
      })
    })
  },
  upload_profile: function (payload) {
    return new Promise((resolve, reject) => {
      axios.post(
        api.path + "player/profile", payload
      ).then((resp) => {
        const data = resp.data;
        store.commit('change_profile', data);
        resolve(data);
      })
      .catch((err) => {
        reject(err);
      })
    })
  }
}

export default api;