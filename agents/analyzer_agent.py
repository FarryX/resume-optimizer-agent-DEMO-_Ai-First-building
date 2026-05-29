# agents/analyzer_agent.py - 确保使用规则引擎，不调用LLM分析

from agents.base_agent import BaseAgent
from models.state_models import ResumeState
from models.resume_models import OptimizationSuggestion
from skills.keyword_extractor import KeywordExtractor
from skills.ats_scorer import ATSScorer
from typing import List, Dict

class AnalyzerAgent(BaseAgent):
    
    def __init__(self, llm_model=None):
        super().__init__("AnalyzerAgent", llm_model)
        self.keyword_extractor = KeywordExtractor()
        self.ats_scorer = ATSScorer()
    
    async def process(self, state: ResumeState) -> ResumeState:
        self.log_action(f"开始分析简历与{state['target_job_title']}的匹配度")
        
        try:
            job_keywords = self.keyword_extractor.extract_from_job_title(
                state['target_job_title']
            )
            
            # 计算ATS评分
            ats_analysis = await self.ats_scorer.score_resume(
                state['parsed_resume'],
                job_keywords
            )
            
            state['ats_score'] = ats_analysis['total_score']
            state['keyword_match_rate'] = ats_analysis['match_rate']
            
            # 使用规则引擎生成建议（不调用LLM）
            suggestions = await self._generate_suggestions(
                state['parsed_resume'],
                job_keywords,
                state['education_background']
            )
            
            state['analysis_result'] = {
                'job_keywords': job_keywords,
                'ats_analysis': ats_analysis,
                'suggestions': suggestions,
                'strengths': ats_analysis.get('strengths', []),
                'weaknesses': ats_analysis.get('weaknesses', [])
            }
            
            state['optimization_log'].append(
                self.log_action(f"分析完成 - ATS评分: {state['ats_score']}/100")
            )
            state['current_phase'] = "optimization"
            
        except Exception as e:
            state['error_message'] = f"分析失败: {str(e)}"
            self.log_action(f"分析错误: {str(e)}")
            # 提供默认值
            state['analysis_result'] = {
                'job_keywords': [],
                'ats_analysis': {},
                'suggestions': [],
                'strengths': [],
                'weaknesses': []
            }
        
        return state
    
    async def _generate_suggestions(self, parsed_resume: dict, 
                                   job_keywords: List[str],
                                   education: str) -> List[OptimizationSuggestion]:
        """规则引擎生成建议"""
        
        suggestions = []
        
        current_skills = set(parsed_resume.get('skills', []))
        missing_keywords = [kw for kw in job_keywords if kw not in current_skills]
        
        if missing_keywords:
            suggestions.append(OptimizationSuggestion(
                section="skills",
                original_content=', '.join(current_skills),
                suggested_content=', '.join(list(current_skills)[:8] + missing_keywords[:3]),
                reason=f"缺少关键词: {', '.join(missing_keywords[:3])}",
                priority=5
            ))
        
        work_exp = parsed_resume.get('work_experience', [])
        if len(work_exp) < 2:
            suggestions.append(OptimizationSuggestion(
                section="work_experience",
                original_content='\n'.join(work_exp),
                suggested_content="建议使用STAR法则，添加量化成果",
                reason="工作经验描述不够详细",
                priority=4
            ))
        
        if not parsed_resume.get('summary'):
            suggestions.append(OptimizationSuggestion(
                section="summary",
                original_content="",
                suggested_content="建议添加个人专业总结",
                reason="缺少个人总结",
                priority=3
            ))
        
        return suggestions