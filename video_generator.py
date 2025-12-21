# 单页视频生成模块
"""
单页视频生成模块 - 使用ffmpeg生成每页的视频
参考FFmpeg使用技巧[citation:5]
"""

import os
import subprocess
import xml.etree.ElementTree as ET
from config import VIDEO_DIR, TEMP_DIR, FFMPEG_PATH, VOICE_DIR

def generate_page_videos():
    """
    为每页PPT生成带音频的视频
    
    返回:
        bool: 是否成功生成所有视频
    """
    os.makedirs(VIDEO_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # 获取XML和音频文件
    xml_files = [f for f in os.listdir(TEMP_DIR) if f.startswith('slide_') and f.endswith('.xml')]
    audio_files = [f for f in os.listdir(VOICE_DIR) if f.endswith('.mp3')]
    
    if not xml_files or not audio_files:
        print("错误：缺少XML或音频文件")
        return False
    
    success_count = 0
    
    for xml_file in sorted(xml_files, key=lambda x: int(x.split('_')[1].split('.')[0])):
        page_num = int(xml_file.split('_')[1].split('.')[0])
        
        # 查找对应的音频文件
        audio_file = f"page_{page_num}.mp3"
        audio_path = os.path.join(VOICE_DIR, audio_file)
        
        if not os.path.exists(audio_path):
            print(f"警告：找不到音频文件 {audio_file}")
            continue
        
        # 生成视频
        video_path = os.path.join(VIDEO_DIR, f"page_{page_num}.mp4")
        
        if create_single_video(xml_file, audio_path, video_path):
            success_count += 1
            print(f"已生成视频: {video_path}")
        else:
            print(f"生成视频失败: page_{page_num}")
    
    print(f"视频生成完成: {success_count}/{len(xml_files)} 个文件成功")
    return success_count > 0

def create_single_video(xml_file, audio_path, output_path):
    """
    创建单页PPT视频
    
    参数:
        xml_file: XML文件名
        audio_path: 音频文件路径
        output_path: 输出视频路径
    
    返回:
        bool: 是否成功
    """
    xml_path = os.path.join(TEMP_DIR, xml_file)
    
    try:
        # 解析XML获取页面元素
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 获取音频时长
        audio_duration = get_audio_duration(audio_path)
        
        if audio_duration is None:
            print(f"错误：无法获取音频时长 {audio_path}")
            return False
        
        # 创建临时图片（这里简化处理，实际应该从PPT提取或创建）
        # 在实际项目中，这里应该解析XML创建对应的图片或视频序列
        temp_image = create_temp_image(xml_file)
        
        if not temp_image:
            return False
        
        # 使用ffmpeg创建视频
        # 基本命令：将图片转为视频，然后添加音频[citation:5]
        cmd = [
            FFMPEG_PATH,
            '-y',  # 覆盖输出文件
            '-loop', '1',
            '-i', temp_image,
            '-i', audio_path,
            '-c:v', 'libx264',
            '-t', str(audio_duration),
            '-pix_fmt', 'yuv420p',
            '-shortest',
            output_path
        ]
        
        # 执行ffmpeg命令
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"ffmpeg错误: {result.stderr}")
            return False
        
        # 清理临时文件
        os.remove(temp_image)
        
        return True
        
    except Exception as e:
        print(f"创建视频失败: {e}")
        return False

def get_audio_duration(audio_path):
    """
    获取音频文件时长
    
    参数:
        audio_path: 音频文件路径
    
    返回:
        float: 音频时长（秒），失败返回None
    """
    try:
        cmd = [
            FFMPEG_PATH,
            '-i', audio_path,
            '-f', 'null',
            '-'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 从输出中解析时长
        for line in result.stderr.split('\n'):
            if 'Duration:' in line:
                time_str = line.split('Duration:')[1].split(',')[0].strip()
                h, m, s = time_str.split(':')
                return float(h) * 3600 + float(m) * 60 + float(s)
        
        return None
    except Exception as e:
        print(f"获取音频时长失败: {e}")
        return None

def create_temp_image(xml_file):
    """
    创建临时图片用于视频生成
    在实际项目中，这里应该根据XML内容创建对应的图像
    """
    from PIL import Image, ImageDraw, ImageFont
    
    # 创建简单的图片
    img_path = os.path.join(TEMP_DIR, f"temp_{xml_file.replace('.xml', '.png')}")
    
    try:
        # 创建一个简单的背景
        img = Image.new('RGB', (1920, 1080), color='lightblue')
        draw = ImageDraw.Draw(img)
        
        # 添加文字
        text = f"PPT Page {xml_file.replace('.xml', '').replace('slide_', '')}"
        # 注意：这里需要字体文件，简化处理
        draw.text((100, 100), text, fill='black')
        
        img.save(img_path)
        return img_path
    except Exception as e:
        print(f"创建临时图片失败: {e}")
        return None