# 作者配置

作者配置属于使用者，不属于通用 Skill。把 `assets/author-profile.example.json` 复制到项目根目录并命名为 `author-profile.json`。

```json
{
  "author_name": "你的名字",
  "opening": "固定开头，可留空",
  "closing": "固定结尾，可留空",
  "default_length": 2500,
  "default_tone": "清楚、具体",
  "image_preference": "官方真实截图优先",
  "wechat_reply_keyword": ""
}
```

只有用户明确确认过的内容才写入配置。不要从几篇文章推断作者人格、收入、职业和经历。

配置可以控制文章的固定开头与结尾，不能覆盖事实边界。用户当前指令与配置冲突时，以当前指令为准。

不得在配置中保存公众号 Cookie、登录凭证、API key、手机号或身份证件等敏感信息。
