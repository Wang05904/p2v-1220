# PPT解析模块
"""
PPT解析模块 - 提取PPT文本内容并生成格式化的文本
使用Spire.Presentation库[citation:1]
"""

import os
from spire.presentation import *
from spire.presentation.common import *
import xml.etree.ElementTree as ET
import win32com.client
import pythoncom
from config import IMG_DIR

def extract_text_from_shape(shape, text_list):
    """递归提取形状中的文本"""
    # 检查是否为组合形状
    if isinstance(shape, GroupShape):
        # 遍历组合中的子形状
        for sub_shape in shape.Shapes:
            extract_text_from_shape(sub_shape, text_list)
    # 检查是否为可包含文本的形状
    elif isinstance(shape, IAutoShape):
        # 提取文本
        if shape.TextFrame is not None:
            for paragraph in shape.TextFrame.Paragraphs:
                if paragraph.Text and paragraph.Text.strip():
                    text_list.append(paragraph.Text)
    # 检查是否为表格
    elif isinstance(shape, ITable):
        # 遍历表格单元格
        for row in range(shape.TableRows.Count):
            for col in range(shape.ColumnsList.Count):
                cell = shape.TableRows[row][col]
                if cell.TextFrame is not None:
                    for paragraph in cell.TextFrame.Paragraphs:
                        if paragraph.Text and paragraph.Text.strip():
                            text_list.append(paragraph.Text)

def extract_slide_text(slide):
    """提取单张幻灯片中的所有文本"""
    slide_text = []
    # 遍历幻灯片中的所有形状
    for shape in slide.Shapes:
        extract_text_from_shape(shape, slide_text)
    return slide_text

def extract_ppt_text(ppt_path, output_xml_dir="temp"):
    """
    从PPT中提取所有文本内容并保存为每页ppt为图片
    
    参数:
        ppt_path: PPT文件路径
        output_xml_dir: 保存XML文件的目录
    
    返回:
        formatted_text: 格式化的文本 "第n页：文字内容"
    """
    # 创建输出目录
    os.makedirs(output_xml_dir, exist_ok=True)
    
    # 加载PPT文件[citation:1]
    presentation = Presentation()
    presentation.LoadFromFile(ppt_path)
    
    formatted_text_parts = []
    
    # 遍历所有幻灯片
    for slide_index, slide in enumerate(presentation.Slides):
        slide_text_parts=[]
        # 添加幻灯片标记
        slide_header = f"====幻灯片 {slide_index + 1}===="
        slide_text = extract_slide_text(slide)
        
        if slide_text:  # 只添加有文本的幻灯片
            slide_text_parts.extend(slide_text)
        
        # 合并当前幻灯片的所有文本
        slide_text = " ".join(slide_text_parts)
        if slide_text:
            formatted_text_parts.append(f"第{slide_index + 1}页：{slide_text}")
        
        # 保存当前幻灯片的XML表示（简化版）
        # save_slide_xml(slide, slide_index, output_xml_dir)
    
    # 释放资源[citation:1]
    presentation.Dispose()
    
    # 返回格式化的文本
    return "\n".join(formatted_text_parts)

def pptx_to_images(pptx_path, dpi=96):
    """
    Windows系统下使用PowerPoint原生引擎转换PPTX到图片
    图片自动保存到项目根目录的img文件夹下
    """
    # 初始化COM环境
    pythoncom.CoInitialize()
    output_dir = IMG_DIR
    # 确保img文件夹存在（不存在则创建）
    os.makedirs(output_dir, exist_ok=True)
    
    # 检查输入PPT文件（转换为绝对路径）
    pptx_path = os.path.abspath(pptx_path)
    if not os.path.exists(pptx_path):
        print(f"❌ 错误：输入文件 {pptx_path} 不存在！")
        pythoncom.CoUninitialize()
        return
    
    powerpoint = None
    presentation = None
    
    try:
        # 初始化PowerPoint应用
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        
        # 打开演示文稿
        presentation = powerpoint.Presentations.Open(
            FileName=pptx_path,
            ReadOnly=True,
            WithWindow=True
        )
        
        slide_count = presentation.Slides.Count
        print(f"开始转换：共 {slide_count} 页幻灯片")
        print(f"图片将保存到：{output_dir}")
        
        # 逐页导出（使用img文件夹的绝对路径）
        for i in range(1, slide_count + 1):
            slide = presentation.Slides(i)
            # 生成img文件夹下的绝对路径（确保反斜杠）
            output_path = os.path.join(output_dir, f"page_{i}.png").replace("/", "\\")
            
            # 计算幻灯片宽度（按DPI）
            slide_width_inch = presentation.PageSetup.SlideWidth / 914400
            slide_width_px = int(slide_width_inch * dpi)
            
            # 导出图片到img文件夹
            slide.Export(output_path, "PNG", slide_width_px, 0)
            print(f"✅ 已导出第{i}页：{output_path}")
    
    except Exception as e:
        print(f"❌ 转换失败：{str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        if presentation:
            presentation.Close()
        if powerpoint:
            powerpoint.Quit()
            del powerpoint
        pythoncom.CoUninitialize()

# def save_slide_xml(slide, slide_index, output_dir):
    """
    保存幻灯片的XML表示（简化版）
    实际项目中需要根据PPT结构创建更详细的XML
    """
    xml_file = os.path.join(output_dir, f"slide_{slide_index + 1}.xml")
    
    # 创建XML结构
    root = ET.Element("slide")
    root.set("number", str(slide_index + 1))
    
    # 添加文本元素
    for shape_index, shape in enumerate(slide.Shapes):
        if isinstance(shape, IAutoShape):
            shape_elem = ET.SubElement(root, "shape")
            shape_elem.set("id", str(shape_index))
            shape_elem.set("type", "text")
            
            for para_index, paragraph in enumerate(shape.TextFrame.Paragraphs):
                text_elem = ET.SubElement(shape_elem, "text")
                text_elem.set("para", str(para_index))
                text_elem.text = paragraph.Text
    
    # 写入文件
    tree = ET.ElementTree(root)
    tree.write(xml_file, encoding="utf-8", xml_declaration=True)
    
    return xml_file