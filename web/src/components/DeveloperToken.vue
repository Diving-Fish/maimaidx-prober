<template>
  <v-dialog
    width="800px"
    :fullscreen="$vuetify.breakpoint.mobile"
    v-if="visible"
    v-model="open"
  >
    <template #activator="{ on, attrs }">
      <v-btn class="mt-3 mr-4" v-bind="attrs" v-on="on">开发者 Token</v-btn>
    </template>
    <v-card>
      <v-card-title class="headline">
        Token 列表
        <v-spacer />
        <v-btn icon @click="open = false">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      <v-card-text>
        <v-data-table :headers="headers" :items="items" class="elevation-1">
          <template v-slot:item.available="{ item }">
            <v-tooltip bottom>
              <template v-slot:activator="{ on, attrs }">
                <v-icon v-bind="attrs" v-on="on" :color="getColor(item)">
                  {{ getIcon(item) }}
                </v-icon>
              </template>
              <span>{{ getText(item) }}</span>
            </v-tooltip>
          </template>
          <template v-slot:item.level="{ item }">
            <span>{{
              item.level == 0 ? "" : level_items[item.level - 1].text
            }}</span>
          </template>
          <template v-slot:item.token="{ item }">
            <div style="display: flex; align-items: center">
              <span>{{ item.token }}</span>
              <v-tooltip bottom>
                <template v-slot:activator="{ on, attrs }">
                  <v-icon
                    v-bind="attrs"
                    v-on="on"
                    class="ml-2"
                    @click="copyToClipboard(item.token)"
                  >
                    mdi-content-copy
                  </v-icon>
                </template>
                <span>复制 Token</span>
              </v-tooltip>
            </div>
          </template>
        </v-data-table>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="openFormDialog">申请新 Token</v-btn>
      </v-card-actions>

      <v-dialog
        v-model="formDialog"
        max-width="600px"
        :fullscreen="$vuetify.breakpoint.mobile"
      >
        <v-card>
          <v-card-title class="headline">申请新 Token</v-card-title>
          <v-card-text>
            <v-form ref="form">
              <v-select
                v-model="newToken.level"
                :items="level_items"
                label="Token 等级"
                :rules="[(v) => !!v || 'Token 等级不能为空']"
                required
              ></v-select>
              <v-textarea
                v-model="newToken.reason"
                label="原因"
                rows="3"
                :rules="[(v) => !!v || '原因不能为空']"
                required
              ></v-textarea>
              <div style="display: flex; align-items: center">
                <v-file-input
                  v-model="newToken.pic"
                  label="上传图片"
                  multiple
                  show-size
                  accept=".jpg,.png"
                  required
                ></v-file-input>
                <v-tooltip bottom>
                  <template v-slot:activator="{ on, attrs }">
                    <v-icon v-bind="attrs" v-on="on" class="ml-2"
                      >mdi-help-circle</v-icon
                    >
                  </template>
                  <span>如果是 bot 使用，请上传图片证明 bot 的服务规模</span>
                </v-tooltip>
              </div>
              <v-text-field
                v-model="newToken.oldToken"
                label="旧版本 Token（如果没有旧版本 Token 请留空）"
                required
              ></v-text-field>
            </v-form>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" @click="submitForm">提交</v-btn>
            <v-btn @click="formDialog = false">取消</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-card>
  </v-dialog>
</template>

<script>
import axios from "axios";
export default {
  data() {
    return {
      open: false,
      visible: true,
      formDialog: false,
      headers: [
        { text: "Token", value: "token" },
        { text: "等级", value: "level" },
        { text: "状态", value: "available" },
        { text: "备注", value: "comment" },
      ],
      level_items: [
        { text: "<300次/天", value: 1 },
        { text: "<1000次/天", value: 2 },
        { text: "<3000次/天", value: 3 },
        { text: "<10000次/天", value: 4 },
      ],
      items: [],
      newToken: {
        level: null,
        reason: "",
        pic: [],
        oldToken: "",
      },
    };
  },
  mounted: function () {
    axios
      .get("https://www.diving-fish.com/api/maimaidxprober/developer_token")
      .then((response) => {
        this.items = response.data;
      })
      .catch((error) => {
        console.error(error);
      });
  },
  methods: {
    openFormDialog() {
      this.formDialog = true;
    },
    async submitForm() {
      if (this.$refs.form.validate()) {
        const base64Pics = await Promise.all(
          this.newToken.pic.map((file) => this.toBase64(file))
        );

        const postData = {
          token: this.newToken.oldToken,
          reason: this.newToken.reason,
          pic: base64Pics,
          level: this.newToken.level,
        };

        try {
          await axios.post(
            "https://www.diving-fish.com/api/maimaidxprober/developer_token",
            postData
          );
          this.items.push(postData);
          this.formDialog = false;
          this.resetForm();
          this.$message.success("已发送申请请求，请等待管理员审核");
        } catch (error) {
          this.$message.error(error.response.data.message);
        }
      }
    },
    resetForm() {
      this.newToken = {
        level: null,
        reason: "",
        pic: [],
        oldToken: "",
      };
    },
    toBase64(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = (error) => reject(error);
      });
    },
    copyToClipboard(text) {
      navigator.clipboard.writeText(text).then(
        () => {
          this.$message.success("已复制");
        },
        (err) => {
          console.error("Could not copy text: ", err);
        }
      );
    },
    getColor(item) {
      if (item.available) {
        return "green";
      } else {
        if (item.level === 0) {
          return "red";
        }
        return "orange";
      }
    },
    getIcon(item) {
      if (item.available) {
        return "mdi-check-circle";
      } else {
        if (item.level === 0) {
          return "mdi-close-circle";
        }
        return "mdi-alert-circle";
      }
    },
    getText(item) {
      if (item.available) {
        return "可用";
      } else {
        if (item.level === 0) {
          return "不可用";
        }
        return "审核中";
      }
    },
  },
};
</script>

<style scoped>
/* Add any component-specific styles here */
</style>