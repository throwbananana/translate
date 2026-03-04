#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频管理器 (Audio Manager)
使用 edge-tts 生成有声书
"""

import os
import asyncio
import threading
from pathlib import Path

# 检查 edge-tts 是否可用
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

class AudioManager:
    # 常用语音角色
    VOICES = {
        'zh-CN-XiaoxiaoNeural': '中文女声 (晓晓)',
        'zh-CN-YunxiNeural': '中文男声 (云希)',
        'en-US-JennyNeural': '英文女声 (Jenny)',
        'en-US-GuyNeural': '英文男声 (Guy)',
        'ja-JP-NanamiNeural': '日文女声 (七海)',
        'ja-JP-KeitaNeural': '日文男声 (圭太)'
    }

    def __init__(self):
        self.is_generating = False

    def check_dependency(self):
        if not EDGE_TTS_AVAILABLE:
            return False, "未安装 edge-tts 库。请运行: pip install edge-tts"
        return True, ""

    async def _generate_audio(self, text, output_file, voice, rate='+0%', volume='+0%'):
        communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
        await communicate.save(output_file)

    def generate_audiobook(self, text, output_path, voice_key='zh-CN-XiaoxiaoNeural', progress_callback=None):
        """
        生成有声书 (同步包装异步方法)
        
        Args:
            text: 要朗读的文本
            output_path: 输出文件路径 (.mp3)
            voice_key: 语音角色 ID
            progress_callback: 进度回调 (目前 edge-tts 不支持实时进度，只能回调开始/结束)
        """
        ok, msg = self.check_dependency()
        if not ok:
            raise ImportError(msg)

        if not text:
            raise ValueError("文本为空")

        self.is_generating = True
        
        try:
            # 运行异步任务
            asyncio.run(self._generate_audio(text, output_path, voice_key))
            if progress_callback:
                progress_callback(100)
        except Exception as e:
            raise e
        finally:
            self.is_generating = False

    def get_voices(self):
        return self.VOICES
