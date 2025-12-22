---
sidebar_position: 1
---

# 代理软件导入

视频教程：[Windows](https://www.bilibili.com/video/BV1Ua411t7Em) | [Mac OS](https://www.bilibili.com/video/BV14v411L7mG)

## 配置代理软件

您可以访问[此链接](https://github.com/Diving-Fish/maimaidx-prober/releases)来下载最新版本的代理工具，文件名为**maimaidx-prober-proxy-(os).exe**（os指您的操作系统）。

> 一般来说，使用 windows 系统的玩家都可以下载 windows-amd64.exe 后缀的文件。

请将代理工具复制到一个空文件夹中，然后双击或使用控制台运行。初次运行后，代理工具将在当前目录下创建 3 个文件：

|文件名|说明|
|------|----|
|`config.json`|配置文件|
|`cert.crt`|可以导入的证书文件|
|`key.pem`|私钥文件，无需进行任何操作|

双击 cert.crt 文件打开，点击**安装证书**，打开证书导入向导。一般情况下，只需要对当前用户安装证书即可。之后点击下一步，按照如图选择将此证书放入“受信任的根证书颁发机构”进行存储。接下来，一路选择**是**，直到提示证书导入完成。

![](https://www.diving-fish.com/images/maimaidx-prober/1.png)

<details>
  <summary>Mac OS 系统的设置</summary>

*在 Mac OS 或者 Linux 上运行，请打开 Shell 输入如下的命令：*
```plain
chmod +x <文件名>
./<文件名>
```
*如果 Mac OS 提示“不受信任的开发者”，请自行百度解决办法。*

*在 Mac OS 系统上，请将钥匙串加入"系统"中，并双击打开证书详情，在信任子菜单下调整设置，如下所示：*

![](https://www.diving-fish.com/images/maimaidx-prober/9.png)

PS：不懂就直接看视频教程吧
</details>

之后，填写`config.json`文件。使用记事本、Notepad++ 或 VS Code 等文本编辑器打开`config.json`，并将 [刚刚生成的成绩导入 Token](/docs/intro.md#完成设置并生成导入-token) 写入对应区域的引号中，类似这样：

```json
{"token": "802f48105e7dbdd3c107cae68fd5f0fa4a6966b15795fbc2bb812ffc07aae023e39910fd3d06e2b0998e24154c7bb5f2714c7c4639e6c1b97e612d771832803d"}
```

此时，打开代理程序，控制台应该会提示：

```
2025/11/06 17:51:12 INFO: 登录成功
2025/11/06 17:51:12 INFO: 使用此软件则表示您同意共享您在微信公众号舞萌 DX、中二节奏中的数据。
2025/11/06 17:51:12 INFO: 您可以在微信客户端访问微信公众号舞萌 DX、中二节奏的个人信息主页进行分数导入，如需退出请直接关闭程序或按下 Ctrl + C
2025/11/06 17:51:12 INFO: 代理设置已自动修改。
2025/11/06 17:51:12 INFO: 代理已开启到 127.0.0.1:8033
```

## 导入数据

默认情况下，代理工具将会自行更改您的系统代理。如果打开代理程序后提示

```
2025/11/06 17:51:12 WARN: 自动修改代理设置失败。请尝试手动修改代理。
```

请按照折叠的部分进行操作。

<details>

  <summary>点击展开</summary>

*以下为Windows 10 系统的代理服务器设置方法。如果您的系统是Windows 10以外的Windows系统（如Windows 7），您可以自行搜索相应系统的代理服务器设置方法。*

打开代理程序后，在 Windows 设置中搜索**代理服务器设置**，进入设置界面，将设置调整如下图所示，之后点击保存。

![](https://www.diving-fish.com/images/maimaidx-prober/3.png)

*如果您使用了其他的系统代理软件（ Shadowsocks、V2Ray 等），请将它们关闭或调整至直连模式再进行设置。*

</details>

*Linux 系统不支持自动修改代理，请自行查找代理修改方法。需要修改 HTTP/HTTPS 的代理，代理 URL 均为 127.0.0.1:8033。*

打开**电脑版微信**，进入舞萌 DX 公众号，点击**我的记录**。如果您的代理设置无误，页面将如下图显示：

![](https://www.diving-fish.com/images/maimaidx-prober/4.png)

切换到代理服务器的控制台界面，它将输出如下的内容：

```
2025/11/06 17:54:02 INFO: 正在导入 Basic 难度……
2025/11/06 17:54:03 INFO: 导入成功
2025/11/06 17:54:03 INFO: 正在导入 Advanced 难度……
2025/11/06 17:54:04 INFO: 导入成功
2025/11/06 17:54:04 INFO: 正在导入 Expert 难度……
2025/11/06 17:54:05 INFO: 导入成功
2025/11/06 17:54:05 INFO: 正在导入 Master 难度……
2025/11/06 17:54:07 INFO: 导入成功
2025/11/06 17:54:07 INFO: 正在导入 Re: MASTER 难度……
2025/11/06 17:54:07 INFO: 导入成功
2025/11/06 17:54:07 INFO: 正在导入 UTAGE 难度……
2025/11/06 17:54:08 INFO: 导入成功
```

在导入完毕后，刷新查分器界面，即可看到最新的乐曲成绩。

如果您需要更新您的成绩数据，无需重新配置代理软件，只需启动之后再次打开**电脑版微信**，进入舞萌 DX 公众号，点击**我的记录**即可。