---
sidebar_position: 2
---

# ShadowRocket 模块导入

此功能需要 iOS 系统设备，并下载 ShadowRocket（俗称小火箭）之后才能使用。

## 配置 ShadowRocket

### 开启 HTTPS 解密

打开 ShadowRocket 主页，点击下方的【配置】，点击本地文件打勾的配置右边的圈i，进入之后点击【HTTPS 解密】

<img src={require('/img/shadowrocket-1.jpg').default} width="45%" />
<img src={require('/img/shadowrocket-2.jpg').default} width="45%" />

打开 HTTPS 解密选项，系统会提示你生成新的 CA 证书。

<img src={require('/img/shadowrocket-3.jpg').default} width="45%" />
<img src={require('/img/shadowrocket-4.jpg').default} width="45%" />

点击证书 -> 安装证书，系统会跳转到安装描述文件，点击右上角的【安装】

<img src={require('/img/shadowrocket-5.jpg').default} width="45%" />

之后，前往设置 -> 关于本机，划到最下面，点击证书信任设置，信任刚刚添加的 ShadowRocket 证书：

<img src={require('/img/shadowrocket-6.png').default} width="45%" />
<img src={require('/img/shadowrocket-7.jpg').default} width="45%" />

回到 ShadowRocket 界面，应该会显示证书已信任，如下图所示：

<img src={require('/img/shadowrocket-8.jpg').default} width="45%" />

### 导入模块

打开查分器网页，前往【编辑个人资料】界面，点击导入 Token 右侧的小火箭图标复制链接：

<img src={require('/img/shadowrocket-11.png').default} width="60%" />

打开 ShadowRocket 主页，点击下方的【配置】，点击【模块】：

<img src={require('/img/shadowrocket-12.jpg').default} width="45%" />

之后，点击右上角的加号，粘贴刚刚的链接到对话框中，如果导入了【舞萌数据转发】模块，则大功告成了。

<img src={require('/img/shadowrocket-9.jpg').default} width="45%" />

## 导入成绩

开启你的 ShadowRocket 服务，一般情况下选择【直连】模式即可。

打开手机微信，进入公众号，依次点击 记录 -> 乐曲成绩 -> 排序，依次点击六个等级（如果无需导入某等级可以不点），并等待网页加载完成。

<img src={require('/img/shadowrocket-10.jpg').default} width="60%" />

如果一切顺利的话，此时登录查分器网页，即可查看最新导入的成绩。

## 其他代理软件

使用 Surge / QuantumultX / Loon / Stash 等软件也可以达成同样功能，都需要以下几步：
1. 开启 HTTPS 解密 ( 或者 Mitm )
2. 安装并信任证书
3. 安装模块 ( 或者叫插件 / 配置 ) 并启用