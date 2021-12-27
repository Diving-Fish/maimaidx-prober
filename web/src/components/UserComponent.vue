<template>
  <span>
    <span v-if="username !== ''">
      <v-btn x-large plain><v-icon>mdi-pencil</v-icon></v-btn>
    </span>
    <span v-else>
      <v-dialog
        width="500px"
        :fullscreen="$vuetify.breakpoint.mobile"
        v-model="loginVisible"
      >
        <template #activator="{ on, attrs }">
          <v-btn x-large plain v-bind="attrs" v-on="on">登录/注册</v-btn>
        </template>
        <v-card>
          <v-card-title>
            登录
            <v-spacer />
            <v-btn icon @click="loginVisible = false">
              <v-icon>mdi-close</v-icon>
            </v-btn>
          </v-card-title>
          <v-card-text>
            <v-form ref="form" v-model="valid" @keydown.enter.native="login">
              <v-text-field
                v-model="loginForm.username"
                label="用户名"
                autocomplete="username"
                :rules="[(u) => !!u || '用户名不能为空']"
              >
              </v-text-field>
              <v-text-field
                v-model="loginForm.password"
                label="密码"
                :rules="[(u) => !!u || '密码不能为空']"
                type="password"
                autocomplete="current-password"
              >
              </v-text-field>
            </v-form>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn class="mr-4" color="primary" @click="login">登录</v-btn>
            <v-btn @click="invokeRegister">立即注册</v-btn>
            <v-dialog
              width="500"
              :fullscreen="$vuetify.breakpoint.mobile"
              v-model="registerVisible"
            >
              <v-card>
                <v-card-title>
                  注册
                  <v-spacer />
                  <v-btn icon @click="registerVisible = false">
                    <v-icon>mdi-close</v-icon>
                  </v-btn>
                </v-card-title>
                <v-card-subtitle>
                  注册后会自动同步当前已导入的乐曲数据
                </v-card-subtitle>
                <v-card-text>
                  <v-form
                    ref="regForm"
                    v-model="valid2"
                    @keydown.enter.native="register"
                  >
                    <v-text-field
                      v-model="registerForm.username"
                      label="用户名"
                      autocomplete="username"
                      :rules="[
                        (u) => !!u || '用户名不能为空',
                        (u) => u.length >= 4 || '用户名至少长 4 个字符',
                      ]"
                    >
                    </v-text-field>
                    <v-text-field
                      v-model="registerForm.password"
                      label="密码"
                      type="password"
                      autocomplete="new-password"
                      :rules="[(u) => !!u || '密码不能为空']"
                    >
                    </v-text-field>
                    <v-text-field
                      v-model="registerForm.passwordConfirm"
                      label="确认密码"
                      type="password"
                      autocomplete="new-password"
                      :rules="[
                        (u) => !!u || '密码不能为空',
                        (u) => registerForm.password == u || '密码不一致',
                      ]"
                    >
                    </v-text-field>
                  </v-form>
                </v-card-text>
                <v-card-actions>
                  <v-spacer />
                  <v-btn color="primary" @click="register">注册</v-btn>
                </v-card-actions>
              </v-card>
            </v-dialog>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </span>
  </span>
</template>

<script>
export default {
  name: "UserComponent",
  props: {
    username: String
  },
  data() {
    return {
      loginVisible: false,
      registerVisible: false,
      loginForm: {
        username: "",
        password: "",
      },
      registerForm: {
        username: "",
        password: "",
        passwordConfirm: "",
      },
      valid: false,
      valid2: false
    };
  },
  created: function () {},
  methods: {
    invokeRegister: function () {
      this.loginVisible = false;
      this.registerVisible = true;
    },
    login: function() {
      if (!this.$refs.form.validate()) return;
      this.$emit('login');
    },
    register: function() {
      if (!this.$refs.regForm.validate()) return;
      this.$emit('register');
    }
  },
};
</script>

<style>
</style>