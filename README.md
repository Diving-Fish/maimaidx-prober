# 舞萌 DX 查分器

本查分器仅用于推分指导用途，不保证歌曲定数、DX Rating、难度 100% 准确。此外，部分歌曲暂无定数数据，如有准确数据欢迎提供。

## 使用指南

*开始之前，建议您先注册一个查分器账户。借由此账户，您可以快捷地利用代理工具导入您的成绩数据。*

如果你在使用过程中遇到任何问题，请先查阅本文末尾的[FAQ](#FAQ)。如果FAQ不能解决您的问题，并且您无法通过查阅其他资料自行解决，欢迎加入舞萌DX查分器交流群（981682758）询问。

### 方法1：通过代理工具导入数据（推荐）

**感谢舞台酱对此代理工具的大力帮助。**

#### 1. 准备工作

您可以访问[此链接](https://github.com/Diving-Fish/maimaidx-prober/releases)来下载最新版本的代理工具，文件名为**maimaidx-prober-proxy-(os).exe**（os指您的操作系统）。

请将代理工具复制到一个空文件夹中，然后点击运行。初次运行后，代理工具将在当前目录下创建 3 个文件：

|文件名|说明|
|------|----|
|`config.json`|用户名和密码的配置文件|
|`cert.crt`|可以导入的证书文件|
|`key.pem`|私钥文件，无需进行任何操作|

*在 Mac OS 或者 Linux 上运行，请打开 Shell 输入如下的命令：*
```plain
chmod +x <文件名>
./<文件名>
```
*如果 Mac OS 提示“不受信任的开发者”，请自行百度解决办法。*

双击 cert.crt 文件打开，点击**安装证书**，打开证书导入向导。一般情况下，只需要对当前用户安装证书即可。之后点击下一步，按照如图选择将此证书放入“受信任的根证书颁发机构”进行存储。接下来，一路选择**是**，直到提示证书导入完成。

![](https://www.diving-fish.com/images/maimaidx-prober/1.png)

*在 Mac OS 系统上，请将钥匙串加入"系统"中，并双击打开证书详情，在信任子菜单下调整设置，如下所示：*

![](https://www.diving-fish.com/images/maimaidx-prober/9.png)

之后，填写`config.json`文件。使用记事本、Notepad++或Sublime Text等文本编辑器打开`config.json`，并将您查分器的用户名（假如是`MyAccount`）和密码（假如是`MyPassword`）写入对应区域的引号中，类似这样：

```json
{"username": "MyAccount", "password": "MyPassword"}
```

此时，打开代理程序，控制台应该会提示：

```plain
登录成功，代理已开启到127.0.0.1:8033
代理设置已自动修改。
```

#### 2. 导入数据

默认情况下，代理工具将会自行更改您的系统代理。如果打开代理程序后提示

```plain
自动修改代理设置失败。请尝试手动修改代理。
```

请按照折叠的部分进行操作。

<details>

<summary>点击展开</summary>
&nbsp;

*以下为Windows 10 系统的代理服务器设置方法。如果您的系统是Windows 10以外的Windows系统（如Windows 7），您可以自行搜索相应系统的代理服务器设置方法。*

打开代理程序后，在 Windows 设置中搜索**代理服务器设置**，进入设置界面，将设置调整如下图所示，之后点击保存。

![](https://www.diving-fish.com/images/maimaidx-prober/3.png)

*如果您使用了其他的系统代理软件（ Shadowsocks、V2Ray 等），请将它们关闭或调整至直连模式再进行设置。*

</details>
&nbsp;

*Mac OS 系统或 Linux 系统不支持自动修改代理，请自行查找代理修改方法。需要修改 HTTP/HTTPS 的代理，代理 URL 均为 127.0.0.1:8033。*

打开**电脑版微信**，进入舞萌 DX 公众号，点击**我的记录**。如果您的代理设置无误，页面将如下图显示：

![](https://www.diving-fish.com/images/maimaidx-prober/4.png)

切换到代理服务器的控制台界面，它将输出如图所示的内容：

![](https://www.diving-fish.com/images/maimaidx-prober/5.png)

在导入完毕后，刷新查分器界面，即可看到最新的乐曲成绩。

如果您需要更新您的成绩数据，只需要做第 2 步便可。

### 方法2：通过源代码导入数据（仅限网页版微信）

用任意浏览器访问如下网址：https://tgk-wcaime.wahlap.com/wc_auth/oauth/authorize/maimai-dx

然后 URL 会被重定向到 **https://open.weixin.qq.com/connect/oauth2/authorize** (后面的查询参数省略掉了)。

之后，在网页版微信的任何聊天框中粘贴刚刚的 URL，如下图所示：

![](https://www.diving-fish.com/images/maimaidx-prober/8.png)

之后点击这个链接即可。如果一切顺利的话，浏览器中将进入舞萌 DX 的主页。如果提示**Not Found**，有可能是操作慢了一点，可以再试一次！

![](https://www.diving-fish.com/images/maimaidx-prober/7.png)

接下来，导航至【记录】-【乐曲成绩】，在上方选择难度后，点击 *Ctrl+U* 或右键获取源代码。

![](https://www.diving-fish.com/images/maimaidx-prober/6.png)

使用**Ctrl+A**全选获取的源代码，并复制到剪切板中。进入查分器主页，点击**导入数据**，将源代码粘贴到输入框中，点击导入。

## 方法3：通过手机微信导入

*该方法仅支持安卓系统*

复制如下三个网址，并在微信中发送给任何一个人：

debugmm.qq.com/?forcex5=true  
http://debugtbs.qq.com  
http://debugx5.qq.com

从上到下依次打开各链接。打开第三个链接后，选择顶部的信息一栏，在下面勾选`打开vConsole调试功能`。

之后，在用微信打开任意网页时，底部都会出现一个里面写着vConsole的绿框。觉得不好看可以在导入完之后取消上面的勾选。

进入舞萌DX公众号，导航至记录-乐曲成绩，选择难度后点击页面最下方vConsole。此时页面会弹出一个窗口。

将以下代码复制粘贴至下方command输入框，然后把`username`和`password`改为你自己的查分器用户名和密码，点击右侧OK按钮：

```
$.ajax({
    url: 'https://www.diving-fish.com/api/pageparser/page',
    type: 'POST',
    data: "<login><u>username</u><p>password</p></login>" + document.getElementsByTagName('html')[0].innerHTML,
    contentType: 'text/plain',
    success: (res) => console.log(res)
})
```

上方窗口显示message success即导入成功。

至此，数据导入教程结束，您可以在查分器主页看到您的成绩数据。

![](https://www.diving-fish.com/images/maimaidx-prober/10.png)

## <span id="FAQ">常见问题（FAQ）</span>

> 为什么我查分器创建了账号，还是没有数据？

您需要自行按照查分器上的教程进行数据导入。查分器并没有能力从华立官方获取您的数据。

> config.json文件应该怎么修改？

用任何文本编辑器（包括记事本），替换myaccount和mypassword为您的账号密码。

> 为什么我在电脑版微信中点击“舞萌DX”公众号中的“我的记录”会自动跳转到浏览器，并显示“请在微信客户端中打开链接”？

进入电脑版微信右下角菜单 - 【设置】 - 【通用设置】- 取消勾选【使用系统默认浏览器打开网页】。现在微信应该会在内置浏览器中打开“我的记录”网页。

> 为什么我的代理工具程序窗口中有一条`... WARN: Error copying to client: ...`？

这只是一个程序警告，不影响代理工具的正常运行，请自动忽略掉这条警告。如果代理工具出现错误，这条警告也基本与错误无关。

> 为什么我在使用代理工具后，打开任何网页都显示“代理服务器错误”？

程序在退出时没能关闭你的系统代理。进入你的系统代理服务器设置并关闭即可。

#### 请作者打一局maimai？

<details>
<summary>点击展开收款码</summary>
<img style="width: 48%" src="https://www.diving-fish.com/images/qrcode/alipay_qrcode.jpg">
<img style="width: 50%" src="https://www.diving-fish.com/images/qrcode/wechat_qrcode.jpg">
</details>

### License & Disclaimer

MIT

本查分器与华立、SEGA 等公司无任何关系，注册商标所有权归相关品牌所有。请勿使用本代码用于网络攻击或其他滥用行为。
