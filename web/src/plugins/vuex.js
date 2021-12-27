import Vue from 'vue';
import Vuex from 'vuex';

Vue.use(Vuex);
const store = new Vuex.Store({
  state: {
    username: '',
    profile: {},
    music_data: [],
    records: []
  },
  mutations: {
    change_username(state, username) {
      state.username = username
    },
    change_profile(state, obj) {
      state.profile = obj
    },
    change_music_data(state, obj) {
      state.music_data = obj
    },
    change_records(state, obj) {
      state.records = obj
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
    }
  }
})

export default store;