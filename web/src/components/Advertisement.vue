<template>
  <div>
    <v-carousel cycle v-if="$vuetify.breakpoint.mobile" height="auto">
      <v-carousel-item v-for="img in img_urls" :key="img">
        <img :src="img" style="width: 100%">
      </v-carousel-item>
    </v-carousel>
    <v-carousel cycle v-else :style="`height: ${height}px; width: ${16 * height / 9}px`">
      <v-carousel-item v-for="img in img_urls" :key="img">
        <img :src="img" style="width: 100%">
      </v-carousel-item>
    </v-carousel>
  </div>
</template>

<script>
export default {
  data: () => {
    return {
      height: 0,
      img_urls: [
        "https://www.diving-fish.com/maimaidx/prober/pic0.jpg",
        "https://www.diving-fish.com/maimaidx/prober/pic1.jpg"
      ]
    }
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