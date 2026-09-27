# WeChat Publisher Skill

一套面向微信公众号的 Agent Skill，把选题、事实核验、中文写作、真实截图、封面、Raphael 排版、剪贴板验收和公众号草稿交付串成一条可复用流程。

它解决的不是“让 AI 写一篇文章”，而是让兼容 Agent 按可检查的步骤交付一份真正能进入公众号后台的文章包。

## 能做什么

- 根据选题研究资料并核验时效性事实
- 按作者配置写公众号正文，避免编造亲历、测试和数据
- 优先使用官方页面或真实操作截图，避免伪造产品界面
- 生成封面、正文配图计划和图片位置说明
- 生成适合 Raphael 导入的 Markdown
- 检查复制后的富文本 HTML，拦截 `localhost`、本机路径和失效图片
- 在用户明确授权后保存公众号草稿；默认不直接发布

## 安装

### Codex

将仓库克隆到 Codex Skills 目录：

```bash
git clone https://github.com/lyun9726/wechat-publisher.git ~/.codex/skills/wechat-publisher
```

然后新建一个 Codex 任务，让 Agent 重新扫描 Skills。

### 其他兼容 Agent

将整个仓库复制到该 Agent 的 Skills 目录，并确保入口文件仍是仓库根目录下的 `SKILL.md`。不同 Agent 的浏览器、截图和剪贴板能力不同，具体降级规则见 [`references/compatibility.md`](references/compatibility.md)。

## 快速开始

直接对 Agent 说：

> 用 wechat-publisher 写一篇微信公众号文章，主题是“……”。需要真实截图、封面、Raphael 带图导入版，并在复制后检查图片是否能正常显示。先保存草稿，不要发布。

创建文章包：

```bash
python3 scripts/init_article.py my-article --title "文章标题" --output runs
```

生成 Raphael 导入版并检查：

```bash
python3 scripts/build_raphael.py runs/my-article/article.md
python3 scripts/validate_package.py runs/my-article/article-raphael.md --min-images 1 --raphael
```

从 Raphael 点击“复制到公众号”后，把剪贴板中的 `text/html` 保存为 `clipboard.html`，再运行：

```bash
python3 scripts/audit_clipboard.py clipboard.html \
  --fingerprint "当前文章指纹" \
  --expected-images 1
```

## 作者配置

复制示例配置：

```bash
cp assets/author-profile.example.json author-profile.json
```

再填写作者名、固定开头、结尾、篇幅和视觉偏好。`author-profile.json` 属于个人配置，不建议提交到公开仓库。

## 文件结构

```text
SKILL.md                       Skill 入口与总规则
agents/openai.yaml             Agent 展示信息
assets/                        文章包模板和作者配置示例
references/                    写作、图片、排版、发布和兼容规范
scripts/                       初始化、转换与验收脚本
```

## 工具依赖与边界

Skill 本身不包含账号凭证，也不会绕过登录、验证码或平台权限。目标 Agent 拥有浏览器控制、截图、图片处理和 HTML 剪贴板读取能力时，可以执行完整流程；缺少相关能力时会停在可验证的中间产物，不会宣称图片已经成功进入公众号。

产品功能、价格、版本、政策和热点等时效信息应在每次写作时重新核验。AI 生图不能冒充官方截图、真实测试或产品界面。

## 本地验证

```bash
python3 scripts/validate_package.py SKILL.md
python3 -m py_compile scripts/*.py
```

## 安全与隐私

- 不提交 Cookie、验证码、API key、邮箱密码或公众号凭证
- 截图前裁掉个人信息、会话信息和敏感文件名
- 发邮件、付款、公开发布和删除数据等动作必须由用户明确确认
- 默认只保存公众号草稿，不自动正式发布
