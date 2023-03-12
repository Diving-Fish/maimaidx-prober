<template>
  <div id="mainPage">
    <v-container fluid :style="$vuetify.breakpoint.mobile ? 'padding:0px' : ''">
      <div
        :style="$vuetify.breakpoint.mobile ? '' : 'display: flex; align-items: flex-end; justify-content: space-between'">
        <h1>舞萌 DX | 中二节奏查分器</h1>
        <profile :available_plates="available_plates" ref="profile" />
      </div>
      <v-divider class="mt-4 mb-4" />
      <p>
        <v-btn href="/maimaidx/prober_guide" target="_blank" color="primary">数据导入指南</v-btn>
        <tutorial ref="tutorial" />
      </p>
      <p class="mb-2">点个 Star 吧！</p>
      <a href="https://github.com/Diving-Fish/maimaidx-prober"><img
          src="https://img.shields.io/github/stars/Diving-Fish/maimaidx-prober?style=social" /></a>
      <view-badge class="ml-3" />
      <a class="ml-3" href="https://space.bilibili.com/10322617"><img
          src="https://shields.io/badge/bilibili-%E6%B0%B4%E9%B1%BC%E5%96%B5%E5%96%B5%E5%96%B5-00A1D6?logo=bilibili&style=flat"></a>
      <p class="mt-3">欢迎加入查分器交流群：</p>
      <p>464083009（3群）</p>
      <p>476936821（2群，已满）</p>
      <p>981682758（1群，已满）</p>
      <p>代理工具上线！使用微信客户端导入数据，请查看新版本的使用指南。</p>
      <p>想要 10 分钟搭建自己的 maimai QQ 机器人？现在就参考开源项目 <a href="https://github.com/Diving-Fish/mai-bot">mai-bot</a> 吧~</p>
      <p>请开发者打一局 maimai 如何？帮助我们<a href="https://afdian.net/a/divingfish">发发电</a>好不好嘛~</p>
      <p style="color: #f44336">
        迁移了数据库以加快网站的响应速度及后续开发。如遇任何无法导入成绩或出错的情况，请及时添加讨论群进行反馈。
      </p>
      <div style="
          display: flex;
          line-height: 64px;
          justify-content: center;
          flex-wrap: wrap;
        ">
        <v-dialog width="500px" :fullscreen="$vuetify.breakpoint.mobile" v-model="loginVisible">
          <template #activator="{ on, attrs }">
            <v-btn class="mt-3 mr-4" v-if="username == '未登录'" v-bind="attrs" v-on="on" color="primary">登录并同步数据</v-btn>
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
                <v-text-field v-model="loginForm.username" label="用户名" autocomplete="username"
                  :rules="[(u) => !!u || '用户名不能为空']">
                </v-text-field>
                <v-text-field v-model="loginForm.password" label="密码" :rules="[(u) => !!u || '密码不能为空']" type="password"
                  autocomplete="current-password">
                </v-text-field>
              </v-form>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn class="mr-4" color="primary" @click="login">登录</v-btn>
              <v-btn @click="invokeRegister">立即注册</v-btn>
              <v-dialog width="500" :fullscreen="$vuetify.breakpoint.mobile" v-model="registerVisible">
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
                    <v-form ref="regForm" v-model="valid2" @keydown.enter.native="register">
                      <v-text-field v-model="registerForm.username" label="用户名" autocomplete="username" :rules="[
                        (u) => !!u || '用户名不能为空',
                        (u) => u.length >= 4 || '用户名至少长 4 个字符',
                      ]">
                      </v-text-field>
                      <v-text-field v-model="registerForm.password" label="密码" type="password"
                        autocomplete="new-password" :rules="[(u) => !!u || '密码不能为空']">
                      </v-text-field>
                      <v-text-field v-model="registerForm.passwordConfirm" label="确认密码" type="password"
                        autocomplete="new-password" :rules="[
                          (u) => !!u || '密码不能为空',
                          (u) => registerForm.password == u || '密码不一致',
                        ]">
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
        <recovery :visible="username == '未登录'" />
        <v-dialog v-model="logoutVisible" width="500px" v-if="username !== '未登录'"
          :fullscreen="$vuetify.breakpoint.mobile">
          <template #activator="{ on, attrs }">
            <v-btn class="mt-3 mr-4" v-bind="attrs" v-on="on">登出</v-btn>
          </template>
          <v-card>
            <v-card-title>
              确认
              <v-spacer />
              <v-btn icon @click="logoutVisible = false">
                <v-icon>mdi-close</v-icon>
              </v-btn>
            </v-card-title>
            <v-card-text> 您确定要登出吗？ </v-card-text>
            <v-card-actions>
              <v-btn class="mr-4" @click="logout" color="primary">登出</v-btn>
              <v-btn @click="logoutVisible = false">取消</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
        <v-dialog width="1000px" :fullscreen="$vuetify.breakpoint.mobile" v-model="dialogVisible">
          <template #activator="{ on, attrs }">
            <v-btn class="mt-3 mr-4" v-bind="attrs" v-on="on">导入数据</v-btn>
          </template>
          <v-card>
            <v-card-title>
              导入数据
              <v-spacer />
              <v-btn icon @click="dialogVisible = false">
                <v-icon>mdi-close</v-icon>
              </v-btn>
            </v-card-title>
            <v-card-text>
              <v-textarea type="textarea" label="请将乐曲数据的源代码粘贴到这里" v-model="textarea" :rows="15" outlined></v-textarea>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn color="primary" @click="flushData()">确定</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
        <v-dialog width="500px" :fullscreen="$vuetify.breakpoint.mobile" v-model="feedbackVisible">
          <template #activator="{ on, attrs }">
            <v-btn class="mt-3 mr-4" v-bind="attrs" v-on="on">提交反馈</v-btn>
          </template>
          <v-card>
            <v-card-title>
              反馈
              <v-spacer />
              <v-btn icon @click="feedbackVisible = false">
                <v-icon>mdi-close</v-icon>
              </v-btn>
            </v-card-title>
            <v-card-text>
              <v-textarea rows="5" placeholder="补充乐曲定数或者对查分器有什么意见和建议都可以写在这里" v-model="feedbackText"></v-textarea>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn color="primary" @click="sendFeedback()">确定</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </div>
      <v-container id="tableBody" style="margin-top: 2em" px-0 py-0>
        <v-card>
          <v-window v-model="tableMode">
            <v-window-item>
              <v-btn v-if="$vuetify.breakpoint.mobile" plain block class="mt-3" @click="changeTable(1)">
                <v-icon>mdi-swap-horizontal</v-icon>切换到中二节奏成绩表格
              </v-btn>
              <div style="display: flex; line-height: 64px; justify-content: left; flex-wrap: wrap;" class="pt-3 pl-5">
                <v-dialog v-model="exportVisible" width="500px" :fullscreen="$vuetify.breakpoint.mobile">
                  <template #activator="{ on, attrs }">
                    <v-btn class="mt-3 mr-4" v-bind="attrs" v-on="on">导出为 CSV</v-btn>
                  </template>
                  <v-card>
                    <v-card-title>
                      导出为 CSV
                      <v-spacer />
                      <v-btn icon @click="exportVisible = false">
                        <v-icon>mdi-close</v-icon>
                      </v-btn>
                    </v-card-title>
                    <v-card-text>
                      <div style="display: flex">
                        <v-select v-model="exportEncoding" label="选择编码" :items="exportEncodings">
                        </v-select>
                        <v-tooltip bottom>
                          <template v-slot:activator="{ on, attrs }">
                            <v-icon v-bind="attrs" v-on="on" class="ml-4">
                              mdi-help-circle
                            </v-icon>
                          </template>
                          <span>GBK编码一般用于Excel打开，UTF-8编码则可以供部分其他编辑器直接显示。</span>
                        </v-tooltip>
                      </div>
                    </v-card-text>
                    <v-card-actions>
                      <v-btn class="mr-4" @click="exportToCSV('sd')">导出标准乐谱</v-btn>
                      <v-btn @click="exportToCSV('dx')">导出 DX 乐谱</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <plate-qualifier ref="pq" :music_data="music_data" :records="records" />
                <calculators ref="calcs" />
                <v-dialog v-model="allModeVisible" width="500px" :fullscreen="$vuetify.breakpoint.mobile">
                  <template #activator="{ on, attrs }">
                    <v-btn class="mt-3 mr-4" v-bind="attrs" v-on="on" color="deep-orange" dark>解锁全曲</v-btn>
                  </template>
                  <v-card>
                    <v-card-title>
                      确认
                      <v-spacer />
                      <v-btn icon @click="allModeVisible = false">
                        <v-icon>mdi-close</v-icon>
                      </v-btn>
                    </v-card-title>
                    <v-card-text>解锁全曲可以让您看到所有谱面的定数数据和相对难度，但您无法对这些谱面进行修改。确定解锁全曲？
                    </v-card-text>
                    <v-card-actions>
                      <v-btn class="mr-4" @click="mergeOnAllMode" color="primary">解锁</v-btn>
                      <v-btn @click="allModeVisible = false">取消</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <v-btn v-if="!$vuetify.breakpoint.mobile" plain class="mt-3 mr-4" style="position: absolute; right: 0px" @click="changeTable(1)">
                  <v-icon>mdi-swap-horizontal</v-icon>切换到中二节奏成绩表格
                </v-btn>
              </div>

              <v-card-title>舞萌 DX 成绩表格
                <v-spacer />
                <v-checkbox label="使用高级设置" v-model="proSetting" class="mr-4" @click="$refs.proSettings.reset()">
                </v-checkbox>
                <v-text-field v-model="searchKey" append-icon="mdi-magnify" label="查找乐曲" single-line hide-details
                  class="mb-4"></v-text-field>
              </v-card-title>
              <v-card-subtitle>底分: {{ sdRa }} + {{ dxRa }} = {{ sdRa + dxRa }}</v-card-subtitle>
              <filter-slider ref="filterSlider"></filter-slider>
              <pro-settings v-show="proSetting" ref="proSettings" :music_data="music_data"
                :music_data_dict="music_data_dict" @setHeaders="setHeaders"></pro-settings>
              <v-card-text>
                <v-tabs v-model="tab">
                  <v-tab key="sd">旧乐谱</v-tab>
                  <v-tab key="dx">DX 2022</v-tab>
                </v-tabs>
                <v-tabs-items v-model="tab">
                  <v-tab-item key="sd">
                    <chart-table @cover="coverRow" @edit="editRow" @calculator="calculatorRow" :search="searchKey"
                      :items="sdDisplay" :limit="25" :loading="loading" :chart_stats="chart_stats" :headers="headers"
                      :music_data_dict="music_data_dict" sort-by="achievements" :key="JSON.stringify(headers)">
                    </chart-table>
                  </v-tab-item>
                  <v-tab-item key="dx">
                    <chart-table @cover="coverRow" @edit="editRow" @calculator="calculatorRow" :search="searchKey"
                      :items="dxDisplay" :limit="15" :loading="loading" :chart_stats="chart_stats" :headers="headers"
                      :music_data_dict="music_data_dict" sort-by="achievements" :key="JSON.stringify(headers)">
                    </chart-table>
                  </v-tab-item>
                </v-tabs-items>
              </v-card-text>
            </v-window-item>
            <v-window-item eager>
              <v-btn plain v-if="$vuetify.breakpoint.mobile" block class="mt-3" @click="changeTable(0)">
                <v-icon>mdi-swap-horizontal</v-icon>切换到舞萌 DX 成绩表格
              </v-btn>
              <div style="display: flex; line-height: 64px; justify-content: left; flex-wrap: wrap; min-height: 60px;" class="pt-3 pl-5">
                <v-dialog v-model="exportVisibleChuni" width="500px" :fullscreen="$vuetify.breakpoint.mobile">
                  <template #activator="{ on, attrs }">
                    <v-btn class="mt-3 mr-4" v-bind="attrs" v-on="on">导出为 CSV</v-btn>
                  </template>
                  <v-card>
                    <v-card-title>
                      导出为 CSV
                      <v-spacer />
                      <v-btn icon @click="exportVisibleChuni = false">
                        <v-icon>mdi-close</v-icon>
                      </v-btn>
                    </v-card-title>
                    <v-card-text>
                      <div style="display: flex">
                        <v-select v-model="exportEncodingChuni" label="选择编码" :items="exportEncodings">
                        </v-select>
                        <v-tooltip bottom>
                          <template v-slot:activator="{ on, attrs }">
                            <v-icon v-bind="attrs" v-on="on" class="ml-4">
                              mdi-help-circle
                            </v-icon>
                          </template>
                          <span>GBK编码一般用于Excel打开，UTF-8编码则可以供部分其他编辑器直接显示。</span>
                        </v-tooltip>
                      </div>
                    </v-card-text>
                    <v-card-actions>
                      <v-btn class="mr-4" @click="expertToCSVChuni()">导出</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <ChuniOverPowerCalculators/>
                <v-dialog v-model="allModeVisibleChuni" width="500px" :fullscreen="$vuetify.breakpoint.mobile">
                  <template #activator="{ on, attrs }">
                    <v-btn class="mt-3 mr-4" v-bind="attrs" v-on="on" color="deep-orange" dark>解锁全曲</v-btn>
                  </template>
                  <v-card>
                    <v-card-title>
                      确认
                      <v-spacer />
                      <v-btn icon @click="allModeVisibleChuni = false">
                        <v-icon>mdi-close</v-icon>
                      </v-btn>
                    </v-card-title>
                    <v-card-text>解锁全曲可以让您看到所有谱面的定数数据，但您无法对这些谱面进行修改。确定解锁全曲？
                    </v-card-text>
                    <v-card-actions>
                      <v-btn class="mr-4" @click="unlockAllChuni" color="primary">解锁</v-btn>
                      <v-btn @click="allModeVisibleChuni = false">取消</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <v-btn plain v-if="!$vuetify.breakpoint.mobile" class="mt-3 mr-4" style="position: absolute; right: 0px" @click="changeTable(0)">
                  <v-icon>mdi-swap-horizontal</v-icon>切换到舞萌 DX 成绩表格
                </v-btn>
              </div>
              <v-card-title>中二节奏成绩表格
                <v-spacer />
                <v-checkbox label="使用高级设置" v-model="proSettingChuni" class="mr-4" @click="$refs.proSettingsChuni.reset()">
                </v-checkbox>
                <v-text-field v-model="searchKey" append-icon="mdi-magnify" label="查找乐曲" single-line hide-details
                  class="mb-4"></v-text-field>
              </v-card-title>
              <v-card-subtitle>
                <span class="mr-2">Rating: {{ chuni_obj.rating ? chuni_obj.rating.toFixed(4) : 0 }}</span>
                <span class="mr-2">无需推分可达到的最高Rating: {{ chuniBestRating.toFixed(4) }}</span>
              </v-card-subtitle>
              <filter-slider ref="filterSliderChuni"></filter-slider>
              <pro-settings-chuni v-show="proSettingChuni" ref="proSettingsChuni" :music_data="chuni_data"
                            :music_data_dict="chuni_data_dict" @setHeaders="setHeaders"></pro-settings-chuni>
              <v-card-text>
                <chuni-table :search="searchKey" :items="chuniRecordDisplay" :music_data_dict="chuni_data_dict">
                </chuni-table>
              </v-card-text>
            </v-window-item>
          </v-window>
        </v-card>
      </v-container>
      <div class="mid" :style="$vuetify.breakpoint.mobile ? '' : 'display: flex'">
        <message @resize="$refs.advertisement.resize()"
          :style="`flex: 1; ${$vuetify.breakpoint.mobile ? '' : 'min-width: 500px; margin-right: 16px'}`" class="mbe-2">
        </message>
        <advertisement ref="advertisement" class="mbe-2"></advertisement>
      </div>
      <v-card>
        <v-card-title>更新记录</v-card-title>
        <v-card-text>
          2023/01/22
          （By 蜜柑）大家新年快乐，除夕和春节两晚给中二节奏成绩表格肝（抄）了个导出成绩、谱面筛选和 OP 计算器（这个是自己写的）等功能。同时修复了一些前端的小 bug，并将成绩评级分数线修改成与中二节奏 NEW 现行分数线一致。<br />
          2022/10/24
          中二查分器来咯，1024程序员节快乐~<br />
          2021/11/25
          （By StageChan）又更了一大堆，包括查看封面按钮，修改密码功能，优化移动端网页体验等。<br />
          2021/11/07
          （By StageChan）更了一些网页计算器工具以及网页使用指南。<br />
          2021/09/28
          （By StageChan）更了一大堆，包括高级设置中的各种筛选、表列选择和暗色主题；DX分数相关；
          鼠标浮动在曲名和难度上显示谱面信息、浮动在DX Rating上显示后续分数线等等。修了一堆bug。<br />
          2021/09/06
          更新了查询牌子的功能。<br />
          2021/07/16
          更新了天界 2 的歌曲数据，以及相对难度从现在开始按照 SSS 的人数进行排名了。<br />
          2021/03/18
          加载动画和按难度/定数筛选，你们要的筛选来了。顺便加了个可以看全曲的功能。<br />
          2021/02/26 发布 1.0
          版本，添加了登出按钮，并优化了一些成绩导入方式。提供了代理服务器供便捷导入成绩。<br />
          2021/02/17 废弃了目前在使用的移动端（Vuetify さいこう！），导出为 csv
          增加了一个二次确认窗口。以及优化了所有的对话框。<br />
          2021/02/15 添加了导出为 csv
          的功能。在导入的页面源代码有问题时新增了报错提示。<br />
          2021/02/10 更改了UI。废弃了微信扫码登录的功能和导出为截图的功能。<br />
          2020/12/12
          大家都在买东西，我在加功能。增加了使用微信扫码导入数据的功能。<br />
          2020/09/26 修正了ENENGY SYNERGY MATRIX的乐曲定数，补充了セイクリッド
          ルイン的定数。增加了评级标签和FC/FS标签<br />
          2020/09/10
          教师节快乐！增加了登录、注册和数据同步的功能，增加了修改单曲完成率的功能，不需要再反复导入数据了<br />
          2020/09/02 增加了导出为截图的功能，增加了Session High⤴ 和
          バーチャルダム ネーション 的 Master 难度乐曲定数<br />
          2020/08/31 发布初版
        </v-card-text>
      </v-card>
    </v-container>
    <v-dialog width="500px" :fullscreen="$vuetify.breakpoint.mobile" v-model="modifyAchievementVisible">
      <v-card>
        <v-card-title>
          修改完成率
          <v-spacer />
          <v-btn icon @click="modifyAchievementVisible = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-subtitle>
          修改
          <i>{{ currentUpdate.type == "DX" ? "[DX] " : ""
          }}<b>{{ currentUpdate.title }}</b> [{{
    currentUpdate.level_label
}}]</i>
          的完成率为
        </v-card-subtitle>
        <v-card-text>
          <v-form ref="modifyAchievementForm" @keydown.enter.native="finishEditRow">
            <v-text-field label="达成率" v-model="currentAchievements" :rules="[
              (u) =>
                (isFinite(+u) && +u >= 0 && +u <= 101) ||
                '请输入合法达成率',
            ]" />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="primary" @click="finishEditRow()">确定</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-dialog width="500px" :fullscreen="$vuetify.breakpoint.mobile" v-model="coverVisible">
      <v-card>
        <v-card-title>
          查看封面
          <v-spacer />
          <v-btn icon @click="coverVisible = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-subtitle>
          <i><b>{{ coverItem.title }}</b></i>
        </v-card-subtitle>
        <v-row class="ma-0" align="center" justify="center" v-if="coverLoading">
          <v-progress-circular color="grey" indeterminate></v-progress-circular>
        </v-row>
        <v-card-text>
          <v-img :src="`https://www.diving-fish.com/covers/${getCoverPathById(coverItem.song_id)}`" contain
            :height="coverLoading ? 0 : undefined" @load="coverLoading = false"></v-img>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import axios from "axios";
