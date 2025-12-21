# -*- coding:utf-8 -*-

import websocket
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import os
import glob
import time
from config import XUNFEI_APP_ID, XUNFEI_API_KEY, XUNFEI_API_SECRET, SCRIPT_DIR, VOICE_DIR

class AssembleHeaderException(Exception):
    def __init__(self, msg):
        self.message = msg

class Url:
    def __init__(self, host, path, schema):
        self.host = host
        self.path = path
        self.schema = schema

def parse_url(request_url):
    stidx = request_url.index("://")
    host = request_url[stidx + 3:]
    schema = request_url[:stidx + 3]
    edidx = host.index("/")
    if edidx <= 0:
        raise AssembleHeaderException("invalid request url:" + request_url)
    path = host[edidx:]
    host = host[:edidx]
    return Url(host, path, schema)

def assemble_ws_auth_url(request_url, method="GET", api_key="", api_secret=""):
    """生成带鉴权的WebSocket URL"""
    u = parse_url(request_url)
    host = u.host
    path = u.path
    
    now = datetime.now()
    date = format_date_time(mktime(now.timetuple()))
    
    signature_origin = f"host: {host}\ndate: {date}\n{method} {path} HTTP/1.1"
    signature_sha = hmac.new(
        api_secret.encode('utf-8'), 
        signature_origin.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
    
    authorization_origin = (
        f'api_key="{api_key}", algorithm="hmac-sha256", '
        f'headers="host date request-line", signature="{signature_sha}"'
    )
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
    
    values = {
        "host": host,
        "date": date,
        "authorization": authorization
    }
    
    return request_url + "?" + urlencode(values)

class XunfeiTTSSynthesizer:
    """讯飞TTS合成器"""
    
    def __init__(self, app_id, api_key, api_secret, output_dir):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.output_dir = output_dir
        self.ws_url = 'wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6'
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
    
    def _prepare_request_data(self, text, voice="x5_lingyuyan_flow"):
        """准备请求数据"""
        common_args = {"app_id": self.app_id, "status": 2}
        
        business_args = {
            "tts": {
                "vcn": voice,
                "volume": 50,
                "rhy": 0,
                "speed": 50,
                "pitch": 50,
                "bgs": 0,
                "reg": 0,
                "rdn": 0,
                "audio": {
                    "encoding": "lame",
                    "sample_rate": 24000,
                    "channels": 1,
                    "bit_depth": 16,
                    "frame_size": 0
                }
            }
        }
        
        data = {
            "text": {
                "encoding": "utf8",
                "compress": "raw",
                "format": "plain",
                "status": 2,
                "seq": 0,
                "text": str(base64.b64encode(text.encode('utf-8')), "UTF8")
            }
        }
        
        return common_args, business_args, data
    
    def _on_message(self, ws, message, audio_data, is_success):
        """WebSocket消息回调"""
        try:
            message = json.loads(message)
            code = message["header"]["code"]
            
            if "payload" in message and "audio" in message["payload"]:
                audio_base64 = message["payload"]["audio"]["audio"]
                audio_chunk = base64.b64decode(audio_base64)
                audio_data.append(audio_chunk)
                
                status = message["payload"]["audio"]["status"]
                if status == 2:
                    ws.close()
            
            if code != 0:
                print(f"错误代码: {code}, 消息: {message.get('header', {}).get('message', '未知错误')}")
                is_success[0] = False
            else:
                is_success[0] = True
                
        except Exception as e:
            print(f"解析消息异常: {e}")
            is_success[0] = False
    
    def _on_error(self, ws, error):
        """WebSocket错误回调"""
        print(f"WebSocket错误: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """WebSocket关闭回调"""
        pass
    
    def _on_open(self, ws, request_data):
        """WebSocket打开回调"""
        def run():
            ws.send(request_data)
        thread.start_new_thread(run, ())
    
    def synthesize_text(self, text, output_filename, voice="x5_lingyuyan_flow"):
        """合成单段文本"""
        # 准备数据
        common_args, business_args, data = self._prepare_request_data(text, voice)
        request_data = json.dumps({
            "header": common_args,
            "parameter": business_args,
            "payload": data
        })
        
        # 生成鉴权URL
        auth_url = assemble_ws_auth_url(
            self.ws_url, "GET", self.api_key, self.api_secret
        )
        
        # 初始化状态变量
        audio_data = []
        is_success = [False]
        
        # 创建WebSocket连接
        ws = websocket.WebSocketApp(
            auth_url,
            on_message=lambda ws, msg: self._on_message(ws, msg, audio_data, is_success),
            on_error=self._on_error,
            on_close=self._on_close
        )
        ws.on_open = lambda ws: self._on_open(ws, request_data)
        
        # 运行WebSocket
        websocket.enableTrace(False)
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        # 保存音频文件
        if audio_data and is_success[0]:
            output_path = os.path.join(self.output_dir, output_filename)
            with open(output_path, 'wb') as f:
                for chunk in audio_data:
                    f.write(chunk)
            print(f"音频文件已保存: {output_path}")
            return True
        else:
            print(f"合成失败: {output_filename}")
            return False
def synthesize_voices(voice="x5_lingyuyan_flow"):
    """
    合成SCRIPT_DIR目录下所有txt文件的语音
    
    Args:
        voice: 发音人，默认使用"x5_lingyuyan_flow"
    
    Returns:
        bool: 是否全部合成成功
    """
    try:
        # 初始化合成器
        synthesizer = XunfeiTTSSynthesizer(
            app_id=XUNFEI_APP_ID,
            api_key=XUNFEI_API_KEY,
            api_secret=XUNFEI_API_SECRET,
            output_dir=VOICE_DIR
        )
        
        # 确保脚本目录存在
        if not os.path.exists(SCRIPT_DIR):
            print(f"错误: 脚本目录不存在 - {SCRIPT_DIR}")
            return False
        
        # 查找所有txt文件
        txt_files = sorted(
            glob.glob(os.path.join(SCRIPT_DIR, "page_*.txt")),
            key=lambda x: int(os.path.basename(x).split('_')[1].split('.')[0])
        )
        
        if not txt_files:
            print(f"警告: 在 {SCRIPT_DIR} 目录下未找到 page_*.txt 文件")
            return False
        
        print(f"找到 {len(txt_files)} 个文本文件")
        
        # 依次处理每个文件
        all_success = True
        
        for txt_file in txt_files:
            # 读取文件内容
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    text_content = f.read().strip()
            except Exception as e:
                print(f"读取文件失败 {txt_file}: {e}")
                all_success = False
                continue
            
            if not text_content:
                print(f"警告: {txt_file} 内容为空，跳过")
                continue
            
            # 生成输出文件名
            base_name = os.path.basename(txt_file).replace('.txt', '.mp3')
            print(f"正在合成: {base_name} (长度: {len(text_content)} 字符)")
            
            # 合成语音
            success = synthesizer.synthesize_text(
                text=text_content,
                output_filename=base_name,
                voice=voice
            )
            
            if not success:
                all_success = False
                print(f"合成失败: {base_name}")
            else:
                print(f"合成成功: {base_name}")
            
            # 为避免API限制，添加短暂延迟
            import time
            time.sleep(1)
        
        return all_success
        
    except Exception as e:
        print(f"合成过程中发生异常: {e}")
        return False