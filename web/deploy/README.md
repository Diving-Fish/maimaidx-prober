# Web 静态发布

参考 [CNGoldenLink 的 OSS 发布实现](https://github.com/CNGoldenTopList/CNGoldenLink/blob/main/scripts/upload-oss.py)，使用 `oss2==2.19.1`：

- Bucket：`aliyun-static-diving-fish`
- Endpoint：`https://oss-cn-shanghai.aliyuncs.com`
- CDN：`https://aliyun-static.diving-fish.com`
- 独立前缀：`maimaidx-prober/releases/<commit>-<run-id>-<attempt>/`

CDN、OSS 与本地路径统一配置在 `web/deploy/config.json`；构建自动生成 `asset-manifest.json`，没有手工维护的文件列表。

每次运行使用独立目录，文件禁止覆盖、不删除旧版本；可重试同内容上传。不会上传 source map。构建依赖使用 `web/pnpm-lock.yaml`。

## 首次配置

当前仓库的 Actions Secrets 需要 `OSS_ACCESS_KEY_ID`、`OSS_ACCESS_KEY_SECRET` 和已有 `CI_TOKEN`。其他仓库的 Secrets 不会自动共享。OSS 权限至少允许这个前缀的 PutObject/GetObject（用于校验已存在对象）；不用 DeleteObject，也不需要 Docker Hub 凭据。

CDN 对本项目前缀启用 Brotli/gzip，遵循源站的缓存头。字体响应必须带 `Access-Control-Allow-Origin: *` 或 `https://maimai.diving-fish.com`；若使用 OSS CORS，确保 CDN 透传并正确缓存相关响应头。生产 Action 会检查资源类型和可达性；字体跨域缺失会告警，浏览器可使用本机回退。仍建议正确配置跨域，否则每次冷启动都会先经历一次失败和重载。

后端部署目录默认 `/var/www/maimaidx/web`，可通过 `PROBER_WEB_ROOT` 覆盖（同时调整 Nginx root）。先创建目录并让运行 Python 服务的用户有写权限。安装新的 Python 路由后重启后端；将 `nginx-web.conf` 中的 location 放入 `maimai.diving-fish.com` server，执行 `nginx -t` 后 reload。迁移期间保留旧 8080 容器作 fallback；没有 `current` 时仍提供旧站点。API、文档、封面、favicon 路由保持原样。

## 发布流程

1. push/PR 的 `Web CI` 只测试、构建并上传 Actions artifact，不发布、不调用旧的 Docker 测试页接口。
2. 合并到 main 后，在 main 上手动运行 `Publish Web to OSS`，`sha256` 填写要发布的完整 **40 位 Git commit SHA**（保留旧输入名，它不是 SHA-256 摘要）。提交必须属于 main，且包含新的 `VUE_APP_ASSET_BASE` 构建配置。也可以先推送 main，再推送指向该提交的 `web-deploy-*` 标签触发同一发布流程；普通分支 push 不会自动发布线上。
3. Action 构建所选提交，上传 OSS，然后通过 CDN 检查资源可达性和字体 CORS。
4. 保留 `web-origin-...` artifact（HTML、favicon、release.json），随后将 HTML 作为 POST body 发往 `https://maimai.diving-fish.com/api/maimaidxprober/ci/production?release=<release-id>`，使用 `Authorization: Bearer <CI_TOKEN>`。
5. `/ci/production` 验证版本、HTML 大小和资源地址，从固定 CDN 地址下载清单及全部资源，并逐文件校验大小和 SHA-256。下载不涉及浏览器 CORS；任何下载或校验失败都不切换线上。
6. 服务端在临时目录生成 `index.local.html` 和本地 CSS（字体、图片 URL 指向同源版本目录），全部完成后写入版本目录并原子切换 `current`。部署跨 worker 加锁；不启动/停止 Docker、不修改 Nginx。`/ci/status` 返回当前版本。
7. Action 请求线上 HTML，与本次构建产物逐字节比较，确认切换成功。

旧的 GET `/ci/production?sha=...` 不再切换 Docker，返回 405。文档构建等现有 CI 接口继续支持 query token。

## 浏览器回退

HTML 头部的小型保护脚本先于外部资源执行，统一捕获本版本 CDN 的脚本/样式加载错误、字体加载错误和异步 chunk 加载错误。出错时只重载一次，打开 `/web-assets/<release>/index.local.html`；随后恢复用户原来的同源地址。不会按文件逐个尝试不同镜像。

本地入口将所有构建资源指向同源 `/web-assets/<release>/`。`asset-path.js` 使用 Webpack 的 `__webpack_public_path__` 让后续异步 chunk 也走本机。本地 CSS 内的字体/图片路径同步改为本机。进入本机模式后不再安装回退监听，避免循环重载；同一版本的 CDN 与本机文件不会混用。

重载会重新初始化页面状态；持续挂起但尚未报错的请求不会触发回退。目前只针对明确的资源加载失败，不做时间阈值猜测。正常 CDN 模式不额外下载本机资源，磁盘中保留完整副本供故障与回滚使用。

## 回滚

从 Actions artifact 取出旧版本的 `index.html`，以其原来的 release ID 再次 POST 到同一接口即可。服务器拒绝以相同 release ID 替换不同 HTML；旧 HTML 引用的 OSS 资源必须保留。部署失败时保留旧 `current`，新建但未启用的版本不影响线上。

首次切换成功后，确认旧资源请求不再需要 Docker fallback，再移除 fallback 和旧容器。当前修改不自动清理旧容器或 OSS 文件。

## 本地验证

```sh
node --test web/scripts/test-fallback.cjs
python -B -m unittest discover -s web/scripts -p 'test_*.py'
database/venv/bin/python -B -m unittest discover -s database/tests -p 'test_web_release.py'
pnpm --dir web install --frozen-lockfile
VUE_APP_ASSET_BASE=https://aliyun-static.diving-fish.com/maimaidx-prober/releases/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-1-1/ pnpm --dir web build
python web/scripts/upload_oss.py web/dist --release aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-1-1 --dry-run
```
