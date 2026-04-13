# 出包规范 BUILD_SPEC

> 版本: v2.0 (重大更新，总结 v10.0~v10.5 全部打包教训)  
> 更新日期: 2026-04-13  
> 适用项目: 天机 TianJi (Kivy Android APK)  
> 状态: 🟢 ACTIVE

---

## 〇、核心原则 (每次出包前必读)

> **三条铁律，违反任何一条都会导致废包：**

1. **必须清缓存** — workflow 中必须有 `rm -rf .buildozer bin`，否则 Buildozer 会复用旧编译产物
2. **必须验版本** — 下载 APK 后先看文件名中的版本号，和 `buildozer.spec` 对不上就是废包
3. **必须用 Widget 基类** — 自定义交互组件继承 `Widget`，不继承 `BoxLayout`；文字用 `add_widget(Label)` + `bind(pos/size)` 手动定位

---

## 一、出包方式

采用 **GitHub Actions 云端自动构建**，无需本地 Linux 环境。

| 项目 | 值 |
|------|------|
| 仓库地址 | `https://github.com/lisinuo001/shiwen-iching` |
| 触发条件 | push 到 `main`/`master` 分支，或手动 `workflow_dispatch` |
| 构建环境 | `ubuntu-22.04` |
| 超时时间 | 60 分钟 |
| 产物位置 | Actions → 对应 run → Artifacts → `TianJi-APK-vXX` |
| 产物保留 | 30 天 |
| 首次全量编译 | 约 25-35 分钟 |

---

## 二、出包前检查清单 (Pre-Build Checklist)

每次出包前 **必须** 逐条确认，不可跳过：

### 2.1 代码规范（移动端兼容性）

> ⚠️ PC 上运行正常 ≠ 手机上正常。以下规则全部来自真实失败案例。

- [ ] `main.py` 用 `py -3.11 main.py` 运行正常，无崩溃
- [ ] **所有可交互 widget（按钮、卡槽等）继承 `Widget`，不继承 `BoxLayout`**
  - 原因：`BoxLayout` 的 canvas 坐标与子 widget 实际位置在 Android 上不同步
- [ ] **widget 文字用 `add_widget(Label)` + `bind(pos, size)` + `_layout()` 手动定位**
  - 原因：`BoxLayout` 自动布局在不同 DPI 设备上时序不可控
- [ ] **`CoreLabel` 仅用于 canvas 装饰性小文字**（HUD 标注、爻线旁小字等）
  - 原因：`CoreLabel` 在 Android 上绝对坐标全部偏到左下角 (0,0)
- [ ] **每个自定义 Widget 的 `_layout()` 方法同时更新：子 Label 的 pos/size + canvas 绘制**
- [ ] 没有使用 Python 3.11+ 专属语法（构建环境为 Python 3.10）
- [ ] 未引入新的外部依赖包（若有，需同步更新 `buildozer.spec` 的 `requirements`）

### 2.2 资源检查

- [ ] `NotoSansCJK.otf` 存在于 `kivy_app/`
- [ ] `icon.png` 存在于 `kivy_app/`（512x512 RGB PNG）
- [ ] `iching_data.py` 和 `yaoci_data.py` 存在于 `iching/` 根目录
- [ ] 未依赖任何外部 PNG 贴图做核心渲染

### 2.3 配置检查

- [ ] `buildozer.spec` 中 `version` 已更新为新版本号
- [ ] `title` 和 `package.name` 正确（当前：天机 / tianji）
- [ ] `source.include_patterns` 包含所有必需文件
- [ ] `requirements = python3,kivy,pillow`（不锁定 kivy 版本）
- [ ] `android.accept_sdk_license = True`

### 2.4 Workflow 检查

- [ ] `build-apk.yml` 中 **有 `rm -rf .buildozer bin` 清缓存步骤**
- [ ] `JAVA_HOME` 设为 JDK 17
- [ ] 命令是 `buildozer -v android debug`（无管道，无 `yes |`，无 `tail`）
- [ ] artifact name 与版本号匹配
- [ ] `if-no-files-found: error` 已设置

---

## 三、出包操作流程

### 第1步：更新版本号

