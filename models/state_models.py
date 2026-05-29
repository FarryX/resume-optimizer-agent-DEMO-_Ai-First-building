# models/state_models.py
from typing import TypedDict, List, Dict, Optional, Any
from enum import Enum

class OptimizationLevel(str, Enum):
    """优化级别"""
    BASIC = "basic"
    PROFESSIONAL = "professional"
    PREMIUM = "premium"

class ResumeState(TypedDict):
    """全局状态管理"""
    # 输入
    original_resume: str
    target_job_title: str
    education_background: str
    additional_requirements: Optional[str]
    
    # 处理过程
    parsed_resume: Dict[str, Any]
    analysis_result: Dict[str, Any]
    optimized_sections: Dict[str, str]
    
    # 技能评分
    ats_score: float
    keyword_match_rate: float
    
    # 最终结果
    final_resume: str
    optimization_log: List[str]
    current_phase: str
    error_message: Optional[str]