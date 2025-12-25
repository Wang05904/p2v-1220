import os
import json
import zipfile
import shutil
from lxml import etree
from pathlib import Path

def extract_only_images(pptx_path, output_json):
    """
    仅提取 PPT 中的图片元素，过滤掉文本框、形状等，提取坐标宽高，下载并保存图片
    """
    slides_data = []
    # PPT 的 XML 命名空间
    ns = {
        'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    }

    if not os.path.exists(pptx_path):
        print(f"❌ 找不到文件: {pptx_path}")
        return

    # 创建图片保存目录
    temp_img_dir = "temp/img"
    Path(temp_img_dir).mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(pptx_path, 'r') as z:
        # 获取所有幻灯片 XML
        slide_files = sorted([f for f in z.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')])
        
        # 获取幻灯片尺寸（用于计算百分比）
        slide_width = 12192000  # 默认值 (EMU单位)
        slide_height = 6858000  # 默认值 (EMU单位)
        
        try:
            # 尝试从 presentation.xml 读取幻灯片尺寸
            if 'ppt/presentation.xml' in z.namelist():
                with z.open('ppt/presentation.xml') as f:
                    presentation_tree = etree.fromstring(f.read())
                    sldSz = presentation_tree.xpath('.//p:sldSz', namespaces=ns)
                    if sldSz:
                        slide_width = int(sldSz[0].get('cx', slide_width))
                        slide_height = int(sldSz[0].get('cy', slide_height))
        except:
            pass
        
        # EMU 转换为像素的转换因子
        emu_to_px = 914400 / 96
        
        for slide_file in slide_files:
            slide_num = "".join(filter(str.isdigit, slide_file.split('/')[-1]))
            slide_info = {"slide_number": slide_num, "animated_elements": []}
            
            # 修复：关系文件在 ppt/slides/_rels/ 目录下
            # 例如: ppt/slides/slide1.xml → ppt/slides/_rels/slide1.xml.rels
            slide_filename = os.path.basename(slide_file)
            slide_rel_file = f"ppt/slides/_rels/{slide_filename}.rels"
            
            # 读取关系映射
            rels_dict = {}
            if slide_rel_file in z.namelist():
                with z.open(slide_rel_file) as f:
                    rels_tree = etree.fromstring(f.read())
                    # 使用正确的命名空间查找Relationship元素
                    relationships = rels_tree.xpath('.//*[local-name()="Relationship"]')
                    for rel in relationships:
                        rid = rel.get('Id')
                        target = rel.get('Target')
                        if rid and target:
                            # 处理相对路径：关系文件在 _rels 目录，所以需要向上退一级
                            if target.startswith('../'):
                                # 例如: ../media/image1.png → ppt/media/image1.png
                                target = 'ppt/' + target[3:]
                            rels_dict[rid] = target
            
            with z.open(slide_file) as f:
                tree = etree.fromstring(f.read())
                
                # 只选取 p:pic 标签
                pics = tree.xpath('.//p:pic', namespaces=ns)
                
                for pic in pics:
                    # 获取 ID 和 名称
                    cnvpr = pic.xpath('.//p:cNvPr', namespaces=ns)[0]
                    pic_id = cnvpr.get('id')
                    pic_name = cnvpr.get('name') # 通常包含 "Picture" 或 "图片" 字样
                    
                    # 进一步验证：检查是否有图片填充 (blip)
                    blip = pic.xpath('.//a:blip', namespaces=ns)
                    if not blip:
                        continue # 如果没有关联图片资源，跳过
                    
                    # 获取图片的关系 ID (rId)
                    rid = blip[0].get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                    
                    # 提取位置和尺寸信息
                    xfrm = pic.xpath('.//a:xfrm', namespaces=ns)
                    if xfrm:
                        xfrm = xfrm[0]
                        off = xfrm.xpath('.//a:off', namespaces=ns)
                        ext = xfrm.xpath('.//a:ext', namespaces=ns)
                        
                        if off and ext:
                            x = int(off[0].get('x', 0))
                            y = int(off[0].get('y', 0))
                            width = int(ext[0].get('cx', 0))
                            height = int(ext[0].get('cy', 0))
                            
                            # 转换为像素
                            x_px = int(x / emu_to_px)
                            y_px = int(y / emu_to_px)
                            width_px = int(width / emu_to_px)
                            height_px = int(height / emu_to_px)
                            
                            # 计算百分比位置（相对于幻灯片）
                            x_percent = round((x / slide_width) * 100, 2)
                            y_percent = round((y / slide_height) * 100, 2)
                            width_percent = round((width / slide_width) * 100, 2)
                            height_percent = round((height / slide_height) * 100, 2)
                        else:
                            x = y = width = height = 0
                            x_px = y_px = width_px = height_px = 0
                            x_percent = y_percent = width_percent = height_percent = 0
                    else:
                        x = y = width = height = 0
                        x_px = y_px = width_px = height_px = 0
                        x_percent = y_percent = width_percent = height_percent = 0
                    
                    # 获取图片路径并保存
                    image_path = None
                    image_target = None
                    
                    if rid and rid in rels_dict:
                        # 获取图片在PPT中的路径
                        image_target = rels_dict[rid]
                        
                        if image_target in z.namelist():
                            # 提取图片文件扩展名
                            ext = os.path.splitext(image_target)[1].lower()
                            if not ext:
                                # 尝试从文件内容判断类型
                                with z.open(image_target) as img_file:
                                    header = img_file.read(8)
                                    if header.startswith(b'\x89PNG\r\n\x1a\n'):
                                        ext = '.png'
                                    elif header.startswith(b'\xff\xd8'):
                                        ext = '.jpg'
                                    elif header.startswith(b'GIF8'):
                                        ext = '.gif'
                                    elif header.startswith(b'BM'):
                                        ext = '.bmp'
                                    else:
                                        ext = '.bin'
                            
                            # 生成唯一文件名并保存
                            image_filename = f"slide{slide_num}_pic{pic_id}{ext}"
                            image_save_path = os.path.join(temp_img_dir, image_filename)
                            
                            try:
                                # 从ZIP包中提取图片
                                with z.open(image_target) as img_file:
                                    with open(image_save_path, 'wb') as out_file:
                                        shutil.copyfileobj(img_file, out_file)
                                
                                # 使用相对路径
                                image_path = f"temp/img/{image_filename}"
                            except Exception as e:
                                print(f"❌ 保存图片失败: {e}")
                    
                    element_info = {
                        "id": pic_id,
                        "type": "picture",
                        "name": pic_name,
                        "rId": rid,
                        "url": image_target,
                        "position": {
                            "x": x,  # EMU单位
                            "y": y,  # EMU单位
                            "width": width,  # EMU单位
                            "height": height,  # EMU单位
                            "x_px": x_px,  # 像素单位
                            "y_px": y_px,  # 像素单位
                            "width_px": width_px,  # 像素单位
                            "height_px": height_px,  # 像素单位
                            "x_percent": x_percent,  # 相对于幻灯片宽度的百分比
                            "y_percent": y_percent,  # 相对于幻灯片高度的百分比
                            "width_percent": width_percent,  # 相对于幻灯片宽度的百分比
                            "height_percent": height_percent  # 相对于幻灯片高度的百分比
                        },
                        "image_path": image_path  # 图片保存的本地路径
                    }
                    
                    slide_info["animated_elements"].append(element_info)
            
            if slide_info["animated_elements"]:
                slides_data.append(slide_info)

    # 写入 JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({
            "slides": slides_data,
            "slide_dimensions": {
                "width_emu": slide_width,
                "height_emu": slide_height,
                "width_px": int(slide_width / emu_to_px),
                "height_px": int(slide_height / emu_to_px)
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 提取完成！")
    print(f"   - 生成的 JSON 位于: {output_json}")
    print(f"   - 图片保存到: {temp_img_dir}")
    print(f"   - 共处理 {len(slides_data)} 张幻灯片")
    print(f"   - 共提取 {sum(len(slide['animated_elements']) for slide in slides_data)} 张图片")

if __name__ == "__main__":
    extract_only_images("test.pptx", "extract_pic.json")