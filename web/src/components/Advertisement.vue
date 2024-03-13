<template>
  <div>
    <v-carousel cycle v-if="$vuetify.breakpoint.mobile" height="auto">
      <v-carousel-item v-for="img in img_urls" :key="img.s">
        <img v-if="img.l == ''" :src="img.s" style="width: 100%">
        <a :href="img.l" v-else><img :src="img.s" style="width: 100%"></a>
      </v-carousel-item>
    </v-carousel>
    <v-carousel cycle v-else :style="`height: ${height}px; width: ${16 * height / 9}px`">
      <v-carousel-item v-for="img in img_urls" :key="img.s">
        <img v-if="img.l == ''" :src="img.s" style="width: 100%">
        <a :href="img.l" v-else><img :src="img.s" style="width: 100%"></a>
      </v-carousel-item>
    </v-carousel>
  </div>
</template>

<script>
import axios from "axios";
export default {
  data: () => {
    return {
      height: 0,
      img_urls: []
    }
  },
  mounted: function () {
    axios.get("https://www.diving-fish.com/api/maimaidxprober/advertisements").then((resp) => {
      this.img_urls = resp.data;
      this.resize();
    });
  },
  methods: {
    resize() {
      let height = 0;
      for (const b of document.getElementById("tdMessage").children) {
        height += b.clientHeight
      }
      this.height = height + 12;
    }
  }
}
</script>

<style>

</style>
