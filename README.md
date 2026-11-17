# WeChat Publisher Skill

一套可移植的微信公众号生产 Skill。它把选题、事实核验、中文写作、真实截图、封面、图片内嵌 HTML、交付审计和公众号草稿串成一条可检查的流程。

本仓库默认带有“利云”作者配置，也支持替换成其他作者。账号凭证、Cookie 和验证码不会写进 Skill。

## 能做什么

- 从近 12 到 24 小时热点中筛选适合公众号的候选选题
- 核验产品发布、GitHub 项目、模型能力、价格、榜单和政策
- 生成写作卡、来源记录、公众号摘要和正文
- 优先使用官方真实截图，制作 900×383 封面
- 把封面放在正文最后，便于公众号从正文选择后删除
- 生成图片全部内嵌的 `带图可复制版.html`
- 拦截旧稿指纹、本机路径、临时服务地址和图片数量错误
- 在用户明确授权后保存公众号草稿；默认不正式发布

## 安装

### Codex

```bash
git clone https://github.com/lyun9726/wechat-publisher.git ~/.codex/skills/wechat-publisher
```

新建一个任务，让 Codex 重新扫描 Skills。已有旧版本时进入目录运行 `git pull`。

### 其他 Agent

把整个仓库放入该 Agent 的 Skills 目录，确保入口仍为根目录的 `SKILL.md`。目标 Agent 至少需要读写文件和访问网络；拥有浏览器和截图工具时可以完成真实配图与公众号草稿。

## 直接测试

对 Agent 说：

> 使用 $wechat-publisher 写一篇微信公众号文章，主题是“……”。按利云的作者配置完成事实核验、正文、官方真实截图、文末封面和带图可复制 HTML。不要进入 Raphael，不要发布。

如果只想测试写作：

> 使用 $wechat-publisher 写一篇微信公众号文章，主题是“……”。本轮只交付文章稿和来源，不做图片。

## 文章包

```bash
python3 scripts/init_article.py qwen4-max --title "文章标题" --output runs
```

生成的目录包含 `brief.md`、`sources.md`、`article.md`、`image-plan.md`、`delivery-check.md` 和 `images/`。

图片完成后运行：

```bash
python3 scripts/check_style.py runs/qwen4-max/article.md

python3 scripts/validate_package.py runs/qwen4-max/article.md \
  --min-images 1 --cover-position end

python3 scripts/build_copyable.py runs/qwen4-max/article.md

python3 scripts/audit_clipboard.py runs/qwen4-max/带图可复制版.html \
  --fingerprint "当前文章指纹" \
  --expected-images 5 \
  --cover-position end
```

打开 `带图可复制版.html`，点击“复制带图全文”，再粘贴到公众号后台。独立 HTML 已通过审计，不等于公众号手机真机预览已经通过；发布前仍应在公众号后台检查一次。

没有现成封面工具时，可以用官方截图生成带标题封面：

```bash
python3 scripts/build_cover.py images/source.png \
  --headline "封面主标题" \
  --eyebrow "产品或栏目" \
  --subtitle "一句补充信息" \
  --output images/00-cover.png
```

## 作者配置

- `assets/author-profile.liyun.json` 是默认配置。
- `assets/author-profile.example.json` 是空白示例。
- 项目根目录存在 `author-profile.json` 时优先使用项目配置。

为其他作者工作时，把示例复制到项目根目录并修改：

```bash
cp assets/author-profile.example.json author-profile.json
```

配置只保存公开写作偏好，不要加入登录凭证、手机号、Cookie 或 API key。

## 文件结构

```text
SKILL.md
agents/openai.yaml
assets/
references/
scripts/
```

`Raphael` 仍作为可选流程保留。当前默认交付是独立的带图 HTML，不要求用户逐张插图。

## 验证

```bash
python3 -m py_compile scripts/*.py
python3 scripts/validate_package.py <article.md> --cover-position end
```

Skill 的 YAML 与目录规范可使用 Codex Skill Creator 的 `quick_validate.py` 检查。
