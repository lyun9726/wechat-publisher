---
name: wechat-publisher
description: 为微信公众号完成选题研究、事实核验、中文写作、真实截图与封面、Raphael 带图排版、剪贴板验收和草稿交付。用户要写公众号文章、配图、排版、复制到公众号或保存草稿时使用；普通非公众号写作不要触发。
---

# 公众号全流程制作

把用户给出的选题做成可发布的文章包。按用户实际要求选择交付深度，不强迫只要文字的用户进入排版或发布。

## 先确定交付深度

- 只写文章时，完成材料核验、正文和来源。
- 需要配图时，再制作图片计划、封面和正文图。
- 需要排版或“可直接复制”时，必须完成 Raphael 与剪贴板验收。
- 需要保存草稿时，在公众号后台粘贴并保存；没有明确授权不得正式发布。

完整阶段和停止条件见 [工作流](references/workflow.md)。目标 Agent 缺少浏览器、截图或图片生成工具时，读 [兼容与降级](references/compatibility.md)，交付可继续处理的文件并明确未完成环节。

## 建立文章包

新文章优先运行：

```bash
python3 scripts/init_article.py <slug> --title "文章标题" --output runs
```

如果当前项目已有自己的目录与模板，可以沿用，但仍要保留 `article.md`、`brief.md`、`sources.md`、`image-plan.md`、`delivery-check.md` 和 `images/` 的等价产物。

## 写作边界

动笔前读取 [写作与事实](references/writing.md)。超过 1200 个汉字的现实文章至少需要五件能核验的材料。用户没有提供的亲历、收入、测试结果、客户案例和原话不能补写。产品能力、价格、版本、政策和热点默认重新核验。

作者名、固定开头、结尾、篇幅和视觉偏好来自项目内 `author-profile.json`。没有配置就使用中性表达，不推断作者经历。配置格式见 [作者配置](references/profile.md)。

## 图片边界

需要图片时读取 [图片制作](references/images.md)。产品、模型和教程稿优先使用官方真实截图。AI 生图只用于用户明确需要的概念图、插画或创意封面，不能伪造产品界面、测试过程或官方视觉。

## Raphael 与公众号

需要带图复制时读取 [Raphael 交付](references/raphael.md)，并运行：

```bash
python3 scripts/build_raphael.py runs/<slug>/article.md
python3 scripts/validate_package.py runs/<slug>/article-raphael.md --min-images 1 --raphael
```

点击“复制到公众号”后，必须取得剪贴板 `text/html` 并运行：

```bash
python3 scripts/audit_clipboard.py clipboard.html \
  --fingerprint "当前文章指纹" \
  --expected-images 1
```

只有在当前文章指纹存在、上一篇指纹不存在、图片数量匹配，并且 HTML 不含 `localhost`、`127.0.0.1`、`file://` 或本机绝对路径时，才能宣布带图交付完成。

公众号草稿、发布和账户动作遵守 [发布权限](references/publishing.md)。登录状态、Cookie、API key 和个人资料不得写进 Skill 或提交到仓库。
