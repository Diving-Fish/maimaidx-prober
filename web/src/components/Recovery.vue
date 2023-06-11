<template>
  <v-dialog
    width="500px"
    :fullscreen="$vuetify.breakpoint.mobile"
    v-if="visible"
    v-model="open"
  >
    <template #activator="{ on, attrs }">
      <v-btn
        class="mt-3 mr-4"
        v-bind="attrs"
        v-on="on"
        >重置账户</v-btn
      >
    </template>
    <v-card>
      <v-card-title>
        重置账户
        <v-spacer />
        <v-btn icon @click="open = false">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      <v-card-subtitle>
        该功能仅限绑定 QQ 的账户使用，我们将会往您的 QQ 邮箱发送账户重置的邮件。
      </v-card-subtitle>
      <v-card-text>
        <v-text-field
          v-model="bind_qq"
          label="QQ号"
          :rules="[(u) => !!u || 'QQ号不能为空']"
        >
        </v-text-field>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn class="mr-4" color="primary" @click="execute">发送邮件</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import axios from 'axios';
export default {
  props: {
    visible: Boolean,
  },
  data: () => {
    return {
      open: false,
      bind_qq: ""
    }
  },
  methods: {
    execute: function() {
      axios.post("https://www.diving-fish.com/api/maimaidxprober/recovery?qq=" + this.bind_qq).then(() => {this.$message.success("邮件已发送")});
      this.open = false;
    }
  }
};
</script>

<style>
</style>