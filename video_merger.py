import os
import subprocess
import re
from pathlib import Path

from config import VIDEO_DIR, TEMP_DIR, FFMPEG_PATH, VOICE_DIR

def extract_page_number(filename):
    """从文件名中提取页码数字"""
    match = re.search(r'page_(\d+)\.mp4$', filename)
    return int(match.group(1)) if match else None

def create_fade_filter(input_file, output_file, fade_duration=1.0):
    """为单个视频创建渐入渐出效果"""
    # 获取视频时长
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 
           'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', input_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"无法获取视频时长: {input_file}")
        return None
    
    try:
        duration = float(result.stdout.strip())
    except ValueError:
        print(f"无法解析视频时长: {input_file}")
        return None
    
    # 如果视频时长小于两倍的淡入淡出时间，调整淡入淡出时间
    if duration < fade_duration * 2:
        fade_duration = duration / 3
    
    # 构建带渐入渐出效果的FFmpeg命令
    fade_filter = f"fade=t=in:st=0:d={fade_duration},fade=t=out:st={duration-fade_duration}:d={fade_duration}"
    
    cmd = [
        'ffmpeg',
        '-i', input_file,
        '-vf', fade_filter,
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-y',  # 覆盖输出文件
        output_file
    ]
    
    print(f"正在为 {os.path.basename(input_file)} 添加渐入渐出效果...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"处理失败: {input_file}")
        print(f"错误信息: {result.stderr}")
        return None
    
    return output_file

def concatenate_videos(video_files, output_file):
    """拼接多个视频文件"""
    if not video_files:
        print("没有可拼接的视频文件")
        return False
    
    # 创建临时文件列表
    list_file = 'concat_list.txt'
    
    with open(list_file, 'w') as f:
        for video in video_files:
            f.write(f"file '{video}'\n")
    
    # 使用FFmpeg进行拼接
    cmd = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', list_file,
        '-c', 'copy',  # 直接复制编码，避免重新编码
        '-y',
        output_file
    ]
    
    print(f"正在拼接 {len(video_files)} 个视频...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # 清理临时文件
    if os.path.exists(list_file):
        os.remove(list_file)
    
    if result.returncode != 0:
        print(f"拼接失败")
        print(f"错误信息: {result.stderr}")
        return False
    
    return True

def merge_videos():
    # 设置目录和文件
    OUTPUT_FILE = './final_video.mp4'
    TEMP_DIR = './temp_faded_videos'
    
    # 确保目录存在
    Path(VIDEO_DIR).mkdir(parents=True, exist_ok=True)
    Path(TEMP_DIR).mkdir(parents=True, exist_ok=True)
    
    # 获取所有page_*.mp4文件
    video_files = []
    for file in os.listdir(VIDEO_DIR):
        if file.endswith('.mp4') and file.startswith('page_'):
            video_files.append(file)
    
    if not video_files:
        print(f"在 {VIDEO_DIR} 目录中未找到 page_*.mp4 文件")
        return
    
    # 按页码排序
    video_files.sort(key=lambda x: extract_page_number(x))
    
    print(f"找到 {len(video_files)} 个视频文件:")
    for vf in video_files:
        print(f"  - {vf}")
    
    # 处理每个视频，添加渐入渐出效果
    faded_videos = []
    for video_file in video_files:
        input_path = os.path.join(VIDEO_DIR, video_file)
        output_path = os.path.join(TEMP_DIR, f"faded_{video_file}")
        
        faded_video = create_fade_filter(input_path, output_path)
        if faded_video:
            faded_videos.append(faded_video)
    
    if not faded_videos:
        print("没有成功处理的视频")
        return
    
    # 拼接所有处理后的视频
    success = concatenate_videos(faded_videos, OUTPUT_FILE)
    
    # 清理临时文件
    print("清理临时文件...")
    for temp_video in faded_videos:
        if os.path.exists(temp_video):
            os.remove(temp_video)
    
    if os.path.exists(TEMP_DIR) and not os.listdir(TEMP_DIR):
        os.rmdir(TEMP_DIR)
    
    if success:
        print(f"\n✅ 视频处理完成！最终视频已保存为: {os.path.abspath(OUTPUT_FILE)}")
        print(f"   文件大小: {os.path.getsize(OUTPUT_FILE) / (1024*1024):.2f} MB")
    else:
        print("\n❌ 视频处理失败")
    return success,OUTPUT_FILE

def check_ffmpeg_installed():
    """检查FFmpeg是否已安装"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

# if __name__ == "__main__":
#     # 检查FFmpeg是否安装
#     if not check_ffmpeg_installed():
#         print("错误: 请先安装FFmpeg")
#         print("Ubuntu/Debian: sudo apt-get install ffmpeg")
#         print("macOS: brew install ffmpeg")
#         print("Windows: 从 https://ffmpeg.org/download.html 下载")
#         exit(1)
    
#     # 运行主程序
#     main()