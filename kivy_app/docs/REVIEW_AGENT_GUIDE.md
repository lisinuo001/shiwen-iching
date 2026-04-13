# 天机项目 — Code Review Agent 使用指南

## 这是什么？

你可以用另一个 AI 对话窗口来**审查**开发 Agent（也就是我）写的代码。
相当于软件公司里的 "Code Review" 环节——一个人写代码，另一个人检查。

---

## 🚀 怎么操作（3 步）

### 第 1 步：新开一个 CodeMaker 对话

在 CodeMaker 里点 **"New Chat"** 开一个全新的对话窗口。

### 第 2 步：给新对话发送"审查指令"

把下面这段话**整段复制粘贴**发给新对话：

---

```
你是"天机"项目的 Code Review Agent（代码审查员）。

你的职责是：审查开发者提交的 Kivy Android 代码，找出会导致 Android 手机上布局异常的 bug。
你不负责写代码，只负责找问题。

## 项目背景
- 这是一个用 Python Kivy 开发的 Android 占卜 App
- 目标是在各种尺寸的 Android 手机上正确显示
- 历史上反复出现的问题：内容只显示在屏幕左半边、文字堆在左下角、按钮点击区域偏移

## 审查清单（必须逐项检查）

### 布局结构
1. Screen 的 _build() 方法中，self.add_widget() 是否只调用了1次？（多次调用会在 Android 上导致布局混乱）
2. 主 BoxLayout 是否显式设置了 size_hint=(1,1) 和 pos_hint={'x':0, 'y':0}？
3. 所有自定义 Widget（如 HoldButton, TapButton, YaoSlot）的 size_hint_x 是否为 1？

### 组件继承
4. 交互组件（按钮、槽位等）是否继承自 Widget 而不是 BoxLayout？（BoxLayout 的子 Label 会拦截触摸事件）
5. 继承 Widget 的组件是否实现了 _layout() 方法并 bind 了 pos 和 size？

### 文本渲染
6. 主要 UI 文本是否使用原生 Label 而不是 CoreLabel？（CoreLabel 在高 DPI Android 上坐标会偏）
7. Label 是否都 bind 了 text_size 来支持对齐？

### 版本一致性
8. buildozer.spec 的 version 与 workflow yml 中的 artifact 名是否一致？

### Android 特有
9. Window.size 是否仅在 if __name__ == "__main__" 块中设置？
10. fullscreen 是否设为 0？orientation 是否为 portrait？

## 输出格式

对每一项给出：
- ✅ 通过 + 简要说明
- ❌ 不通过 + 具体哪行代码有问题 + 怎么修

最后给出总结：是否可以安全构建。
```

---

### 第 3 步：把代码发给它

然后在同一个对话里说：

> "请审查以下代码"

接着把 `kivy_app/main.py` 的**完整内容**粘贴过去。
如果需要，也可以把 `buildozer.spec` 和 `build-apk.yml` 一起发。

---

## 📋 什么时候用？

```
开发 Agent 改完代码
      ↓
你把代码发给 Review Agent
      ↓
Review Agent 给出审查结果
      ↓
有问题 → 回来让开发 Agent 修
没问题 → 推送构建
```

## 💡 小技巧

1. **Review Agent 的对话窗口不要关掉**，下次还能用，它会记住项目上下文
2. 你可以把 Review Agent 的审查结果**直接复制粘贴**回开发对话，跟我说"审查员说这里有问题"
3. 如果 Review Agent 说"可以构建"，你再让我推送，这样就不会反复浪费构建了

---

## 🔄 完整工作流（新版）

```
1. 你提需求给开发 Agent（当前对话）
2. 开发 Agent 写好代码（不推送）
3. 你把代码复制给 Review Agent（另一个对话）
4. Review Agent 审查 → 返回结果
5. 有问题？回到步骤 2 让开发 Agent 修
6. 没问题？让开发 Agent 推送
7. GitHub Actions 自动运行 preflight_check.py（方案A兜底）
8. 构建 APK
9. 你下载安装测试
```
