import os
import json
import zipfile
from lxml import etree

def extract_only_images(pptx_path, output_json):
    """
    仅提取 PPT 中的图片元素，过滤掉文本框、形状等
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

    with zipfile.ZipFile(pptx_path, 'r') as z:
        # 获取所有幻灯片 XML
        slide_files = sorted([f for f in z.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')])
        
        for slide_file in slide_files:
            slide_num = "".join(filter(str.isdigit, slide_file.split('/')[-1]))
            slide_info = {"slide_number": slide_num, "animated_elements": []}
            
            with z.open(slide_file) as f:
                tree = etree.fromstring(f.read())
                
                # --- 关键点：只选取 p:pic 标签 ---
                # 这会自动过滤掉 p:sp (文本框/形状)
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
                    
                    slide_info["animated_elements"].append({
                        "id": pic_id,
                        "type": "picture",
                        "name": pic_name,
                        "rId": rid  # 记录这个可以确保它是真正的图片
                    })
            
            if slide_info["animated_elements"]:
                slides_data.append(slide_info)

    # 写入 JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({"slides": slides_data}, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 提取完成！已过滤非图片元素。生成的 JSON 位于: {output_json}")

if __name__ == "__main__":
    extract_only_images("test.pptx", "extract_pic_example.json")