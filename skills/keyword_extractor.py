# skills/keyword_extractor.py - 添加向量检索

from typing import List, Dict
import re

class KeywordExtractor:
    """职位关键词提取器 - 混合模式（硬匹配 + 向量检索）"""
    
    TECH_KEYWORDS = {
        'python_developer': ['Python', 'Django', 'Flask', 'Pandas', 'NumPy', 'FastAPI'],
        'java_developer': ['Java', 'Spring Boot', 'Hibernate', 'Maven', 'JUnit'],
        'frontend_developer': ['React', 'Vue.js', 'Angular', 'JavaScript', 'TypeScript', 'HTML5', 'CSS3'],
        'data_scientist': ['Python', 'SQL', 'Machine Learning', 'Statistics', 'TensorFlow', 'PyTorch'],
        'devops_engineer': ['Docker', 'Kubernetes', 'Jenkins', 'AWS', 'Linux', 'Terraform'],
        'ai_engineer': ['Python', 'Deep Learning', 'NLP', 'Computer Vision', 'LangChain', 'LLM']
    }
    
    SOFT_SKILLS = ['团队协作', '沟通能力', '问题解决', '项目管理', '领导力', '创新思维']
    
    def __init__(self):
        # ========== 新增：引用全局客户端用于向量检索 ==========
        self._deepseek_client = None
    
    @property
    def deepseek_client(self):
        """延迟导入，避免循环依赖"""
        if self._deepseek_client is None:
            from llm_client import deepseek_client
            self._deepseek_client = deepseek_client
        return self._deepseek_client
    
    def extract_from_job_title(self, job_title: str) -> List[str]:
        """从职位标题提取关键词（混合模式）"""
        
        job_title_lower = job_title.lower()
        keywords = []
        
        # 阶段1：硬匹配（快速）
        for role, techs in self.TECH_KEYWORDS.items():
            role_parts = role.split('_')
            if all(part in job_title_lower for part in role_parts):
                keywords.extend(techs)
                break
        
        # 阶段2：如果没有精确匹配，使用模糊匹配
        if not keywords:
            for tech in ['Python', 'Java', 'JavaScript', 'SQL', '数据分析']:
                if tech.lower() in job_title_lower:
                    keywords.append(tech)
        
        # ========== 新增：阶段3：向量检索增强（0 Token成本）==========
        # 通过向量检索获取更准确的关键词建议
        vector_keywords = self._get_keywords_from_vector_search(job_title)
        if vector_keywords:
            keywords.extend(vector_keywords)
        
        # 阶段4：如果仍然为空，使用默认
        if not keywords:
            keywords = ['Python', 'SQL', '数据分析', '问题解决', '团队合作']
        
        # 阶段5：添加软技能
        keywords.extend(self.SOFT_SKILLS[:3])
        
        # 去重并返回
        return list(set(keywords))
    
    # ========== 新增：向量检索获取关键词 ==========
    def _get_keywords_from_vector_search(self, job_title: str) -> List[str]:
        """
        通过向量检索获取关键词 - 0 Token成本
        利用Chroma知识库找到相似职位的关键词
        """
        try:
            # 调用向量检索
            results = self.deepseek_client.search_by_job_title(job_title, top_k=2)
            
            if not results:
                return []
            
            # 从检索结果中提取关键词
            extracted_keywords = []
            for result in results:
                content = result.get('content', '')
                # 从内容中提取技术关键词
                for tech_list in self.TECH_KEYWORDS.values():
                    for tech in tech_list:
                        if tech.lower() in content.lower():
                            extracted_keywords.append(tech)
            
            return list(set(extracted_keywords))[:5]  # 最多返回5个
            
        except Exception as e:
            # 向量检索失败不影响主流程
            print(f"向量检索失败: {e}")
            return []
    
    def extract_from_description(self, job_description: str) -> Dict[str, List[str]]:
        """从职位描述中提取关键词"""
        
        job_desc_lower = job_description.lower()
        tech_skills = []
        soft_skills = []
        
        for role_keywords in self.TECH_KEYWORDS.values():
            for keyword in role_keywords:
                if keyword.lower() in job_desc_lower:
                    tech_skills.append(keyword)
        
        for skill in self.SOFT_SKILLS:
            if skill in job_description:
                soft_skills.append(skill)
        
        # ========== 新增：向量检索补充 ==========
        vector_results = self.deepseek_client.search_knowledge(
            job_description[:500], "job_skills", top_k=2
        )
        for result in vector_results:
            content = result.get('content', '')
            for tech_list in self.TECH_KEYWORDS.values():
                for tech in tech_list:
                    if tech.lower() in content.lower() and tech not in tech_skills:
                        tech_skills.append(tech)
        
        return {
            'technical': list(set(tech_skills)),
            'soft': soft_skills
        }