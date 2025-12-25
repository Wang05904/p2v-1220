#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件 - 从环境变量或.env文件读取配置
安全提示：敏感信息不应硬编码在代码中
"""

import os
import sys
from pathlib import Path

# 基础目录
BASE_DIR = Path(__file__).parent.absolute()

def load_env_file():
    """加载.env文件中的环境变量"""
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释
                    if not line or line.startswith('#'):
                        continue
                    # 解析键值对
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        # 设置环境变量（如果尚未设置）
                        if key and value and os.getenv(key) is None:
                            os.environ[key] = value
        except Exception as e:
            print(f"警告: 读取.env文件失败: {e}")

def get_config(key, default=None, required=False):
    """
    获取配置值，优先级：环境变量 > .env文件 > 默认值
    
    Args:
        key: 配置键名
        default: 默认值
        required: 是否为必需配置
    
    Returns:
        配置值
    """
    # 先尝试从环境变量获取
    value = os.getenv(key)
    
    # 如果环境变量中没有，尝试加载.env文件
    if value is None:
        load_env_file()
        value = os.getenv(key)
    
    # 如果仍然没有，使用默认值
    if value is None:
        value = default
    
    # 检查必需配置
    if required and (value is None or value == ""):
        print(f"错误: 必需配置项 '{key}' 未设置！")
        print("请执行以下操作之一：")
        print("1. 设置环境变量:")
        print(f"   export {key}=your_value")
        print("2. 创建 .env 文件并添加配置:")
        print(f"   {key}=your_value")
        print(f"3. 复制 .env.example 为 .env 并填写真实值")
        sys.exit(1)
    
    return value

# 加载.env文件（如果存在）
load_env_file()

# ========== API配置 ==========
# 硅基流动API配置
SILICONFLOW_API_KEY = get_config('SILICONFLOW_API_KEY', required=True)
SILICONFLOW_API_URL = get_config('SILICONFLOW_API_URL', "https://api.siliconflow.cn/v1/chat/completions")

# 讯飞星火API配置
XUNFEI_APP_ID = get_config('XUNFEI_APP_ID', required=True)
XUNFEI_API_KEY = get_config('XUNFEI_API_KEY', required=True)
XUNFEI_API_SECRET = get_config('XUNFEI_API_SECRET', required=True)
XUNFEI_TTS_URL = get_config('XUNFEI_TTS_URL', "wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6")

# ========== 路径配置 ==========
# 工具路径
FFMPEG_PATH = get_config('FFMPEG_PATH', "ffmpeg")

# 目录配置（相对于项目根目录）
SCRIPT_DIR = get_config('SCRIPT_DIR', "script")
VOICE_DIR = get_config('VOICE_DIR', "voice")
VIDEO_DIR = get_config('VIDEO_DIR', "video")
TEMP_DIR = get_config('TEMP_DIR', "temp")
IMG_DIR = get_config('IMG_DIR', "img")
TEMP_VIDEO= get_config('TEMP_VIDEO', "temp/video")

# 转换为绝对路径
SCRIPT_DIR = str(BASE_DIR / SCRIPT_DIR)
VOICE_DIR = str(BASE_DIR / VOICE_DIR)
VIDEO_DIR = str(BASE_DIR / VIDEO_DIR)
TEMP_DIR = str(BASE_DIR / TEMP_DIR)
IMG_DIR = str(BASE_DIR / IMG_DIR)
TEMP_VIDEO = str(BASE_DIR / TEMP_VIDEO)

# ========== 配置验证 ==========
def validate_config():
    """验证配置是否完整"""
    print("=" * 50)
    print("配置验证")
    print("=" * 50)
    
    configs = {
        "硅基流动API密钥": SILICONFLOW_API_KEY,
        "讯飞APP_ID": XUNFEI_APP_ID,
        "讯飞API_KEY": XUNFEI_API_KEY,
        "讯飞API_SECRET": XUNFEI_API_SECRET,
    }
    
    all_valid = True
    for name, value in configs.items():
        if not value:
            print(f"❌ {name}: 未设置")
            all_valid = False
        else:
            masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"✅ {name}: {masked}")
    
    print(f"📁 脚本目录: {SCRIPT_DIR}")
    print(f"🔊 音频目录: {VOICE_DIR}")
    print(f"🎬 视频目录: {VIDEO_DIR}")
    print(f"🗑️  临时目录: {TEMP_DIR}")
    print("=" * 50)
    
    if not all_valid:
        print("\n❌ 配置不完整！请按照上方提示设置缺失的配置项。")
        return False
    
    # 创建必要目录
    for directory in [SCRIPT_DIR, VOICE_DIR, VIDEO_DIR, TEMP_DIR]:
        os.makedirs(directory, exist_ok=True)
        print(f"已确保目录存在: {directory}")
    
    print("\n✅ 所有配置验证通过！")
    return True

# 如果直接运行此文件，则验证配置
if __name__ == "__main__":
    validate_config()