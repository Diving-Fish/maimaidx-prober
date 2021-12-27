import Vue from 'vue';
import { Dialog, Message } from 'element-ui';
import App from './App.vue';
import vuetify from './plugins/vuetify';
import store from './plugins/vuex';

Vue.use(Dialog);

Vue.prototype.$message = Message;

Vue.config.productionTip = false

new Vue({
  vuetify,
  store: store,
  render: h => h(App)
}).$mount('#app')
