# AstrBot 专供人格包

这套目录不是给 AstrBot `skills` 用的，而是给 AstrBot 原生 `Persona` 直接引用的。

目标很明确：

- 不再把 `maotou` 当 skill 拼进通用提示词
- 直接利用 AstrBot 的 `system_prompt + begin_dialogs + custom_error_message + tools + skills`
- 尽量绕开 AstrBot 宿主会把人格稀释掉的几个坑

## 这次为什么要重写

读完 AstrBot 源码后，问题比“prompt 太短”更具体：

1. Persona 的 `system_prompt` 会被追加进 `# Persona Instructions` 段落
2. Persona 的 `begin_dialogs` 会被作为历史消息直接插到上下文最前面
3. 如果 persona 的 `skills` 是 `None`，AstrBot 会继续把全局 skills prompt 拼进来
4. 如果 persona 的 `tools` 是 `None`，AstrBot 会继续把全量工具提示拼进来
5. `POST /api/persona/create` 时，后端会把空数组 `[]` 折叠成 `None`

第五条是最坑的。

也就是说，你在创建人格时就算传：

- `"skills": []`
- `"tools": []`

后端也会把它们吃成 `None`，运行时反而变成“启用全部 skills / tools”。

所以这个目录里给了两种东西：

- 人能直接看的人格本体
- 给 AstrBot API 直接吃的 payload，并且用宿主兼容绕法封掉全局干扰

## 文件说明

- `system-prompt.md`
  猫头的人格主提示词。不是 skill 规则，而是 AstrBot persona 专用宿主 prompt。
- `begin-dialogs.json`
  直接对应 AstrBot Persona 的 `begin_dialogs` 字段。偶数条，按 user / assistant 轮流。
- `corpus-anchors.md`
  语料锚点说明。告诉你当前这些示例分别借了哪些原话和梗图壳子。
- `custom-error-message.txt`
  可选。让 AstrBot 请求失败时仍然用猫头口气回。
- `persona.chat-only.create.json`
  纯人格版。创建时直接屏蔽 skills 和 tools，最不容易被宿主稀释。
- `persona.assistive.create.json`
  留工具版。创建时屏蔽 skills，但保留 tools，适合你还想让它继续做事。
- `persona.chat-only.update.json`
  可选。创建后如果你想把占位的 fake tool / skill 清掉，再走一次 update。
- `persona.assistive.update.json`
  可选。和上面一样，但保留 tools。

## 两个版本怎么选

### 1. `chat-only`

适合：

- 你就是要最纯的猫头味
- 主要拿来群聊、锐评、接梗、推荐
- 不希望工具调用和技能提示词再把它拉回普通助手

特点：

- 屏蔽全局 skills
- 屏蔽全局 tools
- 最稳定，最像“纯人格接口”

### 2. `assistive`

适合：

- 还想保留 AstrBot 的工具能力
- 但不想再吃通用 skill prompt 的味道污染

特点：

- 屏蔽全局 skills
- 保留 tools
- 味道会比 `chat-only` 稍微淡一点，但实用性更强

## 为什么 payload 里会有假的 tool / skill 名字

因为 AstrBot 的 `create_persona` 路由会把空数组折成 `None`。

所以创建时不能直接传空数组，只能传“永远匹配不到真实工具/技能”的占位名字，让运行时过滤结果变成空集合。

这不是玄学，是为了绕开 AstrBot 当前后端的创建语义。

## 推荐用法

如果你要“开箱即用”：

1. 选一个 `persona.*.create.json`
2. 走 AstrBot 的 `/api/persona/create`
3. 直接创建一个 persona

如果你介意 create payload 里那两个占位名字出现在管理界面：

1. 先用 `persona.*.create.json` 创建
2. 再用同名的 `persona.*.update.json` 走一次 `/api/persona/update`
3. update 路由会保留空数组，不会再被折回 `None`

如果你只想手动复制：

1. 把 `system-prompt.md` 贴到 Persona 的系统提示词
2. 把 `begin-dialogs.json` 里的内容填进 Persona 预设对话
3. 然后自己决定要不要保留 tools
4. 不要再额外挂这个 `maotou` skill

## 宿主层设计原则

这版专门按 AstrBot 的实际拼接行为来写，所以有几个硬原则：

- `system_prompt` 负责定骨架，不写成花里胡哨的 skill 说明书
- `begin_dialogs` 负责钉住味道、节奏、收刀方式和典型壳子
- 当前 few-shot 故意更偏群聊、二游、沪国、婚礼、身份认领，而不是技术工作流
- serious 场景直接内建到人格里，不靠外层再补“安全模式”
- 具体示例尽量往语料原句靠，见 [corpus-anchors.md](corpus-anchors.md)

核心原则还是一句：

`猫头放 Persona 层，不放 skill 杂烩层。`
