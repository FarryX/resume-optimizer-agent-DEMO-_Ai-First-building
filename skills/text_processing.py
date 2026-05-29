import re
from typing import List

class TextProcessor:
    """文本处理工具类"""
    
    def clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符（保留基本标点）
        text = re.sub(r'[^\w\s\u4e00-\u9fff\.\,\!\?\-\:]', '', text)
        return text.strip()
    
    def extract_bullet_points(self, text: str) -> List[str]:
        """提取要点列表"""
        lines = text.split('\n')
        bullets = []
        
        for line in lines:
            if line.strip().startswith(('•', '-', '*', '·')):
                bullets.append(line.strip()[1:].strip())
            elif line.strip() and len(line.strip()) < 100:
                bullets.append(line.strip())
        
        return bullets
    
    def improve_action_verbs(self, text: str) -> str:
        """改善行动动词"""
        weak_verbs = {
            '负责': ['负责了', '作为负责人'],
            '帮助': ['协助了', '辅助'],
            '做': ['完成了', '执行了']
        }
        
        strong_verbs = {
            '负责': '领导',
            '帮助': '推动',
            '做': '实现'
        }
        
        for weak, replacements in weak_verbs.items():
            for replacement in replacements:
                if replacement in text:
                    text = text.replace(replacement, strong_verbs[weak])
        
        return text