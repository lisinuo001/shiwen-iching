[app]
title = 易CODE
package.name = yicode
package.domain = org.yicode

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,otf
source.include_patterns = iching_data.py,yaoci_data.py,NotoSansCJK.otf,icon.png,presplash.png

version = 1.0.0

requirements = python3,kivy,pillow

icon.filename = ./icon.png
presplash.filename = ./presplash.png

orientation = portrait
fullscreen = 1

android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.private_storage = True
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
