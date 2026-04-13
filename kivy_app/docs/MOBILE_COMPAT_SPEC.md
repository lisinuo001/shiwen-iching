# Kivy 移动端适配规范 MOBILE_COMPAT_SPEC

> 版本: v1.0  
> 创建日期: 2026-04-13  
> 来源: 天机 TianJi 项目 v10.0~v10.6 共 7 轮移动端适配失败的完整复盘  
> 适用范围: 所有 Kivy + Buildozer 的 Android 项目  
> 状态: 🟢 ACTIVE

---

## 〇、核心结论

> **PC 上运行正常 ≠ 手机上正常。**  
> Kivy 在 PC 和 Android 上的布局时序、坐标系、事件传播机制存在本质差异。  
> 以下所有规则均来自真实失败案例，每条都对应一次废包。

---

## 一、Widget 架构规范

### 1.1 自定义交互组件必须继承 Widget

```python
# ✅ 正确
class MyButton(Widget):
    pass

# ❌ 错误 — 导致坐标偏移 + touch 拦截
class MyButton(BoxLayout):
    pass
```

**失败案例**: v10.1~v10.4，HoldButton 和 TapButton 继承 BoxLayout，导致：
- `canvas.before` 绘制的边框位置与 widget 实际位置不一致
- 子 Label 拦截 touch 事件，按钮无响应
- 尝试 `label.on_touch_down = lambda t: False` 无效

**根因**: BoxLayout 在 Android 上的布局计算和 canvas 绑定的执行时序不一致。PC 上是同步的，Android 上是异步的。

---

### 1.2 文字显示必须用原生 Label + 手动定位

```python
# ✅ 正确 — 文字永远跟着 widget 走
class MyButton(Widget):
    def __init__(self):
        super().__init__()
        self._label = Label(text="按钮", font_name=CN, font_size=sp(16),
            halign='center', valign='middle')
        self._label.bind(size=lambda w, s: setattr(w, 'text_size', s))
        self.add_widget(self._label)
        self.bind(pos=self._layout, size=self._layout)

    def _layout(self, *_):
        # 子 label 的 pos/size 必须手动同步
        self._label.pos = self.pos
        self._label.size = self.size
        # canvas 绘制也放在这里，确保同一帧更新
        self._draw_border()

# ❌ 错误 — Android 上坐标全部归零
def _draw(self):
    cl = CoreLabel(text="按钮", font_size=sp(16))
    cl.refresh()
    with self.canvas:
        Rectangle(pos=(self.x + 10, self.y + 10), texture=cl.texture)
```

**失败案例**: v10.0~v10.3，所有按钮文字用 CoreLabel + canvas 绘制，在手机上全部堆叠到左下角 (0, 0) 附近。

**根因**: CoreLabel 是离屏渲染纹理，贴到 canvas 时使用的 `self.x, self.y` 在 Android 上第一帧可能还是 (0, 0)，即使 bind 了 pos/size，canvas 刷新和布局更新不在同一帧。

---

### 1.3 _layout() 方法是核心

每个自定义 Widget **必须**有一个 `_layout()` 方法，绑定到 `pos` 和 `size`：

```python
self.bind(pos=self._layout, size=self._layout)
Clock.schedule_once(lambda dt: self._layout(), 0)  # 首帧也要调一次
```

`_layout()` 中**同时**做三件事：
1. 更新所有子 Label 的 `pos` 和 `size`
2. 清除并重绘 `canvas.before`（背景/边框）
3. 清除并重绘 `canvas.after`（前景装饰）

**不要**把 canvas 绘制和 label 定位分到不同的方法或不同的 bind 回调中。

---

## 二、坐标系规范

### 2.1 PC vs Android 坐标行为对照表

| 绘制方式 | PC | Android | 结论 |
|---------|-----|---------|------|
| `Widget.canvas.before` + `self.x, self.y`（bind 后） | ✅ | ✅ | 可用 |
| `BoxLayout.canvas.before` + `self.x, self.y` | ✅ | ❌ 偏移 | **禁用** |
| `CoreLabel` → `Rectangle(texture=...)` | ✅ | ❌ 归零 | **仅装饰** |
| `add_widget(Label)` + `bind(pos, size)` | ✅ | ✅ | **推荐** |
| `BoxLayout` 子 widget 自动布局 | ✅ | ⚠️ 时序不可控 | 仅用于顶层容器 |

