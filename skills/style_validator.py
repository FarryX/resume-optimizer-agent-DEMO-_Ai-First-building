from typing import Dict, List, Tuple

class StyleValidator:
    """简历风格验证器"""
    
    def validate_professional_style(self, resume_text: str) -> Tuple[bool, List[str]]:
        """验证专业风格"""
        issues = []
        
        # 检查被动语态
        passive_patterns = ['被', '由', '受到']
        for pattern in passive_patterns:
            if pattern in resume_text:
                issues.append(f"使用被动语态: '{pattern}'")
        
        # 检查第一人称使用
        if any(word in resume_text for word in ['我', '我们', '我的']):
            issues.append("避免使用第一人称代词")
        
        # 检查长度
        lines = resume_text.split('\n')
        if any(len(line) > 100 for line in lines):
            issues.append("有行文本过长，建议分行")
        
        return len(issues) == 0, issues
    
    def suggest_improvements(self, section: str, content: str) -> List[str]:
        """提供改进建议"""
        suggestions = []
        
        if section == 'work_experience':
            if '负责' in content and '结果' not in content:
                suggestions.append("建议使用STAR法则，突出行动和结果")
            if not any(word in content for word in ['提高', '降低', '增加', '减少']):
                suggestions.append("建议添加量化成果")
        
        elif section == 'skills':
            if len(content.split(',')) > 15:
                suggestions.append("技能过多，建议筛选最相关的10个")
            if not any(word in content for word in ['精通', '熟悉', '掌握']):
                suggestions.append("建议使用熟练度分级")
        
        return suggestions