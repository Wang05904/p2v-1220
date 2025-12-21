# AI讲稿生成模块
"""
AI讲稿生成模块 - 调用硅基流动API生成每页讲稿
参考硅基流动API调用方法[citation:3]
"""

import requests
import json
import os
from config import SILICONFLOW_API_KEY, SILICONFLOW_API_URL, SCRIPT_DIR

def generate_ai_script(ppt_text):
    """
    调用AI生成每页PPT的讲稿
    
    参数:
        ppt_text: 格式化的PPT文本
    
    返回:
        bool: 是否成功生成讲稿
    """
    
    # 构建提示词 - 包含角色定义、任务描述、约束条件和格式要求[citation:9]
    prompt = f"""
    你是一位资深的专业老师，需要根据以下PPT内容为每一页撰写简短的课堂讲稿。
    
    PPT内容：
    {ppt_text}
    
    要求：
    1. 为每一页PPT撰写不超过50字的讲稿
    2. 讲稿要自然流畅，适合口头表达，语言要幽默诙谐，深入浅出
    3. 严格按照以下格式返回：
    
    第1页：[这里写第1页的讲稿内容]
    第2页：[这里写第2页的讲稿内容]
    ...
    
    注意：只返回上述格式的内容，不要添加任何额外说明。
    """
    
    # 准备API请求数据[citation:3]
    headers = {
        "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "Qwen/QwQ-32B",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    try:
        # 调用硅基流动API[citation:3]
        response = requests.post(SILICONFLOW_API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        ai_response = response.json()
        script_content = ai_response["choices"][0]["message"]["content"]
        
        # 验证返回格式并提取讲稿
        if not validate_and_extract_script(script_content):
            print("错误：AI返回的格式不符合要求")
            return False
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"API调用失败: {e}")
        return False
    except (KeyError, IndexError) as e:
        print(f"解析AI响应失败: {e}")
        return False

def validate_and_extract_script(ai_response):
    """
    验证AI返回的格式并提取每页讲稿保存为单独文件
    
    参数:
        ai_response: AI返回的文本
    
    返回:
        bool: 格式是否有效
    """
    # 创建脚本目录
    os.makedirs(SCRIPT_DIR, exist_ok=True)
    
    lines = ai_response.strip().split('\n')
    page_scripts = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith('第') and '页：' in line:
            try:
                # 提取页码和讲稿内容
                page_part, script_part = line.split('：', 1)
                page_num = int(page_part.replace('第', '').replace('页', ''))
                
                # 检查字数限制
                if len(script_part) > 50:
                    print(f"警告：第{page_num}页讲稿超过50字")
                    # script_part = script_part[:50]  # 截断超长部分
                
                page_scripts[page_num] = script_part
            except (ValueError, IndexError):
                print(f"格式错误的行: {line}")
                return False
    
    if not page_scripts:
        print("错误：未找到有效的讲稿内容")
        return False
    
    # 保存每页讲稿为单独文件
    for page_num, script in page_scripts.items():
        script_file = os.path.join(SCRIPT_DIR, f"page_{page_num}.txt")
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script)
        print(f"已保存第{page_num}页讲稿: {script[:30]}...")
    
    return True