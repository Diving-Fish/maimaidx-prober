<template>
  <v-data-table :items-per-page="limit" :footer-props="{'items-per-page-options':[limit, -1]}" :headers="headers" :loading="loading" loading-text="加载中，请稍候……" :items="items" :search="search" sort-by="rank">
      <template #item.title="{ item }">
          {{ item.title }}
          <v-chip v-if="item.fc" :color="getFC(item.fc)" dark>{{ getName(item.fc) }}</v-chip>
          <v-chip v-if="item.fs" :color="getFS(item.fs)" dark>{{ getName(item.fs) }}</v-chip>
      </template>
      <template #item.level="{ item }">
          <v-chip :color="getLevel(item.level_index)" dark>
              {{ item.level_label }} {{ item.level }}
          </v-chip>
      </template>
      <template #item.achievements="{ item }">
          {{ item.achievements.toFixed(4)}}%
          <v-chip :color="getRate(item.rate)" outlined class="ml-1">{{ item.rate.replace('p', '+').toUpperCase() }}</v-chip>
      </template>
      <template #item.ra="{ item }">
          <span style="color: #4CAF50" v-if="item.rank <= limit">{{ item.ra }}</span>
          <span v-else>{{ item.ra }}</span>
      </template>
      <template #item.actions="{ item }">
          <v-icon small @click="$emit('edit', item)">mdi-pencil</v-icon>
      </template>
  </v-data-table>
</template>

<script>
export default {
    props: {
        items: Array,
        search: String,
        loading: Boolean,
        limit: Number
    },
    data: () => {
        return {
            headers: [
                {text: '排名', value: 'rank'},
                {text: '乐曲名', value: 'title'},
                {text: '难度', value: 'level'},
                {text: '定数', value: 'ds'},
                {text: '达成率', value: 'achievements'},
                {text: 'DX Rating', value: 'ra'}, 
                {text: '编辑', value: 'actions', sortable: false}
            ]
        }
    },
    watch: {
        search(n) {
            this.search = n
        }
    },
    methods: {
        getLevel(index) {
            console.log("invoke")
            return ['#22bb5b', '#fb9c2d', '#f64861','#9e45e2', '#ba67f8'][index]
        },
        getFC(str) {
            if (str.startsWith('fc')) return 'green'
            return 'orange'
        },
        getFS(str) {
            if (str.startsWith('fsd')) return 'orange'
            return 'blue'
        },
        getName(str) {
            const map = {
                'fc': 'FC',
                'fcp': 'FC+',
                'fs': 'FS',
                'fsp': 'FS+',
                'fsd': 'FSDX',
                'fsdp': 'FSDX+',
                'ap': 'AP',
                'app': 'AP+'
            }
            return map[str]
        },
        getRate(str) {
            if (str.startsWith('sssp')) return '#f85e5ed0'
            if (str.startsWith('sss')) return '#25bcf5d0'
            if (str.startsWith('ssp')) return '#fda609d0'
            return '#00000020'
        }
    }
}
</script>
