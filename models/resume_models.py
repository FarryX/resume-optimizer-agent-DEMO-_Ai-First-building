# models/resume_models.py
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class ResumeSection:
    """简历段落模型"""
    personal_info: str = ""
    summary: str = ""
    work_experience: List[str] = None
    education: str = ""
    skills: List[str] = None
    projects: List[str] = None
    certifications: List[str] = None
    
    def __post_init__(self):
        if self.work_experience is None:
            self.work_experience = []
        if self.skills is None:
            self.skills = []
        if self.projects is None:
            self.projects = []
        if self.certifications is None:
            self.certifications = []

@dataclass
class OptimizationSuggestion:
    """优化建议"""
    section: str
    original_content: str
    suggested_content: str
    reason: str
    priority: int  # 1-5, 5最高