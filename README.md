# 舞萌 DX 查分器

本查分器仅用于推分指导用途，不保证歌曲定数、DX Rating、难度 100% 准确。

## 使用指南

[新版文档](https://maimai.diving-fish.com/manual/)

## <span id="FAQ">常见问题（FAQ）</span>

> 为什么我查分器创建了账号，还是没有数据？

您需要自行按照查分器上的教程进行数据导入。查分器并没有能力从华立官方获取您的数据。

> config.json文件应该怎么修改？

用任何文本编辑器（包括记事本），将 [生成的成绩导入 Token](https://maimai.diving-fish.com/manual/docs/intro#%E5%AE%8C%E6%88%90%E8%AE%BE%E7%BD%AE%E5%B9%B6%E7%94%9F%E6%88%90%E5%AF%BC%E5%85%A5-token) 写入对应区域的引号中，类似这样：

```
{"token": "802f48105e7dbdd3c107cae68fd5f0fa4a6966b15795fbc2bb812ffc07aae023e39910fd3d06e2b0998e24154c7bb5f2714c7c4639e6c1b97e612d771832803d"}
```

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

爱发电：https://afdian.com/a/divingfish

### License & Disclaimer

MIT

本查分器与华立、SEGA 等公司无任何关系，注册商标所有权归相关品牌所有。请勿使用本代码用于网络攻击或其他滥用行为。
