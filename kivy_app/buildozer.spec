
[app]
title = 筮问 ShiWen
package.name = shiwen
package.domain = org.shiwen

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,otf
source.include_patterns = iching_data.py,yaoci_data.py,NotoSansCJK.otf,icon.png

version = 2.2.0

requirements = python3,kivy==2.2.1,pillow

icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png

orientation = portrait
fullscreen = 0

android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.private_storage = True
android.accept_sdk_license = True
android.arch = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
