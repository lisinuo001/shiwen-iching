# 如何用 GitHub Actions 编译 Android APK

## 一次性操作（5分钟完成）

### 第1步：注册 GitHub 账号（已有跳过）
访问 https://github.com → 注册免费账号

---

### 第2步：创建新仓库
1. 登录 GitHub → 点右上角 **+** → **New repository**
2. Repository name 填：`shiwen-iching`
3. 选 **Private**（私有，不公开代码）
4. 点 **Create repository**

---

### 第3步：上传代码
在仓库页面点 **uploading an existing file**，把以下文件全部上传：

```
d:\snow\iching\
├── main.py
├── iching_data.py
├── yaoci_data.py
├── iching_icon.ico
├── iching_icon.png
├── kivy_app\
│   ├── main.py
│   └── buildozer.spec
└── .github\
    └── workflows\
        └── build-apk.yml
```

> ⚠️ 注意：`.github` 文件夹需要手动创建或用 git 上传

---

### 第4步：等待自动编译（约 20-30 分钟）
- 上传完成后，点仓库顶部的 **Actions** 标签
- 会看到 **Build Android APK** 正在运行（黄色圆圈）
- 等待变成绿色 ✅ 表示成功

---

### 第5步：下载 APK
1. 点击成功的 workflow run
2. 页面底部找到 **Artifacts** 区域
3. 点击 **ShiWen-APK** 下载 ZIP
4. 解压得到 `shiwen-2.1.0-arm64-v8a-debug.apk`

---

### 第6步：安装到手机
1. 把 APK 发送到手机（微信/QQ/邮件均可）
2. 手机打开 APK 文件
3. 如提示"未知来源"，进入 **设置 → 安全 → 允许安装未知应用**
4. 安装完成，桌面出现「筮问 ShiWen」图标

---

## 如果用 git 命令行（可选）
```bash
cd d:\snow\iching
git init
git add .
git commit -m "筮问 ShiWen v2.1.0"
git remote add origin https://github.com/你的用户名/shiwen-iching.git
git push -u origin main
```

---

## 遇到问题？
- Actions 失败：点红色 ❌ → 查看日志 → 截图发给我
- APK 安装失败：确认手机是 Android 5.0+，CPU 是 arm64
