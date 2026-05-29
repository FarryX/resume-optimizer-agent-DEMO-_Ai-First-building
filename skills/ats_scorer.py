from typing import Dict, List, Any

class ATSScorer:
    """ATS系统评分器"""
    
    async def score_resume(self, parsed_resume: Dict, job_keywords: List[str]) -> Dict[str, Any]:
        """计算简历的ATS评分"""
        
        scores = {}
        weaknesses = []
        strengths = []
        
        # 1. 关键词匹配度 (40分)
        keyword_score = self._calculate_keyword_match(parsed_resume, job_keywords)
        scores['keyword_match'] = keyword_score
        
        if keyword_score < 20:
            weaknesses.append("缺少目标职位的关键词")
        else:
            strengths.append("关键词匹配度较好")
        
        # 2. 量化成就 (20分)
        quant_score = self._check_quantifiable_achievements(parsed_resume)
        scores['quantifiable'] = quant_score
        
        if quant_score < 10:
            weaknesses.append("工作经验缺少量化成果")
        else:
            strengths.append("有量化的工作成果")
        
        # 3. 格式规范性 (20分)
        format_score = self._check_format(parsed_resume)
        scores['format'] = format_score
        
        # 4. 内容完整性 (20分)
        completeness_score = self._check_completeness(parsed_resume)
        scores['completeness'] = completeness_score
        
        if completeness_score < 15:
            weaknesses.append("简历内容不够完整")
        
        # 计算总分
        total_score = sum(scores.values())
        
        return {
            'total_score': total_score,
            'match_rate': (keyword_score / 40) * 100,
            'detailed_scores': scores,
            'strengths': strengths,
            'weaknesses': weaknesses
        }
    
    def _calculate_keyword_match(self, resume: Dict, keywords: List[str]) -> int:
        """计算关键词匹配分数"""
        if not keywords:
            return 40
        
        # 收集所有简历文本
        resume_text = ' '.join([
            ' '.join(resume.get('skills', [])),
            ' '.join(resume.get('work_experience', [])),
            resume.get('summary', ''),
            ' '.join(resume.get('projects', []))
        ]).lower()
        
        # 计算匹配数
        matched = sum(1 for kw in keywords if kw.lower() in resume_text)
        
        # 匹配率转分数 (满分40)
        match_rate = matched / len(keywords)
        return int(match_rate * 40)
    
    def _check_quantifiable_achievements(self, resume: Dict) -> int:
        """检查量化成就"""
        quant_patterns = ['%', '提高', '降低', '节省', '增长', '提升', '优化', 
                         '创建', '开发', '领导', '管理', '完成']
        
        score = 0
        text = ' '.join(resume.get('work_experience', []))
        
        for pattern in quant_patterns:
            if pattern in text:
                score += 2
        
        return min(20, score)
    
    def _check_format(self, resume: Dict) -> int:
        """检查格式规范性"""
        score = 20
        
        # 检查是否有明确的段落划分
        sections = ['summary', 'work_experience', 'education', 'skills']
        present_sections = sum(1 for section in sections if resume.get(section))
        
        if present_sections < 3:
            score -= 10
        
        return max(0, score)
    
    def _check_completeness(self, resume: Dict) -> int:
        """检查内容完整性"""
        score = 0
        
        # 各部分权重
        if resume.get('summary'):
            score += 5
        if resume.get('work_experience'):
            score += 8
        if resume.get('education'):
            score += 4
        if resume.get('skills'):
            score += 3
        
        return min(20, score)