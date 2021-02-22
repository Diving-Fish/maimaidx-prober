# 舞萌 DX 查分器

本查分器仅用于推分指导用途，不保证歌曲定数、DX Rating、难度 100% 准确。此外，部分歌曲暂无定数数据，如有准确数据欢迎提供。

### 使用指南

<details>
<summary>可以使用网页版微信的用户请查看此部分(点击展开)</summary>
&nbsp;

用任意浏览器访问如下网址：https://tgk-wcaime.wahlap.com/wc_auth/oauth/authorize/maimai-dx

然后 URL 会被重定向到 **https://open.weixin.qq.com/connect/oauth2/authorize** (后面的查询参数省略掉了)。

之后，在网页版微信的任何聊天框中粘贴刚刚的 URL，如下图所示：

![](https://www.diving-fish.com/images/maimaidx-prober/4.png)

之后点击这个链接即可。如果一切顺利的话，浏览器中将进入舞萌 DX 的主页。如果提示**Not Found**，有可能是操作慢了一点，可以再试一次！

![](https://www.diving-fish.com/images/maimaidx-prober/5.png)

接下来，导航至【记录】-【乐曲成绩】，在上方选择难度后，点击 *Ctrl+U* 或右键获取源代码。

![](https://www.diving-fish.com/images/maimaidx-prober/6.png)
</details>
&nbsp;
<details>
<summary>不能使用网页版微信的用户请查看此部分(点击展开)</summary>
&nbsp;

使用电脑版微信打开【舞萌DX】公众号，点击底部【我的记录】，在打开的页面中导航至【记录】-【乐曲成绩】。
  
在下方乐曲成绩中选择难度后，右击鼠标并点击【获取源代码】（如果右击无效可以往下滑动一些再右击），复制源代码到剪切板中。

![](https://www.diving-fish.com/images/maimaidx-prober/1.png)

![](https://www.diving-fish.com/images/maimaidx-prober/2.png)
</details>
&nbsp;

*您同样可以使用 Fiddler 等抓包工具实现获取网页的源代码。*

将网页的源代码复制到查分器中，点击上方【导入数据】按钮，粘贴源代码，之后点击确认。

因为每次只能导入一个乐曲难度，所以如果需要导入所有成绩，一共需要进行五次不同难度的导入操作（*其实一般导入红、紫、白谱就OK*），之后乐曲会出现在下方表格中。

![](https://www.diving-fish.com/images/maimaidx-prober/3.png)


### License & Disclaimer

MIT

本查分器与华立、SEGA 等公司无任何关系，注册商标所有权归相关品牌所有。请勿使用本代码用于网络攻击或其他滥用行为。
