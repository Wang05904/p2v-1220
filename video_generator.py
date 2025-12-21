# video_maker.py
import os
import subprocess
import re
from config import IMG_DIR, VIDEO_DIR, VOICE_DIR

def get_audio_duration(audio_path):
    """
    获取音频文件的时长（秒），使用ffprobe解析
    """
    try:
        # ffprobe命令：获取音频时长（精确到毫秒）
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
        return duration
    except Exception as e:
        print(f"❌ 获取音频 {audio_path} 时长失败：{e}")
        return None

def generate_page_videos():
    """
    将IMG_DIR中的page_*.png与VOICE_DIR中的page_*.mp3拼接为视频，保存到VIDEO_DIR
    """
    # 1. 校验目录是否存在
    for dir_name, dir_path in {"图片目录": IMG_DIR, "音频目录": VOICE_DIR, "视频目录": VIDEO_DIR}.items():
        if not os.path.exists(dir_path):
            print(f"❌ {dir_name}不存在：{dir_path}")
            return
    
    # 2. 匹配IMG_DIR中的page_*.png文件
    img_pattern = re.compile(r"^page_(\d+)\.png$")
    img_files = [f for f in os.listdir(IMG_DIR) if img_pattern.match(f)]
    
    if not img_files:
        print(f"⚠️ 图片目录 {IMG_DIR} 中未找到page_*.png格式的文件")
        return
    
    # 3. 遍历处理每个图片-音频对
    for img_file in img_files:
        # 提取页码（如page_1.png → 1）
        match = img_pattern.match(img_file)
        page_num = match.group(1)
        
        # 拼接各文件路径
        img_path = os.path.abspath(os.path.join(IMG_DIR, img_file))
        audio_path = os.path.abspath(os.path.join(VOICE_DIR, f"page_{page_num}.mp3"))
        video_path = os.path.abspath(os.path.join(VIDEO_DIR, f"page_{page_num}.mp4"))
        
        # 检查音频文件是否存在
        if not os.path.exists(audio_path):
            print(f"⚠️ 音频文件不存在，跳过：{audio_path}")
            continue
        
        # 获取音频时长
        audio_duration = get_audio_duration(audio_path)
        if audio_duration is None or audio_duration <= 0:
            print(f"⚠️ 音频 {audio_path} 时长无效，跳过")
            continue
        
        print(f"\n📌 开始处理：page_{page_num}")
        print(f"   图片：{img_path}")
        print(f"   音频：{audio_path} (时长：{audio_duration:.2f}秒)")
        print(f"   输出：{video_path}")
        
        # 4. 调用ffmpeg合成视频
        # 核心参数说明：
        # -loop 1：循环播放图片
        # -t {audio_duration}：播放时长等于音频时长
        # -i {img_path}：输入图片
        # -i {audio_path}：输入音频
        # -c:v libx264：视频编码器（H.264，兼容性好）
        # -pix_fmt yuv420p：像素格式（兼容大部分播放器）
        # -shortest：取最短输入的时长（确保视频和音频时长一致）
        # -y：覆盖已存在的文件
        try:
            cmd = [
                "ffmpeg",
                "-y",  # 覆盖已有文件
                "-loop", "1",  # 循环播放图片
                "-t", str(audio_duration),  # 视频时长=音频时长
                "-i", img_path,  # 输入图片
                "-i", audio_path,  # 输入音频
                "-c:v", "libx264",  # 视频编码器
                "-pix_fmt", "yuv420p",  # 像素格式（兼容播放器）
                "-c:a", "aac",  # 音频编码器
                "-shortest",  # 确保时长一致
                video_path  # 输出视频
            ]
            
            # 执行ffmpeg命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # 验证输出文件是否存在
            if os.path.exists(video_path):
                print(f"✅ 视频生成成功：{video_path}")
            else:
                print(f"❌ 视频生成失败：文件未创建 {video_path}")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ ffmpeg执行失败：{e.stderr}")
        except Exception as e:
            print(f"❌ 处理page_{page_num}失败：{str(e)}")
    
    print("\n📝 所有文件处理完成！")

# 测试调用
if __name__ == "__main__":
    # 检查ffmpeg是否安装
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except FileNotFoundError:
        print("❌ 未找到ffmpeg！请先安装并添加到系统环境变量")
        exit(1)
    
    # 执行合成
    generate_page_videos()