```
文件: kivy_app/buildozer.spec → version = X.Y.Z
文件: .github/workflows/build-apk.yml → artifact name 匹配
```

版本号规则：
- **X** (主版本): 大改交互逻辑或新增核心功能
- **Y** (次版本): UI 优化、布局调整
- **Z** (补丁): Bug 修复

### 第2步：本地验证

```bash
cd d:\snow\iching\kivy_app
py -3.11 main.py
```

验证项：首页显示 → 长按生成 → 六爻揭示 → 结果页 → 返回重置

### 第3步：提交推送

```bash
cd d:\snow\iching
git add .
git commit -m "vX.Y.Z: 变更描述"
git push origin main
```

### 第4步：监控构建

1. 打开 https://github.com/lisinuo001/shiwen-iching/actions
2. 等待 ✅ 绿色（全量编译约 25-35 分钟）
3. 如失败 ❌：
   - 先看最底部错误摘要
   - 再搜 `FAILURE`、`Error`、`gradle failed` 关键词
   - 对照第五节踩坑记录排查

### 第5步：下载并验证 APK

1. 点击成功的 workflow run → Artifacts → 下载 ZIP
2. 解压后 **检查 APK 文件名中的版本号**
3. ⚠️ **如果文件名版本号与 spec 不一致，此包作废，检查清缓存步骤是否执行**

### 第6步：安装测试

1. 传输到手机/模拟器
2. 安装（需开启"未知来源"权限）
3. 按第六节测试清单逐条验证

---

## 四、环境依赖参数 (固化)

以下参数经过多轮调试验证可用，**不要随意修改**：

| 参数 | 值 | 修改风险 |
|------|------|---------|
| GitHub Runner | `ubuntu-22.04` | 🔴 切换版本可能缺依赖 |
| Python | `3.10` | 🔴 3.11+ 与 p4a 不兼容 |
| JDK | `openjdk-17` | 🔴 API 33 强制要求 |
| Cython | `0.29.36` | 🟡 更高版本可能不兼容 |
| JAVA_HOME | `/usr/lib/jvm/java-17-openjdk-amd64` | 🔴 必须显式设置 |
| Android API | `33` | 🟡 可升但需同步测试 |
| Min API | `21` | 🟢 Android 5.0 覆盖够广 |
| NDK | `25b` | 🔴 与 p4a 绑定 |
| 架构 | `arm64-v8a` | 🟢 主流设备 |

---

## 五、踩坑全记录 (按严重程度排序)

### 🔴 P0 级（导致安装的是错误版本）

#### 5.1 Buildozer 缓存导致旧版本 APK

**发生次数**: v10.3 → v10.5 期间，连续 3 次安装的都是旧版  
**现象**: Artifact 名称是 v10.5，但 APK 文件名是 `tianji-10.3.0`  
**原因**: `.buildozer` 目录缓存了首次成功编译的产物，后续 `buildozer android debug` 检测到已存在就直接复用，**从未编译新代码**  
**解决**: Build 步骤前必须执行 `rm -rf .buildozer bin`  
**验证**: 下载 APK 后第一件事检查文件名版本号  
**防范规则**: workflow 中永远保留 Clean 步骤，绝不删除

---

### 🔴 P0 级（导致 APK 无法生成）

#### 5.2 `yes | buildozer` Broken Pipe

**现象**: 构建"成功"但 Artifacts 为空  
**原因**: `yes |` 管道在 Buildozer 结束后触发 SIGPIPE  
**解决**: 删除 `yes |`，用 `android.accept_sdk_license = True` 代替  
**防范规则**: buildozer 命令不加任何管道

#### 5.3 Gradle 编译失败 (JDK 11 vs 17)

**现象**: `gradle failed!`，日志 3 万行找不到具体错误  
**原因**: GitHub runner 默认 JAVA_HOME 指向 JDK 11，API 33 需要 JDK 17  
**解决**: workflow 显式设置 `JAVA_HOME` 并写入 `$GITHUB_ENV`  
**防范规则**: 固化在 workflow 中，不可删除

#### 5.4 `tail -50` 截断导致静默失败

