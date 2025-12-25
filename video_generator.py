import os
import json
import subprocess
from pathlib import Path
from PIL import Image

def create_video_for_slide(slide_data, bg_image_path, output_video_path, fps=30):
    """
    为单张幻灯片生成动画视频。
    新增参数控制：
        element_duration: 每个元素出现后停留的秒数（默认1秒30帧）
    """
    slide_num = slide_data.get("slide_number", "1")
    elements = slide_data.get("animated_elements", [])
    
    if not elements:
        print(f"  ⚠️  幻灯片 {slide_num} 无图片元素，跳过。")
        return

    # ============================================
    # 🎯 关键参数：控制元素出现间隔
    # ============================================
    element_duration = 18 # 每个元素停留几帧
    # 或者使用固定总时长方案：
    # total_video_duration = 10  # 视频总长10秒
    # element_duration = (total_video_duration - 1) / len(elements) if elements else 0
    
    print(f"  🎬 开始处理幻灯片 {slide_num}...")
    print(f"     背景图：{bg_image_path}")
    print(f"     元素数：{len(elements)} 个")
    print(f"     元素停留时间：{element_duration} 秒/个")
    
    # 计算总时长
    # 总时长 = 1秒（初始纯背景） + (元素数量 × 每个元素停留时间)
    total_seconds = 1 + (len(elements) * element_duration)
    print(f"     视频总时长：{total_seconds} 秒")

    # 创建临时目录存放每一秒的合成帧
    temp_frame_dir = Path(f"temp_frames_slide_{slide_num}")
    temp_frame_dir.mkdir(exist_ok=True)

    try:
        # 步骤1：打开并准备背景图
        try:
            bg_img = Image.open(bg_image_path).convert("RGBA")
            bg_width, bg_height = bg_img.size
            print(f"     背景图尺寸：{bg_width} x {bg_height}")
        except Exception as e:
            print(f"  ❌ 无法打开背景图片 {bg_image_path}: {e}")
            return

        # 步骤2：预加载所有元素图片
        element_images = []
        for elem in elements:
            img_path = elem.get("image_path")
            if not img_path or not Path(img_path).exists():
                print(f"  ⚠️  元素图片不存在: {img_path}，将跳过。")
                element_images.append(None)
                continue
            try:
                elem_img = Image.open(img_path).convert("RGBA")
                element_images.append(elem_img)
            except Exception as e:
                print(f"  ⚠️  无法打开元素图片 {img_path}: {e}")
                element_images.append(None)

        # 步骤3：生成每一秒的静态画面（帧）
        # 重要修改：现在秒数对应的是视频时间，而不是元素索引
        current_second = 0
        frame_index = 0
        
        # 第0秒：只显示背景（没有元素）
        print(f"     生成第 {current_second} 秒画面（仅背景）...")
        current_frame = bg_img.copy()
        frame_path = temp_frame_dir / f"frame_{frame_index:03d}.png"
        current_frame.convert("RGB").save(frame_path, "PNG")
        current_second += 1
        frame_index += 1
        
        # 对于每个元素，生成 element_duration 秒的画面
        for elem_index in range(len(elements)):
            print(f"     处理元素 {elem_index+1}（第{current_second/30}秒开始）...")
            
            # 为当前元素的每一秒生成画面
            for duration_step in range(int(element_duration)):
                # 创建当前背景副本
                current_frame = bg_img.copy()
                
                # 粘贴所有已经出现的元素（包括当前元素）
                for i in range(elem_index + 1):  # +1 表示包含当前元素
                    if i >= len(elements):
                        break
                    elem_img = element_images[i]
                    if elem_img is None:
                        continue
                    
                    elem_data = elements[i]
                    pos = elem_data.get("position", {})
                    
                    # 坐标缩放计算（与之前相同）
                    elem_x_px = pos.get("x_px", 0)
                    elem_y_px = pos.get("y_px", 0)
                    elem_width_px = pos.get("width_px", 100)
                    elem_height_px = pos.get("height_px", 100)
                    
                    scale_x = bg_width / 1280.0
                    scale_y = bg_height / 720.0
                    
                    target_x = int(elem_x_px * scale_x)
                    target_y = int(elem_y_px * scale_y)
                    target_width = int(elem_width_px * scale_x)
                    target_height = int(elem_height_px * scale_y)
                    
                    # 确保尺寸为偶数
                    if target_width % 2 != 0:
                        target_width += 1
                    if target_height % 2 != 0:
                        target_height += 1
                    
                    resized_elem_img = elem_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                    current_frame.paste(resized_elem_img, (target_x, target_y), resized_elem_img)
                
                # 保存当前合成帧
                frame_path = temp_frame_dir / f"frame_{frame_index:03d}.png"
                current_frame.convert("RGB").save(frame_path, "PNG")
                frame_index += 1
            
            current_second += element_duration

        print(f"     所有画面生成完毕（共{frame_index}帧），开始合成视频...")

        # 步骤4：使用FFmpeg将所有静态帧合成为视频
        # 注意：现在每帧播放时间不再是固定的1秒，需要调整FFmpeg参数
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),  # 输入帧率
            "-i", str(temp_frame_dir / "frame_%03d.png"),  # 输入图像序列
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            # 关键修改：使用-r指定输出帧率，而不是用-vf fps
            "-r", str(fps),
            output_video_path
        ]
        
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            print(f"  ✅ 幻灯片 {slide_num} 视频生成成功: {output_video_path}")
            print(f"     视频时长：{total_seconds/30} 秒，帧率：{fps} fps")
        else:
            print(f"  ❌ 幻灯片 {slide_num} 视频合成失败:")
            print(f"     错误信息: {result.stderr[:200]}")

    except Exception as e:
        print(f"  ❌ 处理幻灯片 {slide_num} 时发生未知错误: {e}")
    finally:
        # 步骤5：清理临时帧文件
        if temp_frame_dir.exists():
            for frame_file in temp_frame_dir.glob("*.png"):
                frame_file.unlink()
            temp_frame_dir.rmdir()

