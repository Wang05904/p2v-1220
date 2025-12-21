# 🎬 教学PPT转教学视频自动化工具
## 项目简介
本项目是一个基于AI的上传教学PPT生成教学视频的自动化工具，能够将PPTX格式的演示文稿自动转换为带有智能语音解说以及页面内部与切换动画的高质量教学视频。通过结合硅基流动AI的教学讲稿生成能力和讯飞星火的超拟人语音合成技术，实现从PPT到视频的一键式转换。

**核心功能:**

📊 智能解析PPT文本内容

🤖 AI自动生成解说脚本

🗣️ 高保真语音合成（超拟人声线）

🎥 自动生成视频动态画面

🎬 视频合成与片段切换动画

## 📁 项目目录结构
``` text
├── 📄 README.md                    # 项目说明文档
├── 📄 requirements.txt             # Python依赖包列表
├── 📄 .gitignore                   # Git忽略配置
├── 📄 .env.example                 # 环境变量模板
├── 📄 .env                         # 本地环境配置（不提交,需要自己新建并写入APIKEY等隐私参数）
├── 📄 config.py                    # 主配置文件
├── 📄 main.py                      # 主程序入口
├── 📄 ai_script_generator.py       # AI脚本生成器
├── 📄 ppt_parser.py                # PPT解析器
├── 📄 voice_synthesizer.py         # 语音合成器
├── 📄 video_generator.py           # 视频生成器
├── 📄 video_merger.py              # 视频合并器
├── 🔊 voice/                       # 生成的音频文件目录
├── 🎬 video/                       # 生成的视频文件目录
├── 📝 script/                      # 生成的脚本文件目录
├── 🗑️ temp/                        # 临时文件目录
```
## 🚀 项目启动
1. 第一步：**配置API密钥**
- 复制配置文件模板：

``` bash
cp .env.example .env
```
- 编辑.env文件，填入真实API密钥：
用文本编辑器打开 .env 文件，填入以下API密钥：

``` bash
# 硅基流动API（内容生成）
SILICONFLOW_API_KEY=your_actual_siliconflow_key_here

# 讯飞星火API（语音合成）
XUNFEI_APP_ID=your_actual_app_id_here
XUNFEI_API_KEY=your_actual_api_key_here
XUNFEI_API_SECRET=your_actual_api_secret_here
```
- 验证配置：

```bash
python config.py
```
如果看到所有配置项显示 ✅ 表示配置成功。

2. 第二步：安装依赖
```bash
pip install -r requirements.txt
```
3. 第三步：启动项目
- 基本用法：

```bash
python main.py test.pptx
```
- 高级用法：

```bash
# 转换当前目录下的PPT文件
python main.py my_presentation.pptx

# 使用绝对路径
python main.py /path/to/your/ppt/demo.pptx

# 转换文件夹下的所有PPT
python main.py ./ppt_folder/
```
## 📋 项目运行方法
1. 准备PPT文件：

2. 将你要转换的PPTX文件放入项目根目录，或记下其完整路径

3. 支持Microsoft PowerPoint 2007+格式（.pptx）

4. 运行转换：

```bash
# 如果PPT在项目根目录
python main.py your_presentation.pptx

# 如果PPT在其他目录
python main.py "/path/to/your/幻灯片.pptx"

# 批量转换文件夹
python main.py "./presentations/"
```
5. 查看结果：
```
音频文件：voice/ 目录

视频片段：video/ 目录

最终视频：项目根目录（如 final_video.mp4）
```
## 💡 小贴士
1. API服务官网链接：

- 硅基流动 🌊：https://cloud.siliconflow.cn/

- 用于AI内容生成和脚本创作

- 注册后可在控制台获取API密钥

2. 讯飞星火 ✨：https://console.xfyun.cn/app/myapp

- 用于超拟人语音合成（TTS）

- 需要创建应用并开通语音合成服务

3. 使用建议：

- 首次使用：先用 test.pptx 测试完整流程

- API配额：注意两个平台的API调用限制和费用

- 网络要求：确保稳定的网络连接，特别是语音合成时

- 文件命名：避免使用中文或特殊字符的路径

- 内存空间：确保有足够的磁盘空间存放生成的音频和视频文件

4. 故障排查：
- 如果遇到API错误，先运行 python config.py 验证配置

- 检查 .env 文件中的密钥是否正确

- 确认Python版本为3.8+

- 确保已安装所有依赖包

5. 📞 技术支持
遇到问题时：

- 检查控制台错误信息

- 确认API密钥有效且未过期

- 确保PPT文件格式正确

- 查看生成的日志文件

开始你的PPT转视频之旅吧！只需一个PPT文件，几分钟内即可获得专业级的教学视频 🎉