**现象**: Build 步骤 exit code 0 但没有 APK  
**原因**: `buildozer ... 2>&1 | tail -50` 截断管道，进程被 kill  
**解决**: 不加任何管道后缀  
**防范规则**: buildozer 命令必须是 `buildozer -v android debug`，不加管道

#### 5.5 Kivy 版本锁定编译失败

**现象**: 指定 `kivy==2.3.0` 时 p4a 编译报错  
**解决**: `requirements` 写 `kivy` 不锁版本  

---

### 🟠 P1 级（导致手机端 UI 异常）

#### 5.6 CoreLabel canvas 绘制在 Android 上坐标归零

**现象**: 所有文字堆在屏幕左下角，按钮边框位置和实际位置不匹配  
**原因**: `CoreLabel` + `canvas` 使用绝对坐标 `(self.x, self.y)` 绘制，但在 Android 上 widget 的 pos 更新时机与 canvas 绑定不同步  
**解决**: 所有可见文字改用 `add_widget(Label)`，通过 `bind(pos, size)` 在 `_layout()` 中手动定位  
**防范规则**: 参见第二节 2.1 代码规范

#### 5.7 BoxLayout 子 widget 拦截 touch 事件

**现象**: 按钮按不动，长按无反应  
**原因**: 继承 `BoxLayout` 后，子 Label 拦截了 `on_touch_down` 事件  
**尝试的错误方案**: `label.on_touch_down = lambda t: False`（不可靠）  
**正确方案**: 不继承 BoxLayout，继承 Widget + 手动定位子 Label  
**防范规则**: 自定义交互组件必须继承 Widget

#### 5.8 BoxLayout canvas.before 坐标与布局不同步

**现象**: 按钮的 chamfer 边框画在了别的位置（红框出现在初爻右下方）  
**原因**: BoxLayout 的布局计算和 canvas.before 的绘制时机在 Android 上不一致  
**解决**: 改为 Widget 基类 + `bind(pos, size)` → `_layout()` 统一更新  
**防范规则**: 同 5.7

---

### 🟡 P2 级（导致构建细节问题）

#### 5.9 APK Artifact 路径错误

**现象**: 构建成功但下载不到 APK  
**原因**: `upload-artifact` 的 path 相对仓库根目录，应为 `kivy_app/bin/*.apk`  
**解决**: 写完整相对路径，加 `if-no-files-found: error`

#### 5.10 .github 目录位置错误

**现象**: workflow 不触发  
**原因**: `.github/workflows/` 必须在 **Git 仓库根目录**，不能在子目录  
**解决**: 放在 `d:\snow\iching\.github\workflows\`

---

## 六、Kivy 移动端开发铁律

> 从 v10.0 到 v10.5 的 5 次失败中提炼的规则，**所有 Kivy Android 项目适用**：

### 6.1 Widget 架构规则

```
✅ 正确做法:
class MyButton(Widget):
    def __init__(self):
        super().__init__()
        self._label = Label(text="按钮")
        self.add_widget(self._label)
        self.bind(pos=self._layout, size=self._layout)
    
    def _layout(self, *_):
        self._label.pos = self.pos
        self._label.size = self.size
        self._draw_border()  # canvas 绘制也在这里
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # 处理点击
            return True
        return False

❌ 错误做法:
class MyButton(BoxLayout):  # 不要继承 BoxLayout
    def _draw(self):
        draw_text(self.canvas, ...)  # 不要用 CoreLabel 画文字
