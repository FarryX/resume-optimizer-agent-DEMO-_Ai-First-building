# skills/pdf_processor.py - 增强版PDF格式化
import PyPDF2
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
import io
import os
import re

class PDFProcessor:
    """PDF文件处理器 - 美观格式版"""
    
    # 定义颜色
    COLORS = {
        'primary': colors.HexColor('#2c3e50'),      # 深蓝色（标题）
        'secondary': colors.HexColor('#34495e'),     # 灰蓝色（副标题）
        'accent': colors.HexColor('#3498db'),        # 亮蓝色（强调）
        'text': colors.HexColor('#333333'),          # 深灰色（正文）
        'light_text': colors.HexColor('#666666'),    # 浅灰色（次要文字）
        'border': colors.HexColor('#e0e0e0'),        # 边框色
    }
    
    @staticmethod
    def read_pdf(file_path: str) -> str:
        """从PDF读取文本"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
            return text
        except Exception as e:
            raise Exception(f"读取PDF失败: {e}")
    
    @staticmethod
    def save_to_pdf(text: str, output_path: str, title: str = "优化简历"):
        """保存文本为美观格式PDF"""
        try:
            # 创建PDF文档
            doc = SimpleDocTemplate(
                output_path, 
                pagesize=A4,
                topMargin=2*cm,
                bottomMargin=2*cm,
                leftMargin=2.5*cm,
                rightMargin=2.5*cm,
                title=title
            )
            
            story = []
            
            # 注册中文字体
            font_registered = PDFProcessor._register_chinese_font()
            
            # 创建样式
            styles = PDFProcessor._create_styles(font_registered)
            
            # 解析Markdown格式的文本
            elements = PDFProcessor._parse_markdown_to_elements(text, styles)
            story.extend(elements)
            
            # 生成PDF
            doc.build(story, onFirstPage=PDFProcessor._header_footer, onLaterPages=PDFProcessor._header_footer)
            return True
            
        except Exception as e:
            print(f"PDF生成警告: {e}")
            # 如果格式化失败，使用简单版本
            PDFProcessor._save_simple_pdf(text, output_path)
            return False
    
    @staticmethod
    def _register_chinese_font():
        """注册中文字体"""
        try:
            # Windows字体路径
            font_paths = [
                "C:/Windows/Fonts/simhei.ttf",      # 黑体
                "C:/Windows/Fonts/msyh.ttc",        # 微软雅黑
                "C:/Windows/Fonts/simsun.ttc",      # 宋体
                "C:/Windows/Fonts/SimHei.ttf",
                "/System/Library/Fonts/PingFang.ttc",  # macOS
                "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Linux
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    addMapping('ChineseFont', 0, 0, 'ChineseFont')
                    addMapping('ChineseFont', 1, 0, 'ChineseFont')  # 粗体
                    print(f"字体加载成功: {font_path}")
                    return True
            
            print("未找到中文字体，将使用默认字体")
            return False
            
        except Exception as e:
            print(f"字体加载失败: {e}")
            return False
    
    @staticmethod
    def _create_styles(font_registered):
        """创建PDF样式"""
        styles = getSampleStyleSheet()
        
        # 基础字体名称
        base_font = 'ChineseFont' if font_registered else 'Helvetica'
        
        # 主标题样式（姓名）
        name_style = ParagraphStyle(
            'NameStyle',
            parent=styles['Normal'],
            fontName=base_font,
            fontSize=24,
            textColor=PDFProcessor.COLORS['primary'],
            alignment=TA_CENTER,
            spaceAfter=20,
            spaceBefore=10
        )
        
        # 一级标题（## 标题）
        h1_style = ParagraphStyle(
            'H1Style',
            parent=styles['Normal'],
            fontName=base_font,
            fontSize=16,
            textColor=PDFProcessor.COLORS['secondary'],
            alignment=TA_LEFT,
            spaceBefore=15,
            spaceAfter=10,
            borderWidth=0,
            borderColor=PDFProcessor.COLORS['border'],
            borderPadding=5,
            borderRadius=0
        )
        
        # 二级标题
        h2_style = ParagraphStyle(
            'H2Style',
            parent=styles['Normal'],
            fontName=base_font,
            fontSize=14,
            textColor=PDFProcessor.COLORS['secondary'],
            alignment=TA_LEFT,
            spaceBefore=12,
            spaceAfter=8
        )
        
        # 正文样式
        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontName=base_font,
            fontSize=10,
            leading=16,  # 行距
            textColor=PDFProcessor.COLORS['text'],
            alignment=TA_JUSTIFY,  # 两端对齐
            spaceBefore=4,
            spaceAfter=4
        )
        
        # 要点列表样式
        bullet_style = ParagraphStyle(
            'BulletStyle',
            parent=styles['Normal'],
            fontName=base_font,
            fontSize=10,
            leading=16,
            textColor=PDFProcessor.COLORS['text'],
            leftIndent=20,
            bulletIndent=10,
            spaceBefore=2,
            spaceAfter=2
        )
        
        # 联系方式样式
        contact_style = ParagraphStyle(
            'ContactStyle',
            parent=styles['Normal'],
            fontName=base_font,
            fontSize=9,
            textColor=PDFProcessor.COLORS['light_text'],
            alignment=TA_CENTER,
            spaceAfter=15
        )
        
        return {
            'name': name_style,
            'h1': h1_style,
            'h2': h2_style,
            'body': body_style,
            'bullet': bullet_style,
            'contact': contact_style,
            'normal': styles['Normal']
        }
    
    @staticmethod
    def _parse_markdown_to_elements(text: str, styles):
        """解析Markdown格式文本为PDF元素"""
        from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
        
        elements = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                elements.append(Spacer(1, 6))
                i += 1
                continue
            
            # 处理姓名（第一行非标题内容）
            if i == 0 and not line.startswith('#'):
                elements.append(Paragraph(line, styles['name']))
                elements.append(Spacer(1, 5))
                i += 1
                continue
            
            # 处理联系方式（包含电话/邮箱的行）
            if '电话' in line or '邮箱' in line or '@' in line or '手机' in line:
                elements.append(Paragraph(line, styles['contact']))
                i += 1
                continue
            
            # 处理一级标题 ## 标题
            if line.startswith('##'):
                title_text = line.replace('##', '').strip()
                # 添加下划线效果
                elements.append(Paragraph(title_text, styles['h1']))
                elements.append(Spacer(1, 3))
                # 添加分割线
                from reportlab.platypus import HRFlowable
                elements.append(HRFlowable(width="100%", thickness=0.5, color=PDFProcessor.COLORS['border']))
                elements.append(Spacer(1, 6))
                i += 1
                continue
            
            # 处理三级标题
            if line.startswith('###'):
                title_text = line.replace('###', '').strip()
                elements.append(Paragraph(title_text, styles['h2']))
                i += 1
                continue
            
            # 处理要点列表（以•、-、*开头）
            if line.startswith(('•', '-', '*', '·')):
                bullet_text = line.lstrip('•-*· ').strip()
                # 添加项目符号
                elements.append(Paragraph(f'• {bullet_text}', styles['bullet']))
                i += 1
                continue
            
            # 处理普通段落
            if len(line) > 0:
                # 清理特殊字符
                line = PDFProcessor._clean_text(line)
                elements.append(Paragraph(line, styles['body']))
            
            i += 1
        
        return elements
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """清理文本中的特殊字符"""
        # 替换可能引起问题的字符
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&apos;',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    @staticmethod
    def _header_footer(canvas, doc):
        """添加页眉页脚"""
        canvas.saveState()
        
        # 页眉
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#999999'))
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin - 10, "简历优化Agent")
        
        # 页脚
        page_num = canvas.getPageNumber()
        canvas.drawCentredString(doc.width / 2, doc.bottomMargin - 10, f"第 {page_num} 页")
        
        # 添加装饰线
        canvas.setStrokeColor(colors.HexColor('#e0e0e0'))
        canvas.line(doc.leftMargin, doc.height + doc.topMargin - 15, 
                    doc.width + doc.leftMargin, doc.height + doc.topMargin - 15)
        canvas.line(doc.leftMargin, doc.bottomMargin - 15, 
                    doc.width + doc.leftMargin, doc.bottomMargin - 15)
        
        canvas.restoreState()
    
    @staticmethod
    def _save_simple_pdf(text: str, output_path: str):
        """简化版PDF保存（备用）"""
        from reportlab.pdfgen import canvas
        
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        y = height - 50
        
        c.setFont("Helvetica", 10)
        
        for line in text.split('\n'):
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = height - 50
            
            # 处理长文本换行
            if len(line) > 80:
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line) + len(word) + 1 <= 80:
                        current_line += word + " "
                    else:
                        c.drawString(50, y, current_line)
                        y -= 15
                        current_line = word + " "
                c.drawString(50, y, current_line)
            else:
                c.drawString(50, y, line)
            y -= 15
        
        c.save()