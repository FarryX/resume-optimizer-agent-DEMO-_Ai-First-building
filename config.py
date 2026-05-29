# config.py - 禁用RAG的配置
import os
from dotenv import load_dotenv

load_dotenv()

class DeepSeekConfig:
    """DeepSeek API配置"""
    
    API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-api-key-here")
    API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    MODEL_NAME = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))
    TOP_P = float(os.getenv("TOP_P", "0.9"))
    
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = float(os.getenv("RETRY_DELAY", "1.0"))
    
    @classmethod
    def validate(cls):
        if not cls.API_KEY or cls.API_KEY == "your-api-key-here":
            raise ValueError(
                "请设置DEEPSEEK_API_KEY环境变量\n"
                "创建.env文件并添加: DEEPSEEK_API_KEY=your_key_here"
            )
        return True


class RAGConfig:
    """RAG配置 - 已禁用"""
    
    # 禁用RAG
    ENABLE_RAG = False
    
    # 以下配置保留但不使用
    CHROMA_PERSIST_DIR = "./chroma_db"
    EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'
    DEFAULT_TOP_K = 5
    SIMILARITY_THRESHOLD = 0.6
    USE_GPU = False


class PromptTemplates:
    """提示词模板库 - 精简版"""
    
    SUMMARY_OPTIMIZATION = """
优化个人总结。职位：{job_title}
原文：{content}
输出3句话。
"""
    
    WORK_EXPERIENCE_OPTIMIZATION = """
优化工作经验。职位：{job_title}
原文：{content}
使用STAR法则，添加数字。输出3条。
"""
    
    SKILLS_OPTIMIZATION = """
优化技能。职位：{job_title}
技能：{skills}
关键词：{keywords}
分类输出。
"""
    
    PROJECT_OPTIMIZATION = """
优化项目。职位：{job_title}
原文：{content}
突出技术栈和成果。
"""