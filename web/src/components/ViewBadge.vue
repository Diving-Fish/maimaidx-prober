<template>
    <img v-if="raw_views != 0" :src="`https://img.shields.io/badge/views-${views}-blue`">
</template>

<script>
import axios from 'axios';
export default {
    name: "ViewBadge",
    data: function() {
        return {
            raw_views: 0
        }
    },
    computed: {
        views: function() {
            return this.raw_views.toLocaleString();
        }
    },
    mounted: function() {
        axios.get('https://www.diving-fish.com/api/maimaidxprober/count_view').then(resp => {
            this.raw_views = resp.data.views;
        })
    }
}
</script>

<style>

</style>