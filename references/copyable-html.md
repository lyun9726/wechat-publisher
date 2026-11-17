# 带图可复制 HTML

## 默认方案

默认不依赖 Raphael。正文和图片完成后运行：

```bash
python3 scripts/build_copyable.py runs/<slug>/article.md
```

脚本会：

- 从页面标题区读取 H1，但从可复制正文中移除 H1。
- 移除开头的公众号摘要引用块，摘要仍保留在 `article.md` 供后台填写。
- 把 Markdown 中的本地 PNG、JPG、WEBP 和 GIF 转成 `data:image`。
- 生成带“复制带图全文”按钮的独立 HTML。
- 只复制 `<article>` 内的富文本，不复制按钮、页面标题和外壳。

图片必须先存在于文章目录中。远程图片默认报错并要求本地化，避免图床防盗链、过期或公众号手机端无法读取。

## 硬验收

运行：

```bash
python3 scripts/audit_clipboard.py runs/<slug>/带图可复制版.html \
  --fingerprint "当前文章指纹" \
  --previous-fingerprint "上一篇文章指纹" \
  --expected-images 5 \
  --cover-position end
```

随后用浏览器打开 HTML，至少检查：

- 桌面预览和窄屏预览无裂图，文字未溢出。
- 顶部明确显示图片已内嵌。
- 点击复制按钮后可粘贴出正文和全部图片。
- 最后一张图为封面，封面不在文章开头重复出现。

剪贴板工具可读取 `text/html` 时，再把实际剪贴板内容保存为文件做一次审计。工具无法读取剪贴板时，只能声称“独立 HTML 已通过静态审计”，不能声称公众号后台与手机真机已经通过。

## Raphael 可选路径

只有用户明确要求 Raphael 样式或现有工作流依赖它时，才读取 [Raphael 交付](raphael.md)。Raphael 预览正常仍要检查最终剪贴板 HTML，不能把本地图片地址交给公众号。
