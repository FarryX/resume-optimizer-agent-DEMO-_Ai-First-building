# agents/coordinator_agent.py
from langgraph.graph import StateGraph, END
from agents.base_agent import BaseAgent
from agents.parser_agent import ParserAgent
from agents.analyzer_agent import AnalyzerAgent
from agents.optimizer_agent import OptimizerAgent
from models.state_models import ResumeState
from typing import Dict, Any
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoordinatorAgent(BaseAgent):
    """协调Agent - 管理整个优化流程"""
    
    def __init__(self, llm_model=None):
        super().__init__("CoordinatorAgent", llm_model)
        self.parser = ParserAgent(llm_model)
        self.analyzer = AnalyzerAgent(llm_model)
        self.optimizer = OptimizerAgent(llm_model)
        self.workflow = None
        self._setup_workflow()
    
    def _setup_workflow(self):
        """设置LangGraph工作流"""
        # 创建状态图
        workflow = StateGraph(ResumeState)
        
        # 添加节点
        workflow.add_node("parse", self.parser.process)
        workflow.add_node("analyze", self.analyzer.process)
        workflow.add_node("optimize", self.optimizer.process)
        
        # 定义边
        workflow.set_entry_point("parse")
        workflow.add_edge("parse", "analyze")
        workflow.add_edge("analyze", "optimize")
        workflow.add_edge("optimize", END)
        
        # 编译工作流
        self.workflow = workflow.compile()
        logger.info("工作流初始化完成")
    
    async def optimize_resume(self, original_resume: str, 
                             target_job: str,
                             education: str,
                             additional_reqs: str = None) -> Dict[str, Any]:
        """执行简历优化流程"""
        
        self.log_action(f"开始为职位 '{target_job}' 优化简历")
        
        # 初始化状态
        initial_state: ResumeState = {
            'original_resume': original_resume,
            'target_job_title': target_job,
            'education_background': education,
            'additional_requirements': additional_reqs,
            'parsed_resume': {},
            'analysis_result': {},
            'optimized_sections': {},
            'ats_score': 0.0,
            'keyword_match_rate': 0.0,
            'final_resume': '',
            'optimization_log': [],
            'current_phase': 'initializing',
            'error_message': None
        }
        
        try:
            # 执行工作流
            final_state = await self.workflow.ainvoke(initial_state)
            
            result = {
                'success': final_state['error_message'] is None,
                'final_resume': final_state['final_resume'],
                'ats_score': final_state['ats_score'],
                'match_rate': final_state['keyword_match_rate'],
                'optimization_log': final_state['optimization_log'],
                'analysis': final_state['analysis_result']
            }
            
            if final_state['error_message']:
                result['error'] = final_state['error_message']
            
            self.log_action(f"优化完成，ATS评分: {result['ats_score']}")
            return result
            
        except Exception as e:
            self.log_action(f"优化流程失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'optimization_log': [self.log_action(f"错误: {str(e)}")]
            }