import os
import subprocess
from pathlib import Path

def merge_video_audio(video_dir="temp/video", audio_dir="voice",output_dir="video"):
    """ 
    清爽版：视频与音频合并，音频长则在视频后添加最后一帧定格
    """
    
    # 1. 获取所有视频
    video_files = [f for f in Path(video_dir).glob("page_*.mp4")]
    print(f"找到 {len(video_files)} 个视频文件")
    
    for video_path in video_files:
        # 2. 提取页码
        slide_num = video_path.stem.split('_')[-1]
        
        # 3. 查找对应音频
        audio_path = Path(audio_dir) / f"page_{slide_num}.mp3"
        
        if not audio_path.exists():
            print(f"跳过 {video_path.name}：未找到对应音频")
            continue
        
        print(f"\n处理: {video_path.name} + {audio_path.name}")
        
        # 4. 获取时长
        video_duration = get_duration(video_path)
        audio_duration = get_duration(audio_path)
        
        if not video_duration or not audio_duration:
            print("  无法获取时长，跳过")
            continue
        
        print(f"  视频: {video_duration:.1f}秒, 音频: {audio_duration:.1f}秒")
        
        # 5. 输出路径（新建文件）
        output_path = Path(output_dir) / f"{video_path.stem}.mp4"
        
        # 6. 执行合并
        if audio_duration <= video_duration:
            # 音频短：直接合并
            success = simple_merge(video_path, audio_path, output_path)
        else:
            # 音频长：在视频后添加最后一帧定格
            success = extend_with_last_frame_simple(video_path, audio_path, output_path, audio_duration)
        
        if success:
            print(f"  ✅ 完成: {output_path.name}")
            # 验证结果
            result_duration = get_duration(output_path)
            if result_duration:
                print(f"  最终时长: {result_duration:.1f}秒")
        else:
            print(f"  ❌ 失败")
    
    print(f"\n处理完成！")
    return True

def get_duration(file_path):
    """获取媒体文件时长（秒）"""
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path)
        ], capture_output=True, text=True)
        return float(result.stdout.strip()) if result.returncode == 0 else None
    except:
        return None

def simple_merge(video_path, audio_path, output_path):
    """简单合并（音频短于视频）"""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(output_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0

def extend_with_last_frame_simple(video_path, audio_path, output_path, audio_duration):
    """
    最简单的方法：使用tpad滤镜直接延长视频
    """
    try:
        # 获取视频时长
        video_duration = get_duration(video_path)
        if not video_duration:
            return False
        
        extend_time = audio_duration - video_duration
        print(f"  需要延长: {extend_time:.1f}秒")
        
        # 单条命令完成：延长视频 + 添加音频
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            # 使用tpad滤镜在结尾添加帧
            "-vf", f"tpad=stop_mode=clone:stop_duration={extend_time}",
            "-af", "apad",  # 为音频添加静音填充（保持同步）
            "-c:v", "libx264",
            "-c:a", "aac",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(output_path)
        ]
        
        # 运行命令，不捕获输出（避免冲突）
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        
        if result.returncode == 0:
            return True
        else:
            print(f"  错误: {result.stderr.decode('utf-8', errors='ignore')[:200]}")
            return False
            
    except Exception as e:
        print(f"  处理出错: {e}")
        return False

# 更简单的方法：如果上面方法不行，用这个
def extend_with_last_frame_alternative(video_path, audio_path, output_path, audio_duration):
    """
    替代方法：使用concat协议
    """
    try:
        # 1. 提取最后一帧
        last_frame = "last_frame.jpg"
        cmd1 = [
            "ffmpeg", "-y",
            "-sseof", "-1",
            "-i", str(video_path),
            "-update", "1",
            "-q:v", "1",
            last_frame
        ]
        subprocess.run(cmd1, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 2. 获取视频时长
        video_duration = get_duration(video_path)
        extend_time = audio_duration - video_duration
        
        # 3. 创建延长部分
        extended = "extended.mp4"
        cmd2 = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", last_frame,
            "-t", str(extend_time),
            "-vf", "fps=30",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            extended
        ]
        subprocess.run(cmd2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 4. 拼接视频（先不带音频）
        concat_list = "concat.txt"
        with open(concat_list, "w") as f:
            f.write(f"file '{os.path.abspath(str(video_path))}'\n")
            f.write(f"file '{os.path.abspath(extended)}'\n")
        
        temp_video = "temp_video.mp4"
        cmd3 = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list,
            "-c", "copy",
            "-an",
            temp_video
        ]
        subprocess.run(cmd3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 5. 添加音频
        cmd4 = [
            "ffmpeg", "-y",
            "-i", temp_video,
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(output_path)
        ]
        result = subprocess.run(cmd4, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        
        # 清理
        for f in [last_frame, extended, concat_list, temp_video]:
            if os.path.exists(f):
                os.remove(f)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"  处理出错: {e}")
        # 清理
        for f in ["last_frame.jpg", "extended.mp4", "concat.txt", "temp_video.mp4"]:
            if os.path.exists(f):
                os.remove(f)
        return False

# 运行
if __name__ == "__main__":
    merge_video_audio("video", "voice")