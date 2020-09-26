<template>
	<view>
		<cu-custom bgColor="bg-gradual-blue">
			<block slot="content">舞萌 DX 查分器</block>
		</cu-custom>
	</view>
</template>

<script>
	export default {
		data() {
			return {
				title: 'Hello'
			}
		},
		onLoad() {
			uni.request({
				url: "https://www.diving-fish.com/api/maimaidxprober/music_data",
				success: (resp) => {
					getApp().globalData.musicData = resp.data;
				}
			})
		},
		methods: {

		}
	}
</script>

<style>
	.content {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
	}

	.logo {
		height: 200rpx;
		width: 200rpx;
		margin-top: 200rpx;
		margin-left: auto;
		margin-right: auto;
		margin-bottom: 50rpx;
	}

	.text-area {
		display: flex;
		justify-content: center;
	}

	.title {
		font-size: 36rpx;
		color: #8f8f94;
	}
</style>