# 舞萌 DX 查分器

本查分器仅用于推分指导用途，不保证歌曲定数、DX Rating、难度 100% 准确。

## 使用指南

*开始之前，建议您先注册一个查分器账户。借由此账户，您可以快捷地利用代理工具导入您的成绩数据。*

如果你在使用过程中遇到任何问题，请先查阅本文末尾的[FAQ](#FAQ)。如果FAQ不能解决您的问题，并且您无法通过查阅其他资料自行解决，欢迎加入我们的[QQ频道](https://qun.qq.com/qqweb/qunpro/share?_wv=3&_wwv=128&appChannel=share&biz=ka&businessType=5&from=181075&inviteCode=20DoWXWylop&mainSourceId=qr_code&subSourceId=pic4&jumpsource=shorturl#/out)询问。

### 方法1：通过代理工具导入数据（推荐）

**感谢舞台酱对此代理工具的大力帮助。**

视频教程：

Windows: [https://www.bilibili.com/video/BV1Ua411t7Em](https://www.bilibili.com/video/BV1Ua411t7Em)

Mac OS: [https://www.bilibili.com/video/BV14v411L7mG](https://www.bilibili.com/video/BV14v411L7mG)

@Bakapiano 的互联网代理方式: [https://www.bilibili.com/video/BV1pT411G7U1](https://www.bilibili.com/video/BV1pT411G7U1)

#### 1. 准备工作

您可以访问[此链接](https://github.com/Diving-Fish/maimaidx-prober/releases)来下载最新版本的代理工具，文件名为**maimaidx-prober-proxy-(os).exe**（os指您的操作系统）。

请将代理工具复制到一个空文件夹中，然后双击或使用控制台运行。初次运行后，代理工具将在当前目录下创建 3 个文件：

|文件名|说明|
|------|----|
|`config.json`|用户名和密码的配置文件|
|`cert.crt`|可以导入的证书文件|
|`key.pem`|私钥文件，无需进行任何操作|

双击 cert.crt 文件打开，点击**安装证书**，打开证书导入向导。一般情况下，只需要对当前用户安装证书即可。之后点击下一步，按照如图选择将此证书放入“受信任的根证书颁发机构”进行存储。接下来，一路选择**是**，直到提示证书导入完成。

![](https://www.diving-fish.com/images/maimaidx-prober/1.png)

<details>

<summary>Mac OS 系统的设置（点击展开）</summary>
&nbsp;

*在 Mac OS 或者 Linux 上运行，请打开 Shell 输入如下的命令：*
```plain
chmod +x <文件名>
./<文件名>
```
*如果 Mac OS 提示“不受信任的开发者”，请自行百度解决办法。*

*在 Mac OS 系统上，请将钥匙串加入"系统"中，并双击打开证书详情，在信任子菜单下调整设置，如下所示：*

![](https://www.diving-fish.com/images/maimaidx-prober/9.png)

</details>
&nbsp;



之后，填写`config.json`文件。使用记事本、Notepad++或Sublime Text等文本编辑器打开`config.json`，并将您查分器的用户名（假如是`MyAccount`）和密码（假如是`MyPassword`）写入对应区域的引号中，类似这样：

```json
{"username": "MyAccount", "password": "MyPassword"}
```

此时，打开代理程序，控制台应该会提示：

```plain
2023/07/04 16:55:06 INFO: 您使用的是最新版本。
2023/07/04 16:55:06 INFO: 登录成功
2023/07/04 16:55:06 INFO: 使用此软件则表示您同意共享您在微信公众号舞萌 DX、中二节奏中的数据。
2023/07/04 16:55:06 INFO: 您可以在微信客户端访问微信公众号舞萌 DX、中二节奏的个人信息主页进行分数导入，如需退出请直接关闭程序或按下 Ctrl + C
2023/07/04 16:55:06 INFO: 代理设置已自动修改。
2023/07/04 16:55:06 INFO: 代理已开启到 127.0.0.1:8033
```

#### 2. 导入数据

默认情况下，代理工具将会自行更改您的系统代理。如果打开代理程序后提示

```plain
2023/07/04 16:54:56 WARN: 自动修改代理设置失败。请尝试手动修改代理。
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

*Linux 系统不支持自动修改代理，请自行查找代理修改方法。需要修改 HTTP/HTTPS 的代理，代理 URL 均为 127.0.0.1:8033。*

打开**电脑版微信**，进入舞萌 DX 公众号，点击**我的记录**。如果您的代理设置无误，页面将如下图显示：

![](https://www.diving-fish.com/images/maimaidx-prober/4.png)

切换到代理服务器的控制台界面，它将输出如下的内容：

```plain
2023/07/04 16:55:06 INFO: 您使用的是最新版本。
2023/07/04 16:55:06 INFO: 登录成功
2023/07/04 16:55:06 INFO: 使用此软件则表示您同意共享您在微信公众号舞萌 DX、中二节奏中的数据。
2023/07/04 16:55:06 INFO: 您可以在微信客户端访问微信公众号舞萌 DX、中二节奏的个人信息主页进行分数导入，如需退出请直接关闭程序或按下 Ctrl + C
2023/07/04 16:55:06 INFO: 代理设置已自动修改。
2023/07/04 16:55:06 INFO: 代理已开启到 127.0.0.1:8033
2023/07/04 16:55:37 INFO: 正在导入 Basic 难度……
2023/07/04 16:55:38 INFO: 导入成功
2023/07/04 16:55:40 INFO: 正在导入 Advanced 难度……
2023/07/04 16:55:41 INFO: 导入成功
2023/07/04 16:55:41 INFO: 正在导入 Expert 难度……
2023/07/04 16:55:43 INFO: 导入成功
2023/07/04 16:55:43 INFO: 正在导入 Master 难度……
2023/07/04 16:55:45 INFO: 导入成功
2023/07/04 16:55:45 INFO: 正在导入 Re: MASTER 难度……
2023/07/04 16:55:46 INFO: 导入成功
```

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

## 方法3：通过Chrome调试工具导入

*该方法仅支持安卓系统，且需要安装Chrome的计算机*

在无法使用前三种方法时，可尝试使用此方法

开启设备上的`USB调试`功能并连接电脑

在电脑上的Chrome打开 chrome://inspect

在手机上确认授权后，即可在此列表中看见自己的设备

![image](https://user-images.githubusercontent.com/22652631/224410009-6b6ebc61-5b49-448f-b312-3b05574e5a5c.png)

之后，在手机微信上需打开成功一次如下网址，才能正常使用inspect功能

> http://debugxweb.qq.com/?inspector=true


完成以上步骤后，在手机上打开舞萌DX主页。此时，此列表中将会出现以下内容

![image](https://user-images.githubusercontent.com/22652631/224410727-3c377d36-1d3e-436e-8437-9d48f46a6455.png)

请点击`inspect`，并在红框标识处粘贴如下代码，然后把`USERNAME`和`PASSWORD`改为你自己的查分器用户名和密码，并按下回车

```javascript
((u,p)=>[0,1,2,3,4].reduce(async(promise, diff)=>{
  await promise
  var diffName = ['Basic', 'Advanced', 'Expert', 'Master', 'Re:Master'][diff]
  var url = 'https://maimai.wahlap.com/maimai-mobile/record/musicGenre/search/?genre=99&diff='+diff
  return fetch(url)
  .then(r => {if(r.url!=url)throw new Error(diffName+' 获取分数出错');return r.text()})
  .then(res => fetch('https://www.diving-fish.com/api/pageparser/page', {
    method: 'POST',
    headers:(new Headers({'Content-Type':'text/plain'})),
    body: "<login><u>"+u+"</u><p>"+p+"</p></login>" + res.match(/<html.*>([\s\S]*)<\/html>/)[1].replace(/\s+/g,' ')
  }))
  .then(r => r.json())
  .then(res => {console.log(diffName, res.message, res);if(res.message!='success')throw new Error(diffName+' 上传分数出错')})
}, Promise.resolve()))
("USERNAME", "PASSWORD");
```


![image](https://user-images.githubusercontent.com/22652631/224410943-43d3efc9-fab9-404c-84b8-10c7efd5e0eb.png)

**至此，数据导入教程结束，您可以在查分器主页看到您的成绩数据。**

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

> 如果我想使用不同的端口或者仅导入某一个难度怎么办？

可以使用代理工具的命令行参数（需要 1.3.0 以上的版本）：

| Arg | Default Value | Description | 
| --- | --- | --- |
| v | false | should every proxy request be logged to stdout |
| addr | :8033 | proxy listen address |
| config | config.json | path to config.json file |
| no-edit-global-proxy | false | don't edit the global proxy settings |
| timeout | 30 | timeout when connect to servers |
| mai-diffs |  | mai diffs to import | 

对于 mai-diffs 而言，您可以使用逗号连接的字符串来指定需要导入的难度，字符串的内容可以是以下三者之一
0 - 难度等级索引
bas - 难度等级缩写
basic - 难度等级

例如
```
./executable_file_path -mai-diffs mas,4
``` 
即可导入 Master 和 Re: MASTER 难度。如果留空的话则默认导入所有难度，您也可以在 json 文件中添加
```json5
{
    ...,
    "mai_diffs": ["bas", "adv", "exp"]
}
```
来导入指定难度。

> 为什么我在使用代理工具后，打开任何网页都显示“代理服务器错误”？

程序在退出时没能关闭你的系统代理。进入你的系统代理服务器设置并关闭即可。

### 捐赠

爱发电：https://afdian.net/a/divingfish

### License & Disclaimer

MIT

本查分器与华立、SEGA 等公司无任何关系，注册商标所有权归相关品牌所有。请勿使用本代码用于网络攻击或其他滥用行为。
