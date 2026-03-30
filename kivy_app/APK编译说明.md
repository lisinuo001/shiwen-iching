
# 易经算卦 APK 编译说明

## 方式一：使用 WSL (Windows Subsystem for Linux) —— 推荐

### 1. 安装 WSL2 + Ubuntu
```powershell
# 在 Windows PowerShell (管理员) 运行:
wsl --install -d Ubuntu-22.04
```

### 2. 在 Ubuntu 中安装依赖
```bash
sudo apt update && sudo apt install -y \
    python3-pip python3-venv git \
    build-essential libssl-dev \
    zlib1g-dev libbz2-dev libreadline-dev \
    libsqlite3-dev libffi-dev \
    openjdk-17-jdk unzip curl

pip3 install buildozer cython==0.29.33
```

### 3. 将项目文件复制到 WSL
```bash
# 在 WSL 中访问 Windows 文件:
cp -r /mnt/d/snow/iching/kivy_app ~/iching_apk/
cp /mnt/d/snow/iching/iching_data.py ~/iching_apk/
cp /mnt/d/snow/iching/yaoci_data.py ~/iching_apk/
```

### 4. 编译 APK
```bash
cd ~/iching_apk
buildozer android debug
# 首次编译需下载 Android SDK/NDK，约需 20~40 分钟
# 生成的 APK 位于: bin/易经算卦-2.0.0-arm64-v8a-debug.apk
```

---

## 方式二：使用 GitHub Actions 云端自动构建 —— 无需本地环境

在 `kivy_app/.github/workflows/build.yml` 中配置：
```yaml
name: Build APK
on: [push]
jobs:
  build:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with: { python-version: '3.10' }
      - run: pip install buildozer cython==0.29.33
      - run: sudo apt-get install -y openjdk-17-jdk
      - run: buildozer android debug
      - uses: actions/upload-artifact@v3
        with:
          name: iching-apk
          path: bin/*.apk
```

---

## 方式三：使用 Google Colab 在线编译

1. 打开 https://colab.research.google.com
2. 新建 Notebook，运行：
```python
!pip install buildozer cython==0.29.33
!apt-get install -y openjdk-17-jdk
# 上传文件后运行 buildozer android debug
```

---

## 注意事项

- APK 文件生成后传输到手机，需开启"未知来源"安装权限
- 推荐安装到 Android 8.0 (API 26) 及以上版本
- 如遇字体问题，可在 kivy_app/ 中添加中文字体文件（.ttf）并在代码中指定
