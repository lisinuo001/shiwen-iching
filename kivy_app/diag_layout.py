# -*- coding: utf-8 -*-
"""
TIANJI Layout Diagnostic - 最小化布局测试
这个文件会在屏幕上显示4个全宽色块，如果 Android 上看到的色块
不是全屏宽度或有偏移，就说明是 Kivy 框架层面的问题。
"""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.metrics import dp, sp

Window.clearcolor = [0.06, 0.07, 0.11, 1]

class DiagApp(App):
    def build(self):
        root = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        # Block 1: Red - should be full width
        b1 = Widget(size_hint=(1, 1))
        with b1.canvas:
            Color(1, 0.2, 0.2, 1)
            b1._r = Rectangle(pos=b1.pos, size=b1.size)
        b1.bind(pos=lambda w,v: setattr(w._r, 'pos', v),
                size=lambda w,v: setattr(w._r, 'size', v))
        root.add_widget(b1)

        # Block 2: Green
        b2 = Widget(size_hint=(1, 1))
        with b2.canvas:
            Color(0.2, 0.9, 0.3, 1)
            b2._r = Rectangle(pos=b2.pos, size=b2.size)
        b2.bind(pos=lambda w,v: setattr(w._r, 'pos', v),
                size=lambda w,v: setattr(w._r, 'size', v))
        root.add_widget(b2)

        # Block 3: Blue
        b3 = Widget(size_hint=(1, 1))
        with b3.canvas:
            Color(0.2, 0.4, 1.0, 1)
            b3._r = Rectangle(pos=b3.pos, size=b3.size)
        b3.bind(pos=lambda w,v: setattr(w._r, 'pos', v),
                size=lambda w,v: setattr(w._r, 'size', v))
        root.add_widget(b3)

        # Info label
        info = Label(
            text=f"Window: {Window.width}x{Window.height}\n"
                 f"density: {Window._density if hasattr(Window,'_density') else 'N/A'}\n"
                 f"dp(100)={dp(100):.0f}  sp(16)={sp(16):.0f}",
            font_size=sp(14),
            size_hint=(1, None), height=dp(80),
            halign='center', valign='middle')
        info.bind(size=lambda w,s: setattr(w,'text_size',s))
        root.add_widget(info)

        return root

if __name__ == "__main__":
    Window.size = (390, 844)
    DiagApp().run()
