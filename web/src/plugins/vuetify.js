import Vue from 'vue';
import Vuetify from 'vuetify/lib/framework';

Vue.use(Vuetify);

import zhHans from 'vuetify/lib/locale/zh-Hans'

export default new Vuetify({
    lang: {
        locales: { zhHans },
        current: 'zhHans'
    }
});
