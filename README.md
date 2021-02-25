# 舞萌 DX 查分器

本查分器仅用于推分指导用途，不保证歌曲定数、DX Rating、难度 100% 准确。此外，部分歌曲暂无定数数据，如有准确数据欢迎提供。

## 使用指南

*开始之前，建议您先注册一个查分器账户。借由此账户，您可以快捷地利用代理工具导入您的成绩数据。*

### 通过代理工具导入数据（推荐）

**感谢舞台酱对此代理工具的大力帮助。**

#### 1. 准备工作

您可以访问[此链接](https://github.com/Diving-Fish/maimaidx-prober/releases)来下载最新版本的代理工具，文件名为**maimaidx-prober-proxy.exe**。*如果您是 Windows 以外的操作系统，可以自行编译 `/proxy` 下的文件来获得可运行的程序。*

请将代理工具复制到一个空文件夹中，然后点击运行。初次运行后，代理工具将创建 3 个文件：
```c
config.json - 用户名和密码的配置文件
cert.crt - 可以导入的证书文件
key.pem - 私钥文件，无需进行任何操作
```

首先，双击 cert.crt 文件打开，点击**安装证书**，打开证书导入向导。一般情况下，只需要对当前用户安装证书即可。之后点击下一步，按照如图选择将此证书放入“受信任的根证书颁发机构”进行存储。接下来，一路选择**是**，直到提示证书导入完成。

![](https://www.diving-fish.com/images/maimaidx-prober/1.png)

之后，填写`config.json`文件，将您的用户名和密码写入对应区域的引号中，类似这样：

```json
{"username": "MyAccount", "password": "MyPassword"}
```

此时，打开代理程序，控制台应该会提示：
```c
登录成功，代理已开启到127.0.0.1:8033
```

#### 2. 导入数据

打开代理程序后，在 Windows 设置中搜索**代理服务器设置**，进入设置界面，将设置调整如下图所示：

![](https://www.diving-fish.com/images/maimaidx-prober/3.png)

*如果您使用了其他的系统代理软件（Shadowsocks、V2Ray 等），请将它们关闭或调整至直连模式再进行设置。*

点击保存，打开**电脑版微信**，进入舞萌 DX 公众号，点击**我的记录**。如果您的代理设置无误，页面将如下图显示：

![](https://www.diving-fish.com/images/maimaidx-prober/4.png)

切换到代理服务器的控制台界面，它将输入如图所示的内容：

![](https://www.diving-fish.com/images/maimaidx-prober/5.png)

在导入完毕后，刷新查分器界面，即可看到最新的乐曲成绩。关闭代理程序后，别忘了在【代理服务器设置】中恢复以前的设置。

如果您需要更新您的成绩数据，只需要做第 2 步便可。

### 通过源代码导入数据（仅限网页版微信）

用任意浏览器访问如下网址：https://tgk-wcaime.wahlap.com/wc_auth/oauth/authorize/maimai-dx

然后 URL 会被重定向到 **https://open.weixin.qq.com/connect/oauth2/authorize** (后面的查询参数省略掉了)。

之后，在网页版微信的任何聊天框中粘贴刚刚的 URL，如下图所示：

![](https://www.diving-fish.com/images/maimaidx-prober/8.png)

之后点击这个链接即可。如果一切顺利的话，浏览器中将进入舞萌 DX 的主页。如果提示**Not Found**，有可能是操作慢了一点，可以再试一次！

![](https://www.diving-fish.com/images/maimaidx-prober/7.png)

接下来，导航至【记录】-【乐曲成绩】，在上方选择难度后，点击 *Ctrl+U* 或右键获取源代码。

![](https://www.diving-fish.com/images/maimaidx-prober/6.png)

使用**Ctrl+A**全选获取的源代码，并复制到剪切板中。进入查分器主页，点击**导入数据**，将源代码粘贴到输入框中，点击导入。

至此，数据导入教程结束，您可以在查分器主页看到您的成绩数据。

![](https://www.diving-fish.com/images/maimaidx-prober/10.png)

#### 请作者打一局maimai？

<details>
<summary>点击展开收款码</summary>
<img src="https://www.diving-fish.com/images/qrcode/alipay_qrcode.jpg">
<img src="https://www.diving-fish.com/images/qrcode/wechat_qrcode.jpg">
</details>

### License & Disclaimer

MIT

本查分器与华立、SEGA 等公司无任何关系，注册商标所有权归相关品牌所有。请勿使用本代码用于网络攻击或其他滥用行为。
