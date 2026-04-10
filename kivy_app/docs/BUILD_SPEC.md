# 出包规范 BUILD_SPEC

> 版本: v1.0  
> 创建日期: 2026-04-10  
> 适用项目: 筮问 ShiWen (Kivy Android APK)  
> 状态: 🟢 ACTIVE

---

## 一、出包方式

采用 **GitHub Actions 云端自动构建**，无需本地 Linux 环境。

| 项目 | 值 |
|------|------|
| 仓库地址 | `https://github.com/lisinuo001/shiwen-iching` |
| 触发条件 | push 到 `main`/`master` 分支，或手动 `workflow_dispatch` |
| 构建环境 | `ubuntu-22.04` |
| 超时时间 | 60 分钟 |
| 产物位置 | Actions → 对应 run → Artifacts → `ShiWen-APK-vXX` |
| 产物保留 | 30 天 |

---

## 二、出包前检查清单 (Pre-Build Checklist)

每次出包前 **必须** 逐条确认：

### 2.1 代码检查

- [ ] `main.py` 在 PC 上用 `py -3.11 main.py` 运行正常，无崩溃
- [ ] 所有 widget 的文字使用 **原生 Label**（不用 CoreLabel canvas 绘制长文字），避免手机端字体渲染偏移
- [ ] `CoreLabel` 仅用于 canvas 装饰性小文字（LED 数字、爻线标注等）
- [ ] 未引入新的外部依赖包（若有，需同步更新 `buildozer.spec` 的 `requirements`）
- [ ] 没有使用 Python 3.11+ 专属语法（构建环境为 Python 3.10）

### 2.2 资源检查

- [ ] 字体文件 `NotoSansCJK.otf` 存在于 `kivy_app/` 目录
- [ ] 图标文件 `icon.png` 存在于 `kivy_app/` 目录
- [ ] 数据文件 `iching_data.py` 和 `yaoci_data.py` 存在于 `iching/` 根目录
- [ ] 未依赖任何 PNG 贴图做核心渲染（所有视觉元素均程序化绘制）

### 2.3 配置检查

- [ ] `buildozer.spec` 中 `version` 已更新为新版本号
- [ ] `source.include_patterns` 包含所有必需文件
- [ ] `requirements` 不锁定不兼容的版本（推荐 `python3,kivy,pillow`）
- [ ] `android.accept_sdk_license = True` 已设置

### 2.4 兼容性检查

- [ ] 未使用 `Window.size = (x, y)` 在非 `__main__` 块中（手机端会被忽略但不应在全局设置）
- [ ] 所有布局使用 `size_hint` 或 `dp()`/`sp()` 单位，无硬编码像素值
- [ ] 按钮最小点击区域 >= `dp(44)`

---

## 三、出包操作流程

### 第1步：更新版本号