### 2.2 安全使用 canvas 的条件

canvas 绘制在 Android 上正确的前提是：
1. widget 继承 `Widget`（不是 BoxLayout）
2. 绑定了 `self.bind(pos=callback, size=callback)`
3. 在 callback 中使用实时的 `self.x, self.y, self.width, self.height`
4. canvas 绘制和子 widget 定位在**同一个 callback** 中完成

### 2.3 CoreLabel 的安全使用范围

CoreLabel 只能用于：
- **面积小于 dp(60) 的装饰性文字**（如爻线旁的"阳/阴"标注）
- **不需要精确对齐的 HUD 标注**
- **canvas 背景上的半透明水印文字**

CoreLabel **不能用于**：
- 按钮文字
- 标题
- 任何需要用户阅读的主内容
- 任何需要与 widget 边界精确对齐的文字

---

## 三、Touch 事件规范

### 3.1 事件传播机制差异

| 基类 | `on_touch_down` 行为 | 结论 |
|------|---------------------|------|
| `Widget` | 直接收到，由自己决定是否消费 | ✅ 可控 |
| `BoxLayout` | 先遍历子 widget，子 widget 可能拦截 | ❌ 不可控 |

### 3.2 正确的 touch 处理模板

```python
class MyButton(Widget):
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False  # 不在范围内，不处理
        # 处理按下逻辑
        self._pressed = True
        self._redraw()
        return True  # 消费事件

    def on_touch_up(self, touch):
        if not self._pressed:
            return False
        self._pressed = False
        self._redraw()
        if self.collide_point(*touch.pos):
            self._on_press()  # 触发回调
        return True
```

### 3.3 长按 (Hold) 处理模板

```python
class HoldButton(Widget):
    HOLD_TIME = 1.5

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        self._holding = True
        self._progress = 0
        self._ev = Clock.schedule_interval(self._tick, 0.025)
        return True

    def on_touch_up(self, touch):
        if not self._holding:
            return False
        self._holding = False
        if self._ev:
            self._ev.cancel()
        if self._progress < 1.0:
            self._progress = 0  # 未完成，重置
        self._update()
        return True

    def _tick(self, dt):
        self._progress += dt / self.HOLD_TIME
        if self._progress >= 1.0:
            self._progress = 1.0
            self._holding = False
            self._ev.cancel()
            self._on_complete()  # 触发完成回调
        self._update()
```

### 3.4 禁止的做法

```python
# ❌ 不要这样试图阻止子 widget 拦截 touch
label.on_touch_down = lambda t: False

# ❌ 不要在 BoxLayout 子类中覆盖 on_touch_down 
# 因为 super().on_touch_down(touch) 会遍历子 widget
class MyButton(BoxLayout):
    def on_touch_down(self, touch):
        ...  # 不可靠
```

---

## 四、布局规范

### 4.1 垂直空间分配规则

| 元素类型 | size_hint_y | 高度设置 | 说明 |
|---------|-------------|---------|------|
| 固定高度元素（按钮、标题栏） | `None` | `height = dp(xx)` | 高度确定 |
| 填充元素（内容区、卡槽列表） | `1`（或其他比例） | 不设 height | 自动分配剩余空间 |
| 间距 | `None` | `height = dp(xx)` | 用 `Widget(size_hint_y=None, height=dp(10))` |

### 4.2 不要用不可见的 Widget 占位

```python
# ❌ 错误 — HUD 装饰 Widget 占了 size_hint_y=1，把内容挤到底部
self._hud = Widget()  # 默认 size_hint_y=1
container.add_widget(self._hud)  # 吃掉全部剩余空间

# ✅ 正确 — 装饰画在背景上，不占布局空间
# 用 root.canvas.before 或 root.canvas.after 画装饰
```

**失败案例**: v10.4~v10.5，添加了 HUD 装饰 Widget（同心圆+十字准星），它用默认 `size_hint_y=1` 吃掉了屏幕上半部分全部空间，6 个爻位被挤到底部 40% 区域。

### 4.3 BoxLayout 仅用于顶层容器

