<template>
	<view>
		<form>
			<view style="padding: 20rpx; background-color: #FFFFFF; font-size: 32rpx;">手机版不支持导入数据，请登录后使用</view>
			<view class="cu-form-group">
				<view class="title">用户名</view>
				<input v-model="username"></input>
			</view>
			<view class="cu-form-group">
				<view class="title">密码</view>
				<input v-model="password" type="password"></input>
			</view>
			<view class="padding flex flex-direction bg-white">
			  <button class="cu-btn bg-blue lg" @click="login">登录</button>
			</view>
		</form>
	</view>
</template>

<script>
	export default {
		data() {
			return {
				username: "",
				password: ""
			}
		},
		methods: {
			login: function() {
				let that = this;
				uni.request({
					method: "POST",
					url: "https://www.diving-fish.com/api/maimaidxprober/login",
					data: {
						"username": that.username,
						"password": that.password
					},
					success: (resp) => {
						if (resp.statusCode == 200) {
							that.$emit('child-event', 'login')
						}
					}
				})
			}
		}
	}
</script>

<style>

</style>