import Vue from "vue";
import ChartTable from "../components/ChartTable.vue";
import ChuniTable from "../components/ChuniTable.vue";
import ViewBadge from "../components/ViewBadge.vue";
import GBK from "../plugins/gbk";
import FilterSlider from "../components/FilterSlider.vue";
import ProSettings from "../components/ProSettings.vue";
import ProSettingsChuni from "@/components/ProSettingsChuni";
import Advertisement from "../components/Advertisement.vue";
import Message from "../components/Message.vue";
import Profile from "../components/Profile.vue";
import PlateQualifier from "../components/PlateQualifier.vue";
import Calculators from "../components/Calculators.vue";
import Tutorial from "../components/Tutorial.vue";
import Recovery from "../components/Recovery.vue";
import watchVisible from "../plugins/watchVisible";
import ChuniOverPowerCalculators from "@/components/ChuniOverPowerCalculators";
const xpath = require("xpath"),
  dom = require("xmldom").DOMParser;
const DEBUG = false;
export default {
  name: "App",
  components: {
    ChuniOverPowerCalculators,
    ProSettingsChuni,
    ChartTable,
    ChuniTable,
    ViewBadge,
    FilterSlider,
    ProSettings,
    Advertisement,
    Recovery,
    Message,
    Profile,
    PlateQualifier,
    Calculators,
    Tutorial,
  },
  data: function () {
    return {
      tableMode: 0, // mai or chuni
      tab: "",
      loginForm: {
        username: "",
        password: "",
      },
      registerForm: {
        username: "",
        password: "",
        passwordConfirm: "",
      },
      chart_stats: {},
      currentUpdate: {},
      currentAchievements: 0,
      username: "未登录",
      activeName: "SD",
      textarea: "",
      searchKey: "",
      records: [],
      music_data: [],
      music_data_dict: {},
      chuni_obj: {},
      chuni_records: [],
      chuni_data: [],
      chuni_data_dict: {},
      level_label: ["Basic", "Advanced", "Expert", "Master", "Re:MASTER"],
      feedbackText: "",
      feedbackVisible: false,
      loginVisible: false,
      registerVisible: false,
      dialogVisible: false,
      modifyAchievementVisible: false,
      coverVisible: false,
      coverLoading: true,
      coverItem: {},
      qrDialogVisible: false,
      qrcode: "",
      qrcodePrompt: "",
      ws: null,
      loading: false,
      valid: false,
      valid2: false,
      exportVisible: false,
      exportEncoding: "GBK",
      exportEncodingChuni: "GBK",
      exportEncodings: ["GBK", "UTF-8"],
      logoutVisible: false,
      allModeVisible: false,
      allModeVisibleChuni: false,
      exportVisibleChuni: false,
      proSetting: false,
      proSettingChuni: false,
      chart_combo: {},
      headers: [
        { text: "排名", value: "rank" },
        { text: "封面", value: "cover", sortable: false},
        { text: "乐曲名", value: "title" },
        { text: "难度", value: "level", sortable: false },
        { text: "定数", value: "ds" },
        { text: "达成率", value: "achievements" },
        { text: "DX Rating", value: "ra" },
        { text: "相对难度", value: "tag" },
        { text: "操作", value: "actions", sortable: false },
      ],
    };
  },
  computed: {
    chuniBestRating: function() {
      let ra = 0;
      if (this.chuni_obj.records == undefined) return 0.0;
      if (this.chuni_obj.records.best.length > 0) ra += this.chuni_obj.records.best[0].ra * 10;
      for (let i = 0; i < Math.min(this.chuni_obj.records.best.length, 30); i++)
      {
        ra += this.chuni_obj.records.best[i].ra;
      }
      return ra / 40;
    },
    chuniRecordDisplay: function() {
      const that = this;
      return this.chuni_records.filter((elem) => {
        return (
            that.$refs.filterSliderChuni.f(elem) &&
            (!that.proSettingChuni || that.$refs.proSettingsChuni.f(elem)))
      });
    },
    title2id: function () {
      let obj = {};
      for (const music of this.music_data) {
        obj[music.title + music.type] = music.id
      }
      return obj;
    },
    sdDisplay: function () {
      const that = this;
      return this.sdData.filter((elem) => {
        return (
          that.$refs.filterSlider.f(elem) &&
          (!that.proSetting || that.$refs.proSettings.f(elem))
        );
      });
    },
    dxDisplay: function () {
      const that = this;
      return this.dxData.filter((elem) => {
        return (
          that.$refs.filterSlider.f(elem) &&
          (!that.proSetting || that.$refs.proSettings.f(elem))
        );
      });
    },
    sdData: function () {
      let data = this.records
        .filter((elem) => {
          return !this.is_new(elem);
        })
        .sort((a, b) => {
          return b.ra - a.ra;
        });
      for (let i = 0; i < data.length; i++) {
        data[i].rank = i + 1;
      }
      return data;
    },
    dxData: function () {
      let data = this.records
        .filter((elem) => {
          return this.is_new(elem);
        })
        .sort((a, b) => {
          return b.ra - a.ra;
        });
      for (let i = 0; i < data.length; i++) {
        data[i].rank = i + 1;
      }
      return data;
    },
    sdRa: function () {
      let ret = 0;
      for (let i = 0; i < Math.min(this.sdData.length, 25); i++) {
        ret += this.sdData[i].ra;
      }
      return ret;
    },
    dxRa: function () {
      let ret = 0;
      for (let i = 0; i < Math.min(this.dxData.length, 15); i++) {
        ret += this.dxData[i].ra;
      }
      return ret;
    },
  },
  created: function () {
    history.replaceState("", "", window.location.pathname);
    this.fetchMusicData();
  },
  watch: {
    loginVisible: watchVisible("loginVisible", "Login"),
    // registerVisible: watchVisible("registerVisible", "Register"),
    dialogVisible: watchVisible("dialogVisible", "Import"),
    feedbackVisible: watchVisible("feedbackVisible", "Feedback"),
    exportVisible: watchVisible("exportVisible", "Export"),
    logoutVisible: watchVisible("logoutVisible", "Logout"),
    allModeVisible: watchVisible("allModeVisible", "AllMode"),
    modifyAchievementVisible: watchVisible("modifyAchievementVisible", "ModifyAchievement"),
    coverVisible: watchVisible("coverVisible", "Cover"),
    qrDialogVisible: function (to) {
      if (!to) {
        console.log("cancelled by user.");
        this.qrcode = "";
        this.ws.close();
        this.ws = null;
      }
    },
    tableMode: function () {
      // 强刷 FilterSlider
      // if (this.chuni_records.length > 0)
      //   setTimeout(() => {Vue.set(this.chuni_records, 0, this.chuni_records[0])}, 100);
    }
  },
  methods: {
    rawToString: function (text) {
      if (text[text.length - 1] == "p" && text != "ap") {
        return text.substring(0, text.length - 1).toUpperCase() + "+";
      } else {
        return text.toUpperCase();
      }
    },
    invokeRegister: function () {
      this.loginVisible = false;
      this.registerVisible = true;
    },
    coverRow: function (record) {
      this.coverVisible = true;
      if (record.song_id != this.coverItem.song_id)
        this.coverLoading = true;
      this.coverItem = record;
    },
    getCoverPathById: function (songId) {
      let i = parseInt(songId);
      if (i > 10000) i -= 10000;
      return (i + "").padStart(4, '0') + ".png";
    },
    editRow: function (record) {
      this.currentUpdate = record;
      this.currentAchievements = this.currentUpdate.achievements;
      this.modifyAchievementVisible = true;
    },
    finishEditRow: function () {
      if (!this.$refs.modifyAchievementForm.validate()) return;
      this.currentUpdate.achievements = parseFloat(this.currentAchievements);
      this.computeRecord(this.currentUpdate);
      if (this.username != "未登录") {
        axios
          .post(
            "https://www.diving-fish.com/api/maimaidxprober/player/update_record",
            this.currentUpdate
          )
          .then(() => {
            this.$message.success("修改已同步");
          })
          .catch(() => {
            this.$message.error("修改失败！");
          });
      } else {
        this.$message.success("修改成功");
      }
      this.modifyAchievementVisible = false;
    },
    calculatorRow: function (item) {
      let note_total = {
        Tap: this.music_data_dict[item.song_id].charts[item.level_index]
          .notes[0],
        Hold: this.music_data_dict[item.song_id].charts[item.level_index]
          .notes[1],
        Slide:
          this.music_data_dict[item.song_id].charts[item.level_index].notes[2],
        Touch: 0,
        Break:
          this.music_data_dict[item.song_id].charts[item.level_index].notes[3],
      };
      if (this.music_data_dict[item.song_id].type == "DX") {
        Object.assign(note_total, {
          Touch:
            this.music_data_dict[item.song_id].charts[item.level_index]
              .notes[3],
          Break:
            this.music_data_dict[item.song_id].charts[item.level_index]
              .notes[4],
        });
      }
      this.$refs.calcs.fill({
        note_total: note_total,
        current_song: item,
        visible: true,
      });
      this.$message.success(
        `已填入 ${item.type == "DX" ? "[DX] " : ""}${item.title} [${item.level_label
        }] 的数据`
      );
    },
    register: function () {
      if (!this.$refs.regForm.validate()) return;
      axios
        .post("https://www.diving-fish.com/api/maimaidxprober/register", {
          username: this.registerForm.username,
          password: this.registerForm.password,
          records: this.records,
        })
        .then(() => {
          this.$message.success("注册成功，数据已同步完成");
          this.username = this.registerForm.username;
          this.registerVisible = false;
          setTimeout("window.location.reload()", 1000);
        })
        .catch((err) => {
          this.$message.error("注册失败！");
          this.$message.error(err.response.data.message);
        });
    },
    sync: function () {
      // console.log(this.records);
      axios
        .post(
          "https://www.diving-fish.com/api/maimaidxprober/player/update_records",
          this.records.filter((elem) => {
            return elem.block !== true;
          })
        )
        .then(() => {
          this.$message.success("数据已同步完成");
        })
        .catch(() => {
          this.$message.error("数据同步失败！");
        });
    },
    sendFeedback: function () {
      axios
        .post("https://www.diving-fish.com/api/maimaidxprober/feedback", {
          message: this.feedbackText,
        })
        .then(() => {
          this.$message.success("您的反馈我们已收到，谢谢！");
          this.feedbackVisible = false;
        })
        .catch(() => {
          this.$message.error("反馈发送失败！");
        });
    },
    fetchMusicData: function () {
      const that = this;
      that.loading = true;
      this.$message.info("正在获取乐曲信息……");
      axios.get("https://www.diving-fish.com/api/chunithmprober/music_data")
        .then((resp) => {
          this.chuni_data = resp.data;
          this.chuni_data_dict = this.chuni_data.reduce((acc, music) => {
            acc[music.id] = music;
            return acc;
          }, {});
          this.$message.success("中二节奏乐曲信息获取完成，正在获取用户分数信息……");
          axios.get(
            DEBUG ? "https://www.diving-fish.com/api/chunithmprober/player/test_data" : "https://www.diving-fish.com/api/chunithmprober/player/records"
          ).then(resp => {
            this.chuni_obj = resp.data;
            this.chuni_obj.records.best = this.chuni_obj.records.best.sort((a, b) => {return b.ra - a.ra})
            this.chuni_obj.records.r10 = this.chuni_obj.records.r10.sort((a, b) => {return b.ra - a.ra})
            this.chuni_records = JSON.parse(JSON.stringify(this.chuni_obj.records.r10))
            this.chuni_records = this.chuni_records.concat(JSON.parse(JSON.stringify(this.chuni_obj.records.best)))
            let rank = -10;
            for (let i of this.chuni_records) {
              i.rank = rank;
              rank++;
              if (rank == 0) rank++;
            }
          }).catch(() => {
            this.$message.warning("未获取用户分数");
          })
        })
      axios.get("https://www.diving-fish.com/api/maimaidxprober/music_data")
        .then((resp) => {
          this.music_data = resp.data;
          this.music_data_dict = this.music_data.reduce((acc, music) => {
            acc[music.id] = music;
            return acc;
          }, {});
          for (let elem of this.music_data)
            this.chart_combo[elem.id] = elem.charts.map((o) =>
              o.notes.reduce((prev, curr) => prev + curr)
            );
          this.$message.success("舞萌 DX 乐曲信息获取完成，正在获取用户分数及相对难度信息……");
          Promise.allSettled([
            axios.get(
              "https://www.diving-fish.com/api/maimaidxprober/chart_stats"
            ),
            axios.get(
              DEBUG ? "https://www.diving-fish.com/api/maimaidxprober/player/test_data" : "https://www.diving-fish.com/api/maimaidxprober/player/records"
            ),
          ]).then(([resp1, resp2]) => {
            if (resp1.status === "rejected") {
              this.$message.error("相对难度信息获取失败，请重新加载！");
              that.loading = false;
              return;
            }
            that.chart_stats = resp1.value.data;
            if (resp2.status !== "rejected") {
              const data = resp2.value.data;
              that.username = data.username;
              that.merge(data.records);
              this.$message.success("用户分数及相对难度信息获取完成");
            } else {
              this.$message.warning("未获取用户分数");
            }
            this.$refs.pq.init();
            that.loading = false;
          });
        })
        .catch(() => {
          this.$message.error("乐曲信息获取失败，请重新加载！");
        });
    },
    login: function () {
      if (!this.$refs.form.validate()) return;
      axios
        .post("https://www.diving-fish.com/api/maimaidxprober/login", {
          username: this.loginForm.username,
          password: this.loginForm.password,
        })
        .then(() => {
          this.$message.success("登录成功，加载乐曲数据中……");
          this.loading = true;
          this.loginVisible = false;
          this.$refs.profile.fetch();
          axios
            .get(
              "https://www.diving-fish.com/api/maimaidxprober/player/records"
            )
            .then((resp) => {
              const data = resp.data;
              this.username = data.username;
              this.merge(data.records);
              this.$refs.pq.init();
              this.loading = false;
            })
            .catch(() => {
              this.$message.error("加载乐曲失败！");
            });
        })
        .catch((err) => {
          this.$message.error("登录失败！");
          this.$message.error(err.response.data.message);
        });
    },
    computeRecord: function (record) {
      if (this.music_data_dict[record.song_id])
        record.ds = this.music_data_dict[record.song_id].ds[record.level_index];
      if (record.ds && record.ds >= 7.0) {
        let arr = ("" + record.ds).split(".");
        if (["7", "8", "9"].indexOf(arr[1]) != -1) {
          record.level = arr[0] + "+";
        } else {
          record.level = arr[0];
        }
      }
      record.level_label = this.level_label[record.level_index];
      let l = 14;
      const rate = record.achievements;
      if (rate < 50) {
        l = 0;
      } else if (rate < 60) {
        l = 5;
      } else if (rate < 70) {
        l = 6;
      } else if (rate < 75) {
        l = 7;
      } else if (rate < 80) {
        l = 7.5;
      } else if (rate < 90) {
        l = 8.5;
      } else if (rate < 94) {
        l = 9.5;
      } else if (rate < 97) {
        l = 10.5;
      } else if (rate < 98) {
        l = 12.5;
      } else if (rate < 99) {
        l = 12.7;
      } else if (rate < 99.5) {
        l = 13;
      } else if (rate < 100) {
        l = 13.2;
      } else if (rate < 100.5) {
        l = 13.5;
      }
      record.ra = Math.floor(record.ds * (Math.min(100.5, rate) / 100) * l);
      if (isNaN(record.ra)) record.ra = 0;
      // Update Rate
      if (record.achievements < 50) {
        record.rate = "d";
      } else if (record.achievements < 60) {
        record.rate = "c";
      } else if (record.achievements < 70) {
        record.rate = "b";
      } else if (record.achievements < 75) {
        record.rate = "bb";
      } else if (record.achievements < 80) {
        record.rate = "bbb";
      } else if (record.achievements < 90) {
        record.rate = "a";
      } else if (record.achievements < 94) {
        record.rate = "aa";
      } else if (record.achievements < 97) {
        record.rate = "aaa";
      } else if (record.achievements < 98) {
        record.rate = "s";
      } else if (record.achievements < 99) {
        record.rate = "sp";
      } else if (record.achievements < 99.5) {
        record.rate = "ss";
      } else if (record.achievements < 100) {
        record.rate = "ssp";
      } else if (record.achievements < 100.5) {
        record.rate = "sss";
      } else {
        record.rate = "sssp";
      }
      if (!this.chart_stats[record.song_id]) {
        record.tag = 0.5;
      } else {
        let elem = this.chart_stats[record.song_id][record.level_index];
        if (elem.t) {
          record.tag = (elem.v + 0.5) / elem.t;
        } else {
          record.tag = 0.5;
        }
      }
      if (!this.chart_combo[record.song_id]) {
        record.dxScore_perc = 0;
      } else {
        record.dxScore_perc =
          (record.dxScore /
            (this.chart_combo[record.song_id][record.level_index] * 3)) *
          100;
      }
    },
    mergeOnAllMode: function () {
      this.allModeVisible = false;
      let oldRecords = new Set(
        this.records.map((r) => +r.song_id * 10 + r.level_index)
      );
      for (const music of this.music_data) {
        //console.log(music);
        for (let j = 0; j < music.ds.length; j++) {
          const record = {
            song_id: music.id,
            title: music.title,
            ds: music.ds[j],
            level: music.level[j],
            level_index: j,
            type: music.type,
            achievements: 0,
            dxScore: 0,
            fc: "",
            fs: "",
            rate: "d",
            ra: 0,
            level_label: this.level_label[j],
            block: true,
          };
          if (
            !oldRecords.has(Number(record.song_id) * 10 + record.level_index)
          ) {
            this.records.push(record);
          }
        }
      }
      //console.log(this.records);
      for (let i = 0; i < this.records.length; i++) {
        this.computeRecord(this.records[i]);
      }
    },
    is_new: function (record) {
      return this.music_data_dict[record.song_id].basic_info.is_new;
    },
    merge: function (records) {
      // console.log(records);
      let oldRecords = Object.fromEntries(
        this.records.map((r, i) => [+r.song_id * 10 + r.level_index, i])
      );
      for (let record of records) {
        let i = oldRecords[+record.song_id * 10 + record.level_index];
        if (typeof i != "undefined") {
          Vue.set(this.records, i, record);
        } else {
          this.records.push(record);
        }
      }
      for (let i = 0; i < this.records.length; i++) {
        this.computeRecord(this.records[i]);
      }
      // console.log(this.records);
    },
    flushData: function () {
      const records = this.pageToRecordList(this.textarea);
      this.merge(records);
      this.sync();
      this.textarea = "";
      this.dialogVisible = false;
    },
    pageToRecordList: function (pageData) {
      const getSibN = function (node, n) {
        let cur = node;
        let f = false;
        if (n < 0) {
          n = -n;
          f = true;
        }
        for (let i = 0; i < n; i++) {
          if (f) cur = cur.previousSibling;
          else cur = cur.nextSibling;
        }
        return cur;
      };
      try {
        let link = false;
        let records = [];
        let doc = new dom().parseFromString(pageData);
        // this modify is about to detect two different 'Link'.
        const names = xpath.select(
          '//div[@class="music_name_block t_l f_13 break"]',
          doc
        );
        const labels = ["basic", "advanced", "expert", "master", "remaster"];
        for (const name of names) {
          let title = name.textContent;
          if (title == "Link") {
            if (!link) {
              title = "Link(CoF)";
              link = true;
            }
          }
          let diffNode = getSibN(name, -6);
          let levelNode = getSibN(name, -2);
          let scoreNode = getSibN(name, 2);
          if (scoreNode.tagName !== "div") {
            continue;
          }
          let dxScoreNode = getSibN(name, 4);
          let fsNode = getSibN(name, 6);
          let fcNode = getSibN(name, 8);
          let rateNode = getSibN(name, 10);
          let record_data = {
            title: title,
            level: levelNode.textContent,
            level_index: labels.indexOf(
              diffNode.getAttribute("src").match("diff_(.*).png")[1]
            ),
            type: "",
            achievements: parseFloat(scoreNode.textContent),
            dxScore: parseInt(dxScoreNode.textContent.replace(",", "")),
            rate: rateNode.getAttribute("src").match("_icon_(.*).png")[1],
            fc: fcNode
              .getAttribute("src")
              .match("_icon_(.*).png")[1]
              .replace("back", ""),
            fs: fsNode
              .getAttribute("src")
              .match("_icon_(.*).png")[1]
              .replace("back", ""),
          };
          const docId = name.parentNode.parentNode.parentNode.getAttribute(
            "id"
          );
          if (docId) {
            if (docId.slice(0, 3) == "sta") record_data.type = "SD";
            else record_data.type = "DX";
          } else {
            record_data.type = name.parentNode.parentNode.nextSibling.nextSibling
              .getAttribute("src")
              .match("_(.*).png")[1];
            if (record_data.type == "standard") record_data.type = "SD";
            else record_data.type = "DX";
          }
          records.push(record_data);
        }
        for (let i = 0; i < records.length; i++) {
          records[i].song_id = this.title2id[records[i].title + records[i].type];
        }
        return records;
      } catch (err) {
        console.log(err);
        this.$message.error(
          "导入页面信息出错，请确认您导入的是【记录】-【乐曲成绩】-【歌曲类别】。"
        );
      }
    },
    expertToCSVChuni: function() {
      let text = "排名,乐曲名,难度,定数,分数,Rating\n";
      const escape = function (value) {
        if (value.indexOf(",") >= 0) {
          return value;
        } else {
          return `"${value}"`;
        }
      };
      for (const m of this["chuni_records"]) {
        text += `${m.rank},${escape(m.title)},${m.level},${m.ds},${m.score},${m.ra}\n`;
      }
      const blob = new Blob([
        this.exportEncodingChuni === "GBK" ? new Uint8Array(GBK.encode(text)) : text,
      ]);
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "中二节奏.csv";
      a.click();
    },
    exportToCSV: function (type) {
      let text = "排名,曲名,难度,等级,定数,达成率, DX Rating\n";
      const escape = function (value) {
        if (value.indexOf(",") == -1) {
          return value;
        } else {
          return `"${value}"`;
        }
      };
      for (const m of this[type + "Data"]) {
        text += `${m.rank},${escape(m.title)},${m.level_label},${m.level},${m.ds
          },${m.achievements},${m.ra}\n`;
      }
      const blob = new Blob([
        this.exportEncoding === "GBK" ? new Uint8Array(GBK.encode(text)) : text,
      ]);
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = type == "sd" ? "标准乐谱.csv" : "DX 乐谱.csv";
      a.click();
    },
    logout: function () {
      const setCookie = function (cname, cvalue, exdays) {
        var d = new Date();
        d.setTime(d.getTime() + exdays * 24 * 60 * 60 * 1000);
        var expires = "expires=" + d.toUTCString();
        document.cookie = cname + "=" + cvalue + "; " + expires + ";path=/";
      };
      setCookie("jwt_token", "", -1);
      this.logoutVisible = false;
      this.$message.success("已登出");
      setTimeout("window.location.reload()", 1000);
    },
    available_plates: function () {
      return this.$refs.pq.available_plates();
    },
    setHeaders: function (headers) {
      this.headers = headers;
    },
    changeTable: function (target) {
      this.tableMode = target;
    },
    unlockAllChuni: function() {
      const currentCids = this.chuni_records.map(elem => {return elem.cid});
      let rank = currentCids.length + 1;
      for (const m of this.chuni_data) {
        for (let i = 0; i < m.ds.length; i++) {
          if (currentCids.indexOf(m.cids[i]) != -1) continue;
          if (m.level[i] === "-") continue;
          this.chuni_records.push(
            {
              "rank": rank,
              "ds": m.ds[i],
              "fc": "",
              "title": m.title,
              "level": m.level[i],
              "mid": m.id,
              "cid": m.cid,
              "level_index": i,
              "level_label": ["Basic", "Advanced", "Expert", "Master", "Ultima", "World's End"][i],
              "score": 0,
              "ra": 0.0
            }
          )
          rank++;
        }
      }
      this.allModeVisibleChuni = false;
    }
  },
};
</script>

<style>
#mainPage {
  margin: auto;
  padding: 30px;
}

#tableBody {
  margin-bottom: 2em;
  max-width: calc(100vw - 60px);
}

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

.mid {
  justify-content: space-between;
}

.mbe-2 {
  margin-bottom: 2em;
}
</style>