def generate_all_ppt_videos(json_file_path="extract_pic.json", bg_img_dir="img", output_video_dir="temp/video", fps=30):
    """
    主函数：读取JSON，为每张幻灯片生成视频。
    新增可选参数：
        element_duration: 可从此函数传入（如果需要在外部统一控制）
    """
    print("=" * 60)
    print("PPT图片动画视频生成器 (调整元素间隔版)")
    print("=" * 60)

    if not Path(json_file_path).exists():
        print(f"❌ 找不到JSON文件: {json_file_path}")
        return
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 读取JSON文件失败: {e}")
        return

    slides = data.get("slides", [])
    if not slides:
        print("⚠️  JSON文件中未找到幻灯片数据。")
        return

    output_path = Path(output_video_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"📊 共发现 {len(slides)} 张幻灯片待处理。")
    print("-" * 60)

    for slide in slides:
        slide_num = slide.get("slide_number")
        bg_image_path = Path(bg_img_dir) / f"page_{slide_num}.png"
        
        if not bg_image_path.exists():
            print(f"❌ 幻灯片 {slide_num} 的背景图不存在: {bg_image_path}")
            continue
        
        output_video_path = output_path / f"page_{slide_num}.mp4"
        
        # 可以在这里统一设置所有幻灯片的元素间隔
        # 例如，如果想所有幻灯片都使用3秒间隔，可以在这里设置
        create_video_for_slide(slide, str(bg_image_path), str(output_video_path), fps)
        print("-" * 40)

    print("=" * 60)
    print("✅ 所有幻灯片处理完成！")
    print(f"   视频文件保存在: {output_video_dir}")
    print("=" * 60)
    return True

if __name__ == "__main__":
    # 配置参数
    JSON_FILE = "extract_pic.json"
    BACKGROUND_IMG_DIR = "./img"
    OUTPUT_VIDEO_DIR = "./temp/video"
    FPS = 30
    
    # 运行主程序
    generate_all_ppt_videos(JSON_FILE, BACKGROUND_IMG_DIR, OUTPUT_VIDEO_DIR, FPS)