"""
官方智能体模块

本模块包含11个官方智能体的封装实现：
1. 聊天助手 - 通用对话
2. 翻译专家 - 多语言翻译
3. 语音识别助手 - 语音转文本
4. 知识库搜索 - 知识库检索
5. Web搜索助手 - 网络搜索
6. 图片生成器 - AI生成图片
7. 图像识别专家 - 图片内容识别
8. 视频生成器 - AI生成视频
9. 视频分析专家 - 视频内容分析
10. 文字转语音 - TTS
11. 语音转文字 - STT
"""

from app.agents.official.chat_agent import ChatAgent
from app.agents.official.translate_agent import TranslateAgent
from app.agents.official.speech_recognition_agent import SpeechRecognitionAgent
from app.agents.official.knowledge_search_agent import KnowledgeSearchAgent
from app.agents.official.web_search_agent import WebSearchAgent
from app.agents.official.image_generation_agent import ImageGenerationAgent
from app.agents.official.image_recognition_agent import ImageRecognitionAgent
from app.agents.official.video_generation_agent import VideoGenerationAgent
from app.agents.official.video_analysis_agent import VideoAnalysisAgent
from app.agents.official.tts_agent import TTSAgent
from app.agents.official.stt_agent import STTAgent

__all__ = [
    'ChatAgent',
    'TranslateAgent',
    'SpeechRecognitionAgent',
    'KnowledgeSearchAgent',
    'WebSearchAgent',
    'ImageGenerationAgent',
    'ImageRecognitionAgent',
    'VideoGenerationAgent',
    'VideoAnalysisAgent',
    'TTSAgent',
    'STTAgent',
]

# 所有官方智能体的列表
OFFICIAL_AGENTS = [
    ChatAgent,
    TranslateAgent,
    SpeechRecognitionAgent,
    KnowledgeSearchAgent,
    WebSearchAgent,
    ImageGenerationAgent,
    ImageRecognitionAgent,
    VideoGenerationAgent,
    VideoAnalysisAgent,
    TTSAgent,
    STTAgent,
]
