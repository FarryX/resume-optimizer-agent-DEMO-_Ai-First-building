# agents/base_agent.py
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from models.state_models import ResumeState
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseAgent:
    """基础Agent类，所有Agent继承此类"""
    
    def __init__(self, name: str, llm_model: Any = None):
        self.name = name
        self.llm = llm_model
        logger.info(f"Initializing {self.name}")
    
    async def process(self, state: ResumeState) -> ResumeState:
        """处理状态，子类需要实现"""
        raise NotImplementedError
    
    def log_action(self, message: str) -> str:
        """日志记录Agent操作"""
        logger.info(f"[{self.name}] {message}")
        return f"{self.name}: {message}"