```

### 6.2 坐标系规则

| 场景 | PC 表现 | Android 表现 | 结论 |
|------|---------|-------------|------|
| `Widget.canvas` + `self.x, self.y` | ✅ 正确 | ✅ 正确（bind 后） | 可用 |
| `BoxLayout.canvas.before` | ✅ 正确 | ❌ 坐标偏移 | 禁用 |
| `CoreLabel` canvas 绘制 | ✅ 正确 | ❌ 堆叠到左下角 | 仅装饰用 |
| `add_widget(Label)` + bind | ✅ 正确 | ✅ 正确 | **推荐** |

### 6.3 Touch 事件规则

| 基类 | touch 传播 | 结论 |
|------|-----------|------|
| `Widget` | 直接收到 `on_touch_down` | ✅ 推荐 |
| `BoxLayout` | 先传给子 widget，子 widget 可能拦截 | ❌ 不可控 |

---

## 七、手机端测试清单 (Post-Install Checklist)

### 7.0 版本验证（最先做）

- [ ] APK 文件名中版本号 = buildozer.spec 中版本号
- [ ] 如不一致，**立即作废此包，检查 workflow 清缓存步骤**

### 7.1 首页

- [ ] 标题"天机"完整显示，未被截断
- [ ] 所有文字在屏幕正确位置（不在左下角堆叠）
- [ ] 6 个爻位插槽均匀分布
- [ ] "按住·感应天机"按钮宽度撑满（两侧等距边距）
- [ ] 按钮呼吸脉冲效果可见
- [ ] "重置 RESET"按钮正常显示

### 7.2 交互

- [ ] 长按 1.5s 触发生成（touch 响应区域 = 按钮可见区域）
- [ ] 6 爻逐一揭示
- [ ] 自动跳转结果页

### 7.3 结果页

- [ ] 卦象 + 卦名 + 卦辞完整显示
- [ ] 各模块可读
- [ ] 页面可滚动
- [ ] "重新起卦"返回正常

### 7.4 兼容性

- [ ] 竖屏锁定
- [ ] 无白屏/黑屏/闪退
- [ ] 中文字体正常

---

## 八、关键文件索引

```
d:\snow\iching\
├── .github\workflows\build-apk.yml    ← CI/CD 工作流 (含清缓存步骤)
├── iching_data.py                      ← 64 卦数据
├── yaoci_data.py                       ← 爻辞数据
└── kivy_app\
    ├── main.py                         ← 主程序
    ├── buildozer.spec                  ← Buildozer 配置 (版本号在这里)
    ├── gen_icon.py                     ← 图标生成脚本
    ├── NotoSansCJK.otf                 ← 中文字体
    ├── icon.png                        ← 应用图标 (512x512)
    ├── DESIGN_SPEC.md                  ← UI 设计规范
    └── docs\
        ├── UI_KNOWLEDGE.md             ← 项目知识库
        ├── CHECKLIST.md                ← UI 检查清单
        └── BUILD_SPEC.md              ← 本文档
```

---

## 九、版本发布记录

| 版本 | 日期 | 变更摘要 | 结果 |
|------|------|---------|------|
| 2.1.0 | 04-08 | 初始 APK | ✅ |
| 2.2.0 | 04-09 | PC 安装包 + APK | ✅ |
| 10.0.0 | 04-10 | v10 重构：LED 数码管、呼吸光效 | ⚠️ 首次编译成功 |
| 10.1.0 | 04-10 | 改 BoxLayout + Label | ❌ 手机端文字左下角堆叠 |
| 10.2.0 | 04-10 | 太极 icon、改名天机 | ❌ 实际安装的仍是 10.3 旧包 |
| 10.3.0 | 04-10 | 修 native Label | ❌ 缓存导致未真正编译 |
| 10.4.0 | 04-13 | 修 touch 事件 + HUD 装饰 | ❌ 缓存导致未真正编译 |
| 10.5.0 | 04-13 | Widget 基类 + 手动定位 + 清缓存 | � 首次全量重编 |

---

## 十、给 AI 助手的备忘录

> 如果你是 LLM 助手正在帮助此项目出包，请注意：

1. **不要省略清缓存步骤**，哪怕用户说"快速出包"
2. **不要把自定义交互 widget 继承 BoxLayout**，无论看起来多方便
3. **不要用 CoreLabel 画按钮文字**，在 Android 上必定偏位
4. **不要给 buildozer 命令加管道**（`| tail`, `| grep`, `2>&1 |` 都不行）
5. **不要锁定 kivy 版本号**
6. **每次出包后第一件事**：验证 APK 文件名中的版本号
7. **PC 运行正常不代表手机正常**，两个平台的布局时序完全不同

---

> ⚠️ 本文档是 v10.0~v10.5 **五次失败** 的血泪总结。每次出包前必读第〇节和第二节。  
> ⚠️ 遇到新问题务必追加到第五节，附上现象、原因、解决方案。