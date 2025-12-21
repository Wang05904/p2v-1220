import os
import subprocess
import re
from config import IMG_DIR, VIDEO_DIR, VOICE_DIR

def get_audio_duration(audio_path):
    """获取音频时长（秒），兼容各种编码格式"""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            "-hide_banner",
            audio_path
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8',
            errors='ignore'
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"❌ 获取音频时长失败：{e}")
        return None

def check_audio_in_video(video_path):
    """检查视频是否包含音频流"""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "stream=codec_type",
            "-of", "csv=p=0",
            "-hide_banner",
            video_path
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8',
            errors='ignore'
        )
        return "audio" in result.stdout.strip()
    except Exception:
        return False

def generate_page_videos():
    """
    最终版：无滤镜错误，确保音频嵌入视频
    """
    # 1. 目录校验
    for dir_name, dir_path in {"图片目录": IMG_DIR, "音频目录": VOICE_DIR, "视频目录": VIDEO_DIR}.items():
        if not os.path.exists(dir_path):
            print(f"❌ {dir_name}不存在：{dir_path}")
            return

    # 2. 匹配图片文件
    img_pattern = re.compile(r"^page_(\d+)\.png$")
    img_files = [f for f in os.listdir(IMG_DIR) if img_pattern.match(f)]
    
    if not img_files:
        print(f"⚠️ 图片目录 {IMG_DIR} 中未找到page_*.png格式的文件")
        return

    # 3. 遍历处理每个文件
    for img_file in img_files:
        match = img_pattern.match(img_file)
        page_num = match.group(1)
        
        # 拼接路径（转短路径，避免中文/空格问题）
        img_path = os.path.abspath(os.path.join(IMG_DIR, img_file))
        audio_path = os.path.abspath(os.path.join(VOICE_DIR, f"page_{page_num}.mp3"))
        video_path = os.path.abspath(os.path.join(VIDEO_DIR, f"page_{page_num}.mp4"))

        # 检查音频文件
        if not os.path.exists(audio_path):
            print(f"⚠️ 音频文件不存在，跳过：{audio_path}")
            continue

        # 获取音频时长
        audio_duration = get_audio_duration(audio_path)
        if not audio_duration or audio_duration <= 0:
            print(f"⚠️ 音频时长无效，跳过：{audio_path}")
            continue

        print(f"\n📌 开始处理：page_{page_num}")
        print(f"   图片：{img_path}")
        print(f"   音频：{audio_path} (时长：{audio_duration:.2f}秒)")
        print(f"   输出：{video_path}")

        # ========== 修正后的ffmpeg命令（核心） ==========
        # 关键改进：
        # 1. 移除错误的filter_complex
        # 2. 先输入图片，再输入音频，-t参数精准控制时长
        # 3. 明确映射音视频流，确保音频嵌入
        try:
            cmd = [
                "ffmpeg",
                "-y",  # 覆盖已有文件
                "-v", "error",  # 只输出错误
                "-hide_banner", # 隐藏无关信息
                # 输入1：图片（循环播放）
                "-loop", "1",
                "-i", img_path,
                # 输入2：音频
                "-i", audio_path,
                # 视频参数
                "-c:v", "libx264",        # H.264编码器（兼容性最好）
                "-pix_fmt", "yuv420p",    # 兼容所有播放器
                "-framerate", "25",       # 标准帧率
                "-t", f"{audio_duration:.2f}",  # 精准设置视频时长=音频时长
                # 音频参数（强制兼容MP4）
                "-c:a", "aac",            # MP4标准音频编码器
                "-b:a", "192k",           # 音频码率
                "-ar", "44100",           # 标准采样率
                # 明确映射流（关键！确保音频被包含）
                "-map", "0:v",            # 映射图片的视频流
                "-map", "1:a",            # 映射音频的音频流
                # 输出视频
                video_path
            ]

            # 执行ffmpeg命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8',
                errors='ignore'
            )

            # 验证结果
            if os.path.exists(video_path):
                has_audio = check_audio_in_video(video_path)
                if has_audio:
                    print(f"✅ 视频生成成功！音频已嵌入")
                else:
                    print(f"⚠️ 视频生成但无音频，尝试修复...")
                    # 备用修复方案：重新封装音频
                    fix_video_path = video_path.replace(".mp4", "_fix.mp4")
                    fix_cmd = [
                        "ffmpeg", "-y",
                        "-i", video_path,
                        "-i", audio_path,
                        "-c:v", "copy",  # 视频流直接复制，不重新编码
                        "-c:a", "aac",
                        "-map", "0:v",
                        "-map", "1:a",
                        fix_video_path
                    ]
                    subprocess.run(fix_cmd, capture_output=True, encoding='utf-8', errors='ignore')
                    if os.path.exists(fix_video_path):
                        os.replace(fix_video_path, video_path)
                        print(f"✅ 音频修复成功！")
                    else:
                        print(f"❌ 音频修复失败")
            else:
                print(f"❌ 视频文件未生成")

        except subprocess.CalledProcessError as e:
            print(f"❌ ffmpeg执行失败：{e.stderr[:300]}")  # 只打印前300字符
        except Exception as e:
            print(f"❌ 处理失败：{str(e)}")

    print("\n📝 所有文件处理完成！")
    return True

# 测试调用
if __name__ == "__main__":
    # 检查ffmpeg是否安装
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except FileNotFoundError:
        print("❌ 未找到ffmpeg！请安装并添加到系统环境变量")
        exit(1)
    
    generate_page_videos()