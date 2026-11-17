---
name: wechat-publisher
description: 把微信公众号选题做成可发布文章包，覆盖热点筛选、事实核验、中文写作、真实截图、封面、图片内嵌的可复制 HTML、交付审计与草稿保存。用户要求写公众号文章、仿写改稿、配图、做封面、生成带图复制版或保存公众号草稿时使用；普通非公众号写作不要触发。
---

# 微信公众号文章生产

交付一份事实可追溯、图片真实、能直接进入公众号后台的文章包。根据用户要求停在文章、图文包、带图复制版或公众号草稿，不把网页看起来正常当成交付成功。

## 先读取配置

1. 查找当前项目的 `author-profile.json`。若没有，使用 `assets/author-profile.liyun.json` 作为本 Skill 的默认作者配置；为其他作者工作时改用 `assets/author-profile.example.json` 或用户提供的配置。
2. 用户当轮明确要求高于配置。不得从历史文章推断作者经历、收入、职业或亲测结果。
3. 根据任务读取对应参考文件。
   - 选题、热点、产品发布、项目介绍或教程，读取 [研究与选题](references/research.md)。
   - 新写或大改正文，读取 [写作与标题](references/writing.md)。
   - 需要配图或封面，读取 [图片制作](references/images.md)。
   - 需要可直接复制，读取 [带图 HTML](references/copyable-html.md)。
   - 需要保存草稿或发布，读取 [发布权限](references/publishing.md)。
   - 工具不全时，读取 [兼容与降级](references/compatibility.md)。

## 确定交付深度

- “写一篇、改一下、仿写”至少交付 `brief.md`、`sources.md`、`article.md`。
- “配图、封面”增加 `image-plan.md`、真实图片文件和正文图片引用。
- “带图可复制、直接复制、不想逐张插图”必须生成 `带图可复制版.html`，图片全部内嵌并通过审计。Raphael 只在用户明确要求时使用。
- “保存到公众号草稿”需要把已验收富文本粘贴到已登录后台并确认草稿存在。正式发布必须另获明确确认。
- 作者配置含 `default_delivery` 时，用户未指定交付深度可采用该默认值。

## 建立文章包

新文章优先运行：

```bash
python3 scripts/init_article.py <slug> --title "文章标题" --output runs
```

文章目录至少保留：

```text
runs/<slug>/
├── author-profile.json
├── brief.md
├── sources.md
├── article.md
├── image-plan.md
├── delivery-check.md
└── images/
```

需要带图复制时再生成 `带图可复制版.html`。不覆盖用户原图，不把 Cookie、验证码、API key 或公众号凭证写进文章包。

## 不可省略的边界

- 超过 1200 个汉字的现实稿，动笔前至少有五件能核验的具体材料。产品能力、价格、版本、排名、政策和热点必须在写作当日重查。
- 优先使用官方公告、官方文档、论文、项目仓库和真实操作结果。二手文章可以提供线索，不能独自支撑关键结论。
- 用户没提供的亲历、收入、测试、客户案例、耗时和原话不能补写。官方演示必须标明为官方演示，不能改写成作者亲测。
- 产品、模型、教程稿优先使用用户截图或官方真实截图。AI 生图不得冒充产品界面、测试结果或官方视觉。
- 默认封面为 900×383，放在正文最后一张，方便公众号“从正文选择”后删除。正文开头不重复放封面，除非用户另有要求。
- 默认封面要有手机缩略图仍能读出的标题。简单裁一张横向截图不能代替封面设计，除非用户明确要无字封面。
- 公众号标题栏已有标题，复制正文时不包含 H1 和摘要。
- 没有完成可观察验收，就明确停在哪一步，不能声称“图片已经正常显示”或“草稿已保存”。

## 带图交付

图片与正文齐备后运行：

```bash
python3 scripts/check_style.py runs/<slug>/article.md
python3 scripts/validate_package.py runs/<slug>/article.md --min-images 1 --cover-position end
python3 scripts/build_copyable.py runs/<slug>/article.md
python3 scripts/audit_clipboard.py runs/<slug>/带图可复制版.html \
  --fingerprint "当前文章指纹" \
  --expected-images <图片总数> \
  --cover-position end
```

最终 HTML 必须同时满足：

- `text/html` 含当前文章指纹，不含上一篇文章指纹。
- 图片数量与计划一致，所有本地图片都已变成 `data:image`。
- 不含 `localhost`、`127.0.0.1`、`file://`、本机绝对路径或裂图。
- 封面是最后一张图片，正文没有 H1 和公众号摘要。
- 浏览器打开后，“复制带图全文”复制的是正文富文本，不把页面按钮和外壳复制进去。

将检查结果写进 `delivery-check.md`。完整阶段与停止条件见 [工作流](references/workflow.md)。
