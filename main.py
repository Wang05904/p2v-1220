# 主程序入口
"""
主程序入口 - 协调所有模块执行PPT转视频流程
"""

import sys
import os
from ppt_parser import extract_ppt_text,pptx_to_images
from ai_script_generator import generate_ai_script
from voice_synthesizer import synthesize_voices
from video_generator import generate_page_videos
from video_merger import merge_videos

def main():
    """主函数"""
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法: python main.py <ppt文件路径>")
        print("示例: python main.py presentation.pptx")
        sys.exit(1)
    
    ppt_path = sys.argv[1]
    
    if not os.path.exists(ppt_path):
        print(f"错误：文件不存在 {ppt_path}")
        sys.exit(1)
    
    print("=" * 50)
    print("开始PPT转视频处理")
    print("=" * 50)
    
    # # 步骤1: 解析PPT
    # print("\n[步骤1] 解析PPT文件...")
    # try:
    #     ppt_text = extract_ppt_text(ppt_path)
    #     print("ppt_text\n",ppt_text)
    #     pptx_to_images(ppt_path)
    #     print("PPT解析为图片完成")
    # except Exception as e:
    #     print(f"PPT解析失败: {e}")
    #     sys.exit(1)
    
    # # 步骤2: AI生成讲稿
    # print("\n[步骤2] AI生成讲稿...")
    # if not generate_ai_script(ppt_text):
    #     print("AI讲稿生成失败")
    #     sys.exit(1)
    
    # # 步骤3: 语音合成
    # print("\n[步骤3] 语音合成...")
    # if not synthesize_voices():
    #     print("语音合成失败")
    #     sys.exit(1)
    
    # # 步骤4: 生成单页视频
    # print("\n[步骤4] 生成单页视频...")
    # if not generate_page_videos():
    #     print("单页视频生成失败")
    #     sys.exit(1)
    
    # 步骤5: 合并视频
    print("\n[步骤5] 合并视频...")
    success, final_video = merge_videos()
    
    if success:
        print("\n" + "=" * 50)
        print(f"处理完成！最终视频已保存为: {final_video}")
        print("=" * 50)
    else:
        print("\n视频合并失败")
        sys.exit(1)

if __name__ == "__main__":
    main()