```python
# ✅ BoxLayout 用于页面级布局
root = BoxLayout(orientation='vertical', spacing=dp(8),
                 padding=[dp(16), dp(16), dp(16), dp(16)])

# ✅ BoxLayout 用于简单横向排列（非交互）
header = BoxLayout(size_hint_y=None, height=dp(36))

# ❌ BoxLayout 不用于自定义交互组件
class MyButton(BoxLayout):  # 禁止
```

### 4.4 dp/sp 使用规则

| 用途 | 单位 | 示例 |
|------|------|------|
| 尺寸、间距、边距 | `dp()` | `height=dp(44)`, `padding=dp(16)` |
| 字体大小 | `sp()` | `font_size=sp(16)` |
| canvas 线宽 | `dp()` | `Line(width=dp(1.5))` |
| 最小点击区域 | `dp(44)` | 按钮高度 >= dp(44) |

**永远不要用裸数字**：`height=72` ← 这在高 DPI 设备上只有几毫米。

---

## 五、字体规范

### 5.1 字体加载

```python
# 必须在启动时注册中文字体
LabelBase.register(name="NotoSansCJK", fn_regular="NotoSansCJK.otf")
CN = "NotoSansCJK"

# 所有 Label 必须指定 font_name=CN
Label(text="天机", font_name=CN, font_size=sp(20))
```

### 5.2 字体文件要求

- 格式: `.otf` 或 `.ttf`
- 必须包含: CJK 统一汉字区（U+4E00-U+9FFF）
- 打包: 加入 `buildozer.spec` 的 `source.include_patterns`
- 大小: 尽量选子集字体（<10MB），完整 NotoSansCJK 约 16MB

---

## 六、ScrollView 规范

### 6.1 基本结构

```python
sv = ScrollView(do_scroll_x=False)
inner = BoxLayout(orientation='vertical', size_hint_y=None,
                  spacing=dp(8), padding=[0, dp(4), 0, dp(4)])
inner.bind(minimum_height=inner.setter('height'))
# 添加内容到 inner
sv.add_widget(inner)
```

### 6.2 内部 Label 自适应高度

```python
lbl = Label(text="长文本...", markup=True, font_name=CN,
    font_size=sp(15), size_hint_y=None, halign='left', valign='top')
lbl.bind(size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
lbl.bind(texture_size=lbl.setter('size'))  # 高度跟随内容
```

---

## 七、调试技巧

### 7.1 PC 模拟手机分辨率

```python
if __name__ == "__main__":
    Window.size = (390, 844)  # iPhone 14 比例
    # 注意：这行只在 __main__ 块中，不影响 Android
```

### 7.2 远程调试 Android 日志

```bash
# 手机连 USB，开启开发者模式
adb logcat -s python:* kivy:*
```

### 7.3 常见 Android 崩溃排查

| 现象 | 可能原因 |
|------|---------|
| 启动闪退 | 字体文件未打包、import 失败 |
| 白屏 | 首帧 layout 异常、canvas 绘制崩溃 |
| 文字乱码 | 未注册中文字体 |
| 文字在左下角 | 使用了 CoreLabel canvas 绘制 |
| 按钮无反应 | 继承了 BoxLayout，touch 被子 widget 拦截 |
| 边框位置错误 | canvas.before 坐标与 widget pos 不同步 |
| 上半部分空白 | 不可见 Widget 占了 size_hint_y=1 |

---

## 八、检查清单 (每次改 UI 后必查)

- [ ] 所有自定义交互 Widget 继承 `Widget`（不是 BoxLayout）
- [ ] 所有文字用 `add_widget(Label)` + `bind(pos, size)` + `_layout()`
- [ ] `CoreLabel` 仅用于装饰性小文字
- [ ] 每个 Widget 的 `_layout()` 同时更新子 Label 和 canvas
- [ ] 无不可见的 Widget 占用 `size_hint_y=1` 空间
- [ ] 所有尺寸用 `dp()`，字体用 `sp()`，无裸数字
- [ ] 按钮最小高度 >= `dp(44)`
- [ ] `on_touch_down` 使用 `collide_point` 检查范围
- [ ] `BoxLayout` 仅用于页面级容器，不用于交互组件
- [ ] PC 测试通过后，**不要假设手机也正常**

---

> ⚠️ 本文档是 7 轮失败的结晶。下次开新 Kivy 项目时，先读这份文档再动手。  
> ⚠️ 遇到新的适配问题，务必追加到对应章节。