```
文件: kivy_app/buildozer.spec
字段: version = X.Y.Z
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

确认：
- 首页正常显示
- 长按生成 → 六爻逐一揭示
- 结果页完整显示所有模块
- 返回+重置功能正常

### 第3步：提交推送

```bash
cd d:\snow\iching
git add .
git commit -m "vX.Y.Z: 变更描述"
git push origin main
```

### 第4步：监控构建

1. 打开 https://github.com/lisinuo001/shiwen-iching/actions
2. 等待最新 workflow run 变为 ✅ 绿色（约 15-25 分钟）
3. 如失败 ❌，查看 `Build APK` 步骤日志，定位错误

### 第5步：下载 APK

1. 点击成功的 workflow run
2. 页面底部 **Artifacts** 区域
3. 下载 ZIP → 解压 → 得到 `.apk` 文件

### 第6步：安装测试

1. 将 APK 传输到手机（微信/QQ/邮件/USB）
2. 安装（需开启"未知来源"权限）
3. 按照第六节的测试清单验证

---

## 四、环境依赖参数 (固化)

以下参数经过多轮调试验证可用，**不要随意修改**：

| 参数 | 值 | 备注 |
|------|------|------|
| GitHub Runner | `ubuntu-22.04` | Buildozer 稳定运行 |
| Python 版本 | `3.10` | p4a 兼容性最佳 |
| JDK 版本 | `openjdk-17` | Android API 33 要求 |
| Cython | `0.29.36` | Kivy 编译要求 |
| JAVA_HOME | `/usr/lib/jvm/java-17-openjdk-amd64` | 必须显式设置，否则默认 JDK 11 |
| Android API | `33` | 目标 API |
| Min API | `21` | 最低支持 Android 5.0 |
| NDK | `25b` | 与 p4a 兼容 |
| 架构 | `arm64-v8a` | 主流手机 CPU |

---

## 五、踩坑记录 (历史问题)

### 5.1 `yes | buildozer` 导致 Broken Pipe

**现象**: 构建看似成功但无 APK 产出  
**原因**: `yes |` 管道在 Buildozer 结束后产生 Broken Pipe 信号，干扰退出码  
**解决**: 去掉 `yes |`，靠 `android.accept_sdk_license = True` 自动接受许可证

### 5.2 Gradle 编译失败 (JDK 版本不匹配)

**现象**: `gradle failed!` 错误  
**原因**: GitHub runner 默认 JAVA_HOME 指向 JDK 11，但 API 33 需要 JDK 17  
**解决**: 在 workflow 中显式设置 `JAVA_HOME` 环境变量

### 5.3 `tail -50` 截断输出导致静默失败

**现象**: Build 步骤"成功"但实际编译未完成  
**原因**: `buildozer ... 2>&1 | tail -50` 导致管道截断，进程提前退出  
**解决**: 直接运行 `buildozer -v android debug`，不加管道

### 5.4 手机端文字截断/偏移

**现象**: 安装到手机后文字被切掉、按钮只占半边  
**原因**: `CoreLabel` canvas 绘制的文字在不同 DPI 设备上坐标计算不一致  
**解决**: 按钮和标题改用原生 Kivy `Label` widget，`CoreLabel` 仅用于小型装饰文字

### 5.5 Kivy 版本锁定导致编译不兼容

**现象**: `kivy==2.3.0` 在 p4a 中编译失败  
**原因**: 锁定的版本与当前 python-for-android 不兼容  
**解决**: `requirements` 中写 `kivy`（不锁版本），让 Buildozer 自动选择兼容版本

### 5.6 APK Artifact 路径错误

**现象**: 构建成功但下载不到 APK  
**原因**: `upload-artifact` 的 `path` 相对于仓库根目录，而 `bin/` 在 `kivy_app/` 下  
**解决**: 路径写为 `kivy_app/bin/*.apk`

---

## 六、手机端测试清单 (Post-Install Checklist)

安装到手机后，按以下清单验证：

### 6.1 首页

- [ ] 标题"天机"完整显示，未被截断
- [ ] 6 个爻位插槽可见（灰色占位线）
- [ ] LED 数码管幽灵轮廓可见
- [ ] "按住·感应天机"按钮有呼吸脉冲效果
- [ ] 按钮宽度撑满屏幕（两侧有等距边距）
- [ ] "重置 RESET"按钮正常显示

### 6.2 交互

- [ ] 长按按钮 1.5s 后触发生成
- [ ] 6 个爻逐一显示（每个间隔约 0.3s）
- [ ] LED 数字 0/1 清晰可辨
- [ ] 小阴阳爻线正确显示（阳=实线，阴=断线）
- [ ] 烟雾粒子效果触发
- [ ] 自动跳转到结果页

### 6.3 结果页

- [ ] 卦象（6 条爻线）正确显示
- [ ] 卦名为最大字号
- [ ] 卦辞（古文）显示在卦名下方
- [ ] "卦象含义"模块文字可读
- [ ] "白话解读"模块文字可读，无"【白话】"前缀
- [ ] "六爻详解"模块字号较小
- [ ] 页面可正常滚动
- [ ] "重新起卦"按钮可正常返回首页

### 6.4 兼容性

- [ ] 竖屏锁定正常
- [ ] 未出现白屏/黑屏/闪退
- [ ] 中文字体正常显示（非方块乱码）

---

## 七、关键文件索引

```
d:\snow\iching\
├── .github\workflows\build-apk.yml    ← GitHub Actions 工作流
├── iching_data.py                      ← 64 卦数据（构建时复制到 kivy_app/）
├── yaoci_data.py                       ← 爻辞数据（构建时复制到 kivy_app/）
└── kivy_app\
    ├── main.py                         ← 主程序
    ├── buildozer.spec                  ← Buildozer 配置
    ├── NotoSansCJK.otf                 ← 中文字体
    ├── icon.png                        ← 应用图标
    ├── DESIGN_SPEC.md                  ← UI 设计规范
    └── docs\
        ├── UI_KNOWLEDGE.md             ← 项目知识库
        ├── CHECKLIST.md                ← UI 检查清单
        └── BUILD_SPEC.md              ← 本文档（出包规范）
```

---

## 八、版本发布记录

| 版本 | 日期 | 变更摘要 | 状态 |
|------|------|---------|------|
| 2.1.0 | 2026-04-08 | 初始 APK 构建 | ✅ |
| 2.2.0 | 2026-04-09 | PC 安装包 + APK | ✅ |
| 10.0.0 | 2026-04-10 | v10 全面重构: LED 数码管、呼吸光效、布局优化 | 🔧 调试中 |

---

> ⚠️ **重要提醒**: 每次出包前，必须回顾本文档第二节检查清单。  
> ⚠️ **遇到新问题**: 务必记录到第五节踩坑记录，防止重蹈覆辙。
