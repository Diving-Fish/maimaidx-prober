<template>
	<view>
		<scroll-view scroll-x class="bg-white nav text-center">
			<view :class="`cu-item flex-sub ${tabCur=='sd'?'text-blue cur':''}`" @click="tabSelect('sd')">
				标准乐谱
			</view>
			<view :class="`cu-item flex-sub ${tabCur=='dx'?'text-blue cur':''}`" @click="tabSelect('dx')">
				DX 乐谱
			</view>
		</scroll-view>
		<view class="cu-bar search bg-white">
			<view class="search-form round">
				<text class="cuIcon-search"></text>
				<input v-model="searchKey" type="text" placeholder="搜索乐曲"></input>
			</view>
		</view>
		<view style=" background-color: #FFFFFF;">
			<view style="padding: 12rpx 24rpx 12rpx 12rpx; margin: 0 auto; font-size: 32rpx; width: fit-content;">底分: {{ sdRa }} + {{ dxRa }} = {{ sdRa + dxRa }}</view>
		</view>
		<view v-if="currentDisplay.length == 0" style="padding: 12rpx 24rpx 12rpx 12rpx; margin: 0 auto; font-size: 32rpx; width: fit-content;">数据加载中，请稍候……</view>
		<view class="padding-sm">
			<view v-for="item in currentDisplay" :key="item.title + item.type + item.level_label">
				<view class="margin-bottom padding radius bg-white shadow">
					<view class="text-black margin-bottom">{{ item.title }}
						<text style="margin-left: 20rpx" :class="((item.rank <= 25 && item.type == 'SD') || (item.rank <= 15 && item.type == 'DX')) ? 'text-green':'text-grey'">#{{ item.rank }}</text>
					</view>
					<view class="flex" style="line-height: 24px;">
						<view style="width: 30%;" class="text-grey">难度</view>
						<view style="width: 70%;" :class="`difficulty${item.level_index}`">{{item.level_label}} {{item.level}}
							<text class="text-grey"> ({{item.ds}})</text>
						</view>
					</view>
					<view class="flex" style="line-height: 24px;">
						<view style="width: 30%;" class="text-grey">达成率</view>
						<view style="width: 70%;" class="text-black">{{ item.achievements.toFixed(4) }}%</view>
					</view>
					<view class="flex" style="line-height: 24px;">
						<view style="width: 30%;" class="text-grey">Rating</view>
						<view style="width: 70%;" class="text-black">{{ item.ra }}</view>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	export default {
		data() {
			return {
				tabCur: 'sd',
				searchKey: '',
			}
		},
		methods: {
			tabSelect: function(target) {
				this.tabCur = target
			}
		},
		props: {
			records: {
				type: Array,
				default: () => []
			}
		},
		computed: {
			currentDisplay: function() {
				return this[this.tabCur + 'Display']
			},
			sdDisplay: function() {
				return this.sdData.filter((elem) => {
					return elem.title.indexOf(this.searchKey) !== -1
				});
			},
			dxDisplay: function() {
				return this.dxData.filter((elem) => {
					return elem.title.indexOf(this.searchKey) !== -1
				});
			},
			sdData: function() {
				let data = this.records
					.filter((elem) => {
						return elem.type == "SD";
					})
					.sort((a, b) => {
						return b.ra - a.ra;
					});
				for (let i = 0; i < data.length; i++) {
					data[i].rank = i + 1;
				}
				return data;
			},
			dxData: function() {
				let data = this.records
					.filter((elem) => {
						return elem.type == "DX";
					})
					.sort((a, b) => {
						return b.ra - a.ra;
					});
				for (let i = 0; i < data.length; i++) {
					data[i].rank = i + 1;
				}
				return data;
			},
			sdRa: function() {
				let ret = 0;
				for (let i = 0; i < Math.min(this.sdData.length, 25); i++) {
					ret += this.sdData[i].ra;
				}
				return ret;
			},
			dxRa: function() {
				let ret = 0;
				for (let i = 0; i < Math.min(this.dxData.length, 15); i++) {
					ret += this.dxData[i].ra;
				}
				return ret;
			},
		}
	}
</script>

<style>
	.difficulty4 {
		color: #ba67f8;
	}

	.difficulty3 {
		color: #9e45e2;
	}

	.difficulty2 {
		color: #f64861;
	}

	.difficulty1 {
		color: #fb9c2d;
	}

	.difficulty0 {
		color: #22bb5b;
	}
</style>
