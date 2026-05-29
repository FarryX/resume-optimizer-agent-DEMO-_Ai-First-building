from agents.base_agent import BaseAgent
from models.state_models import ResumeState
from skills.text_processing import TextProcessor
import re

class ParserAgent(BaseAgent):
    """简历解析Agent - 负责将原始简历解析为结构化数据"""
    
    def __init__(self, llm_model=None):
        super().__init__("ParserAgent", llm_model)
        self.text_processor = TextProcessor()
    
    async def process(self, state: ResumeState) -> ResumeState:
        self.log_action("开始解析原始简历")
        
        try:
            # 调用解析方法
            parsed_data = await self._parse_resume(state['original_resume'])
            state['parsed_resume'] = parsed_data
            
            # 保存原文用于长度比较
            state['parsed_resume']['original_full_text'] = state['original_resume']
            
            state['optimization_log'].append(self.log_action("简历解析完成"))
            state['current_phase'] = "analysis"
            
        except Exception as e:
            state['error_message'] = f"解析失败: {str(e)}"
            self.log_action(f"解析错误: {str(e)}")
        
        return state
    
    async def _parse_resume(self, resume_text: str) -> dict:
        """解析简历文本为结构化数据"""
        
        sections = {
            'personal_info': self._extract_personal_info(resume_text),
            'summary': self._extract_summary(resume_text),
            'work_experience': self._extract_work_experience(resume_text),
            'education': self._extract_education(resume_text),
            'skills': self._extract_skills(resume_text),
            'projects': self._extract_projects(resume_text),
            'certifications': self._extract_certifications(resume_text)
        }
        
        return sections
    
    def _extract_personal_info(self, text: str) -> str:
        """提取个人信息"""
        lines = text.split('\n')
        personal_lines = []
        
        for i, line in enumerate(lines[:10]):  # 前10行
            if line.strip():
                personal_lines.append(line.strip())
                if len(personal_lines) >= 4:  # 最多4行
                    break
        
        return '\n'.join(personal_lines)
    
    def _extract_summary(self, text: str) -> str:
        """提取个人总结"""
        lines = text.split('\n')
        
        # 查找总结部分
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['个人总结', '自我评价', 'summary', 'profile', '关于我']):
                # 获取接下来的几行
                summary_lines = []
                for j in range(i + 1, min(i + 6, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and not next_line.startswith('#') and not any(
                        kw in next_line.lower() for kw in ['工作经验', '教育背景', '技能', '项目']
                    ):
                        summary_lines.append(next_line)
                    else:
                        break
                
                if summary_lines:
                    return ' '.join(summary_lines)
        
        # 如果没有找到总结部分，尝试取前几行非联系信息的内容
        for line in lines[3:10]:
            line = line.strip()
            if line and len(line) > 20 and not any(c in line for c in ['@', '电话', '手机', '邮箱']):
                return line[:200]
        
        return ""
    
    def _extract_work_experience(self, text: str) -> list:
        """提取工作经验"""
        experience = []
        lines = text.split('\n')
        
        in_experience = False
        experience_lines = []
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # 检测工作经验开始
            if any(keyword in line_lower for keyword in ['工作经验', '工作经历', 'work experience', '工作履历']):
                in_experience = True
                continue
            
            # 检测工作经验结束
            if in_experience and any(keyword in line_lower for keyword in ['教育背景', '项目经验', '技能', '证书', '语言']):
                break
            
            # 收集工作经验内容
            if in_experience and line.strip():
                clean_line = line.strip()
                # 跳过空行和标题
                if clean_line and not clean_line.startswith('#'):
                    experience_lines.append(clean_line)
        
        # 按空行分割成不同的工作经验
        current_exp = []
        for line in experience_lines:
            if line and len(line) > 0:
                current_exp.append(line)
            elif current_exp:
                experience.append(' '.join(current_exp))
                current_exp = []
        
        if current_exp:
            experience.append(' '.join(current_exp))
        
        # 如果没有找到工作经验部分，尝试智能提取
        if not experience:
            for line in lines:
                if '公司' in line or '有限' in line or '科技' in line or '任职' in line:
                    if len(line) > 10:
                        experience.append(line.strip())
        
        return experience[:8]  # 最多8条
    
    def _extract_education(self, text: str) -> str:
        """提取教育经历"""
        lines = text.split('\n')
        education_lines = []
        
        in_education = False
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # 检测教育背景开始
            if any(keyword in line_lower for keyword in ['教育背景', '教育经历', 'education', '学历']):
                in_education = True
                continue
            
            # 检测结束
            if in_education and any(keyword in line_lower for keyword in ['工作经验', '项目经验', '技能']):
                break
            
            if in_education and line.strip():
                clean_line = line.strip()
                if clean_line and not clean_line.startswith('#'):
                    education_lines.append(clean_line)
        
        if education_lines:
            return ' '.join(education_lines[:3])
        
        # 如果没有找到，尝试直接找学校关键词
        school_keywords = ['大学', '学院', '本科', '硕士', '博士', '研究生']
        for line in lines:
            if any(kw in line for kw in school_keywords):
                return line.strip()
        
        return ""
    
    def _extract_skills(self, text: str) -> list:
        """提取技能"""
        skills = []
        lines = text.split('\n')
        
        # 常见技能关键词
        skill_keywords = [
            'Python', 'Java', 'JavaScript', 'C++', 'Go', 'Rust',
            'React', 'Vue', 'Angular', 'Node.js', 'Spring',
            'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP',
            'MySQL', 'PostgreSQL', 'MongoDB', 'Redis',
            'Git', 'Jenkins', 'CI/CD', 'Linux',
            'Machine Learning', 'AI', 'TensorFlow', 'PyTorch',
            'HTML', 'CSS', 'TypeScript', 'PHP', 'Ruby'
        ]
        
        in_skills = False
        
        for line in lines:
            line_lower = line.lower()
            
            # 检测技能部分开始
            if any(keyword in line_lower for keyword in ['技能', 'skills', '技术栈', '技术能力']):
                in_skills = True
                continue
            
            if in_skills:
                # 提取技能
                if line.strip():
                    # 按逗号、空格分割
                    parts = re.split(r'[,，、\s]+', line)
                    for part in parts:
                        part = part.strip()
                        if part and len(part) < 30:  # 技能名通常较短
                            for skill in skill_keywords:
                                if skill.lower() == part.lower() or skill.lower() in part.lower():
                                    skills.append(skill)
                                    break
                            else:
                                if len(part) > 1 and not part.isdigit():
                                    skills.append(part)
                
                # 检查是否结束
                if any(keyword in line_lower for keyword in ['项目', '证书', '语言', '爱好']):
                    break
        
        # 去重并保留顺序
        seen = set()
        unique_skills = []
        for s in skills:
            if s not in seen:
                seen.add(s)
                unique_skills.append(s)
        
        return unique_skills[:15]  # 最多15个技能
    
    def _extract_projects(self, text: str) -> list:
        """提取项目经验"""
        projects = []
        lines = text.split('\n')
        
        in_projects = False
        project_lines = []
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # 检测项目经验开始
            if any(keyword in line_lower for keyword in ['项目经验', '项目经历', 'projects', '主要项目']):
                in_projects = True
                continue
            
            # 检测结束
            if in_projects and any(keyword in line_lower for keyword in ['技能', '证书', '语言', '获奖']):
                break
            
            if in_projects and line.strip():
                clean_line = line.strip()
                if clean_line and not clean_line.startswith('#'):
                    project_lines.append(clean_line)
        
        # 按空行或数字序号分割
        current_project = []
        for line in project_lines:
            # 检测新项目开始（数字序号、•、-等）
            if re.match(r'^(\d+[\.\)、]|[•\-*])', line) or (len(line) < 50 and current_project):
                if current_project:
                    projects.append(' '.join(current_project))
                    current_project = []
            current_project.append(line)
        
        if current_project:
            projects.append(' '.join(current_project))
        
        return projects[:5]  # 最多5个项目
    
    def _extract_certifications(self, text: str) -> list:
        """提取证书"""
        certs = []
        lines = text.split('\n')
        
        in_certs = False
        
        for line in lines:
            line_lower = line.lower()
            
            if any(keyword in line_lower for keyword in ['证书', '认证', 'certification', '资格']):
                in_certs = True
                continue
            
            if in_certs:
                if line.strip():
                    if any(keyword in line_lower for keyword in ['工作经验', '项目', '技能']):
                        break
                    certs.append(line.strip())
        
        return certs[:5]