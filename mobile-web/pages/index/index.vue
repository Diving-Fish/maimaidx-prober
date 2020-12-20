<template>
	<view>
		<cu-custom bgColor="bg-gradual-blue">
			<block slot="content">舞萌 DX 查分器</block>
		</cu-custom>
		<login v-if="!login" @child-event="logined"></login>
		<record :records="records" v-if="pageCur == 'record' && login"></record>
		<!-- <player :scorestr="scorestr" v-if="pageCur == 'player'"></player> -->
		<view style="height: 100rpx;"></view>
		<view class="cu-bar tabbar bg-white shadow foot">
			<view class="action" @click="navChange('record')">
				<view :class="`text-blue cuIcon-news${(pageCur == 'record') ? 'fill': ''}`">
				</view>
				<view :class="(pageCur == 'record') ? 'text-blue': 'text-gray'">记录</view>
			</view>
			<!-- <view class="action" @click="navChange('player')">
				<view :class="`text-blue cuIcon-my${(pageCur == 'player') ? 'fill': ''}`">
				</view>
				<view :class="(pageCur == 'player') ? 'text-blue': 'text-gray'">玩家</view>
			</view> -->
		</view>
	</view>
</template>

<script>
	import player from '@/pages/components/player/player';
	import record from '@/pages/components/record/record';
	import login from '@/pages/components/login/login';
	export default {
		data() {
			return {
				pageCur: 'record',
				records: [],
				scorestr: "",
				login: true
			}
		},
		onLoad() {
			uni.request({
				url: "https://www.diving-fish.com/api/maimaidxprober/music_data",
				success: (resp) => {
					getApp().globalData.musicData = resp.data;
					this.fetchRecords();
				}
			})
		},
		methods: {
			navChange: function(page) {
				this.pageCur = page;
			},
			fetchRecords: function() {
				const that = this;
				console.log(this);
				uni.request({
					url: "https://www.diving-fish.com/api/maimaidxprober/player/records",
					success: (resp) => {
						if (resp.statusCode != 200) {
							that.login = false;
						} else {
							that.records = resp.data.records;
							that.login = true;
						}
					},
				})
			},
			logined: function() {
				this.login = true;
				this.fetchRecords();
			}
		},
		components: {
			record,
			player,
			login
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
