import Vue from 'vue';
import Vuex from 'vuex';

Vue.use(Vuex);
const store = new Vuex.Store({
  state: {
    username: '',
    profile: {},
    music_data: [],
    music_data_dict: {},
    records: [],
    chart_stats: {},
    available_plates: () => {},

  },
  mutations: {
    change_username(state, username) {
      state.username = username
    },
    change_profile(state, obj) {
      state.profile = obj
    },
    change_music_data(state, obj) {
      state.music_data = obj;
      state.music_data_dict = state.music_data.reduce((acc, music) => {
        acc[music.id] = music;
        return acc;
      }, {});
    },
    change_records(state, obj) {
      state.records = obj
    },
    change_chart_stats(state, obj) {
      state.chart_stats = obj
    },
    merge_records(state, records) {
      let oldRecords = Object.fromEntries(
        state.records.map((r, i) => [+r.song_id * 10 + r.level_index, i])
      );
      for (let record of records) {
        let i = oldRecords[+record.song_id * 10 + record.level_index];
        if (typeof i != "undefined") {
          Vue.set(state.records, i, record);
        } else {
          state.records.push(record);
        }
      }
      // after merge, you also need compute record ra
    },
    set_available_plates(state, func) {
      state.available_plates = func
    }
  }
})

export default store;