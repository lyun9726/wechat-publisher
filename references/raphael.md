# Raphael 带图交付

## 构建导入稿

`article.md` 保留标题、摘要和相对图片路径，便于阅读和迁移。运行 `build_raphael.py` 后，`article-raphael.md` 会移除 H1 与摘要，并把本地图片变成 data URL。

如果浏览器自动化能直接从文件或系统剪贴板粘贴大文本，优先导入 data URL 版本。这样 Raphael 页面关闭本地服务后仍能显示图片。

## 浏览器只能使用虚拟剪贴板时

大段 base64 可能无法通过工具参数传入。可以临时制作一个使用本地 HTTP 图片地址的紧凑稿，并运行：

```bash
python3 scripts/serve_assets.py runs/<slug> --port 8765
```

服务会增加 `Access-Control-Allow-Origin: *`，让 Raphael 的图片打包逻辑能够读取图片。导入紧凑稿以后按下面顺序操作。

1. 确认预览中的每张图 `complete=true` 且 `naturalWidth>0`。
2. 点击“复制到公众号”，等待图片打包完成。
3. 读取剪贴板 HTML，确认所有图片已经是 `data:image`。
4. 为了让 Raphael 页面脱离本地服务仍能工作，把刚复制的富文本重新粘贴回编辑区。Raphael 会把图片转成 data URL Markdown。
5. 再点一次“复制到公众号”，进行最终审计。
6. 只有最终 HTML 不含本地地址时，才关闭本地服务。

Python 自带的普通 `http.server` 没有 CORS 响应头，会导致 Raphael 预览正常、复制后仍保留本地图片地址。必须使用随 Skill 提供的 `serve_assets.py` 或等价的 CORS 服务。

## 真实输入事件

不能只在页面内部无事件地修改输入框值。使用真实粘贴、键盘输入、Playwright `fill` 或能触发框架输入事件的等价操作。修改后再次读取编辑区长度与正文指纹。

## 硬验收

最终剪贴板以 `text/html` 为准，至少检查：

- 当前正文指纹存在。
- 上一篇正文指纹不存在。
- `<img>` 数量与图片计划一致。
- 每张图片使用 `data:image` 或微信可长期访问的 HTTPS 地址。
- 不含 `localhost`、`127.0.0.1`、`file://` 和本机绝对路径。
- 正文没有重复 H1。

把剪贴板 HTML 保存为文件或通过标准输入交给 `audit_clipboard.py`。网页看起来正确但审计失败时，继续修复，不得宣布完成。
