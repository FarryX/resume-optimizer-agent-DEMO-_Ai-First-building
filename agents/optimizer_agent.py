from agents.base_agent import BaseAgent
from models.state_models import ResumeState
from skills.text_processing import TextProcessor
from skills.style_validator import StyleValidator
from llm_client import deepseek_client
from typing import List, Dict, Any
import asyncio
import json
import re
from datetime import datetime


class OptimizerAgent(BaseAgent):
    """优化Agent - 只生成建议，绝不修改原文"""

    def __init__(self, llm_model=None):
        super().__init__("OptimizerAgent", llm_model)
        self.text_processor = TextProcessor()
        self.style_validator = StyleValidator()

    async def process(self, state: ResumeState) -> ResumeState:
        self.log_action("开始分析简历（只生成建议模式）")

        try:
            # 获取职位关键词
            keywords = state['analysis_result'].get('job_keywords', [])
            job_title = state['target_job_title']

            # 评估简历
            assessment = self._assess_resume_detail(state['parsed_resume'])

            self.log_action(f"简历评估: 总结{assessment['summary_len']}字, "
                            f"工作经验{assessment['work_count']}条, "
                            f"技能{assessment['skill_count']}个, "
                            f"项目{assessment['project_count']}个")

            # 判断简历是否足够详细
            is_detailed = self._is_resume_detailed(assessment)

            # ========== 生成优化建议 ==========
            suggestions = await self._generate_improvement_suggestions(
                state['parsed_resume'],
                job_title,
                keywords,
                assessment
            )

            # ========== 根据详细程度决定输出内容 ==========
            if is_detailed:
                # 简历足够详细：只输出建议，不输出原文
                self.log_action("简历已足够详细，只输出优化建议")

                # 构建建议报告（不含原文）
                report = self._build_suggestions_only_report(
                    state,
                    suggestions,
                    job_title,
                    assessment
                )

                state['final_resume'] = report
                state['optimization_mode'] = 'suggestions_only'
                state['optimization_log'].append(
                    self.log_action(f"简历已足够详细，生成 {len(suggestions)} 条优化建议（未包含原文）")
                )
            else:
                # 简历需要改进：输出建议 + 原文（供参考）
                self.log_action("简历需要改进，输出建议和原文")

                # 构建完整报告（含原文）
                report = self._build_full_report(
                    state,
                    suggestions,
                    job_title,
                    assessment
                )

                state['final_resume'] = report
                state['optimization_mode'] = 'suggestions_with_resume'
                state['optimization_log'].append(
                    self.log_action(f"生成 {len(suggestions)} 条优化建议（包含原文参考）")
                )

            state['optimization_suggestions'] = suggestions
            state['current_phase'] = "completed"

        except Exception as e:
            state['error_message'] = f"处理失败: {str(e)}"
            self.log_action(f"处理错误: {str(e)}")
            state['final_resume'] = f"处理失败: {str(e)}"
            state['optimization_suggestions'] = []

        return state

    def _is_resume_detailed(self, assessment: dict) -> bool:
        """判断简历是否足够详细"""
        # 详细标准：
        # - 总结 > 60字
        # - 工作经验 >= 2条
        # - 技能 >= 6个
        # - 项目 >= 2个

        summary_ok = assessment['summary_len'] >= 60
        work_ok = assessment['work_count'] >= 2
        skills_ok = assessment['skill_count'] >= 6
        projects_ok = assessment['project_count'] >= 2

        # 至少3项达标才算详细
        ok_count = sum([summary_ok, work_ok, skills_ok, projects_ok])

        return ok_count >= 3

    def _assess_resume_detail(self, parsed_resume: dict) -> dict:
        """评估简历详细程度"""
        summary = parsed_resume.get('summary', '')
        work_exp = parsed_resume.get('work_experience', [])
        skills = parsed_resume.get('skills', [])
        projects = parsed_resume.get('projects', [])

        return {
            'summary_len': len(summary),
            'work_count': len(work_exp),
            'work_items': work_exp,
            'skill_count': len(skills),
            'skills': skills,
            'project_count': len(projects),
            'projects': projects
        }

    async def _generate_improvement_suggestions(self, parsed_resume: dict,
                                                job_title: str,
                                                keywords: List[str],
                                                assessment: dict) -> List[dict]:
        """生成改进建议"""
        suggestions = []

        # 构建完整的简历内容用于分析
        full_resume = self._build_full_resume(parsed_resume)

        # 调用LLM生成建议
        prompt = f"""作为资深HR和简历优化专家，请分析以下简历与目标职位的匹配度，提供具体的改进建议。

## 目标职位
{job_title}

## 职位关键词
{', '.join(keywords[:10])}

## 当前简历
{full_resume}

## 简历现状
- 个人总结长度: {assessment['summary_len']}字
- 工作经验条数: {assessment['work_count']}条
- 技能数量: {assessment['skill_count']}个
- 项目数量: {assessment['project_count']}个

## 输出要求
请提供3-6条具体的改进建议，每条建议包括：
1. 问题描述：当前存在的问题
2. 改进建议：具体怎么做
3. 示例：改写示例（可选）
4. 优先级：1-5（5最高）

输出JSON格式：
{{
    "suggestions": [
        {{
            "section": "总结/工作经验/技能/项目/整体",
            "issue": "问题描述",
            "suggestion": "改进建议",
            "example": "示例（可选）",
            "priority": 5
        }}
    ]
}}

注意：只输出JSON，不要有其他内容。
"""

        try:
            response = await deepseek_client.optimize_text(prompt, {}, max_tokens=1000)

            # 提取JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                suggestions = result.get('suggestions', [])

        except Exception as e:
            self.log_action(f"LLM生成建议失败: {e}")

        # 补充规则建议（确保至少有建议）
        rule_suggestions = self._generate_rule_suggestions(parsed_resume, keywords, assessment)

        # 合并去重
        existing_issues = {s.get('issue', '') for s in suggestions}
        for rs in rule_suggestions:
            if rs.get('issue', '') not in existing_issues:
                suggestions.append(rs)

        return suggestions

    def _build_full_resume(self, parsed_resume: dict) -> str:
        """构建完整简历文本"""
        parts = []

        if parsed_resume.get('personal_info'):
            parts.append(f"【个人信息】\n{parsed_resume['personal_info']}")

        if parsed_resume.get('summary'):
            parts.append(f"【个人总结】\n{parsed_resume['summary']}")

        work_exp = parsed_resume.get('work_experience', [])
        if work_exp:
            work_text = '\n'.join([f"- {w}" for w in work_exp])
            parts.append(f"【工作经验】\n{work_text}")

        if parsed_resume.get('education'):
            parts.append(f"【教育背景】\n{parsed_resume['education']}")

        skills = parsed_resume.get('skills', [])
        if skills:
            parts.append(f"【技能】\n{', '.join(skills)}")

        projects = parsed_resume.get('projects', [])
        if projects:
            projects_text = '\n'.join([f"- {p}" for p in projects])
            parts.append(f"【项目经验】\n{projects_text}")

        return '\n\n'.join(parts)

    def _generate_rule_suggestions(self, parsed_resume: dict,
                                   keywords: List[str],
                                   assessment: dict) -> List[dict]:
        """基于规则生成建议"""
        suggestions = []

        # 获取职位关键词
        job_keyword = keywords[0] if keywords else "目标职位"

        # 1. 关键词匹配建议
        current_skills = set(parsed_resume.get('skills', []))
        missing_keywords = [kw for kw in keywords if kw not in current_skills]

        if missing_keywords:
            suggestions.append({
                'section': '技能',
                'issue': '简历中缺少目标职位相关的关键技能词',
                'suggestion': f'建议在技能部分添加以下关键词：{", ".join(missing_keywords[:5])}。这些是{job_keyword}职位常用的技能要求。',
                'priority': 5
            })

        # 2. 个人总结建议
        summary_len = assessment['summary_len']
        if summary_len == 0:
            suggestions.append({
                'section': '个人总结',
                'issue': '简历缺少个人总结部分',
                'suggestion': f'建议添加3-4句话的个人总结，突出核心竞争力和与{job_keyword}相关的能力。',
                'example': f'具有多年{job_keyword}经验，精通相关技术栈，擅长系统设计与优化，具备良好的团队协作能力。',
                'priority': 5
            })
        elif summary_len < 60:
            suggestions.append({
                'section': '个人总结',
                'issue': f'个人总结过短（{summary_len}字）',
                'suggestion': f'建议将个人总结扩充到80-120字，更全面地展示您的核心竞争力和职业目标。',
                'priority': 4
            })

        # 3. 工作经验建议
        work_count = assessment['work_count']
        if work_count == 0:
            suggestions.append({
                'section': '工作经验',
                'issue': '简历缺少工作经验描述',
                'suggestion': '建议添加详细的工作经历，使用STAR法则（情境、任务、行动、结果）描述每段工作。',
                'priority': 5
            })
        elif work_count < 2:
            suggestions.append({
                'section': '工作经验',
                'issue': f'工作经验条数较少（{work_count}条）',
                'suggestion': '建议至少包含2-3段相关工作经历，如果工作经验较少，可以用实习、项目经验补充。',
                'priority': 4
            })

        # 4. 量化成果建议
        work_items = assessment.get('work_items', [])
        has_numbers = any(re.search(r'\d+', w) for w in work_items)
        if not has_numbers and work_items:
            suggestions.append({
                'section': '工作经验',
                'issue': '工作经验缺少量化成果',
                'suggestion': '建议在每条工作经历中添加具体数字，如"提升了30%性能"、"服务100万用户"等，让成果更有说服力。',
                'example': '原："负责系统优化" → 改："负责系统性能优化，将响应时间从500ms降低到200ms，提升了60%"。',
                'priority': 4
            })

        # 5. 技能建议
        skill_count = assessment['skill_count']
        if skill_count < 5:
            suggestions.append({
                'section': '技能',
                'issue': f'技能数量较少（{skill_count}个）',
                'suggestion': f'建议扩充技能列表到8-12个，包括{job_keyword}相关的技术栈、工具和软技能。',
                'priority': 3
            })

        # 6. 项目经验建议
        project_count = assessment['project_count']
        if project_count < 2:
            suggestions.append({
                'section': '项目经验',
                'issue': f'项目经验较少（{project_count}个）',
                'suggestion': '建议添加2-3个有代表性的项目，说明项目背景、技术栈、你的职责和项目成果。',
                'priority': 3
            })

        return suggestions

    def _build_suggestions_only_report(self, state: ResumeState,
                                       suggestions: List[dict],
                                       job_title: str,
                                       assessment: dict) -> str:
        """构建只包含建议的报告（不含原文）"""
        report_lines = []

        # 标题
        report_lines.append("=" * 70)
        report_lines.append("简历优化建议报告")
        report_lines.append("=" * 70)

        # 基本信息
        report_lines.append(f"\n📄 分析时间: {self._get_current_time()}")
        report_lines.append(f"🎯 目标职位: {job_title}")

        # 简历评估
        report_lines.append(f"\n📊 简历评估:")
        report_lines.append(f"   - 个人总结: {assessment['summary_len']}字 {'✅' if assessment['summary_len'] >= 60 else '⚠️'}")
        report_lines.append(f"   - 工作经验: {assessment['work_count']}条 {'✅' if assessment['work_count'] >= 2 else '⚠️'}")
        report_lines.append(f"   - 技能数量: {assessment['skill_count']}个 {'✅' if assessment['skill_count'] >= 6 else '⚠️'}")
        report_lines.append(f"   - 项目经验: {assessment['project_count']}个 {'✅' if assessment['project_count'] >= 2 else '⚠️'}")

        # 总体评价
        report_lines.append(f"\n📝 总体评价:")
        report_lines.append(f"   您的简历内容已比较完整，以下是针对{job_title}职位的优化建议。")

        # 优化建议
        report_lines.append(f"\n" + "=" * 70)
        report_lines.append("💡 优化建议")
        report_lines.append("=" * 70)

        if suggestions:
            # 按优先级排序
            suggestions.sort(key=lambda x: x.get('priority', 0), reverse=True)

            for i, s in enumerate(suggestions, 1):
                priority_star = "⭐" * s.get('priority', 3)
                report_lines.append(f"\n{i}. [{s.get('section', '通用')}] {priority_star} (优先级: {s.get('priority', 3)}/5)")
                report_lines.append(f"   📌 问题: {s.get('issue', '')}")
                report_lines.append(f"   💡 建议: {s.get('suggestion', '')}")
                if s.get('example'):
                    report_lines.append(f"   📝 示例: {s.get('example')}")
        else:
            report_lines.append("\n   未生成具体建议，您的简历已经很优秀！")

        # 结束语
        report_lines.append(f"\n" + "=" * 70)
        report_lines.append("✅ 分析完成")
        report_lines.append("=" * 70)
        report_lines.append("\n📌 温馨提示:")
        report_lines.append("   - 以上建议仅供参考，请根据实际情况选择性采纳")
        report_lines.append("   - 您的原始简历未被修改，请放心")

        return '\n'.join(report_lines)

    def _build_full_report(self, state: ResumeState,
                           suggestions: List[dict],
                           job_title: str,
                           assessment: dict) -> str:
        """构建完整报告（含原文）- 用于需要改进的简历"""
        report_lines = []

        # 标题
        report_lines.append("=" * 70)
        report_lines.append("简历优化分析报告")
        report_lines.append("=" * 70)

        # 基本信息
        report_lines.append(f"\n📄 分析时间: {self._get_current_time()}")
        report_lines.append(f"🎯 目标职位: {job_title}")

        # 评估
        report_lines.append(f"\n📊 简历评估:")
        report_lines.append(f"   - 个人总结: {assessment['summary_len']}字")
        report_lines.append(f"   - 工作经验: {assessment['work_count']}条")
        report_lines.append(f"   - 技能数量: {assessment['skill_count']}个")
        report_lines.append(f"   - 项目经验: {assessment['project_count']}个")

        # 改进建议
        report_lines.append(f"\n" + "=" * 70)
        report_lines.append("💡 优化建议")
        report_lines.append("=" * 70)

        if suggestions:
            suggestions.sort(key=lambda x: x.get('priority', 0), reverse=True)

            for i, s in enumerate(suggestions, 1):
                report_lines.append(f"\n{i}. [{s.get('section', '通用')}] (优先级: {s.get('priority', 3)}/5)")
                report_lines.append(f"   问题: {s.get('issue', '')}")
                report_lines.append(f"   建议: {s.get('suggestion', '')}")
                if s.get('example'):
                    report_lines.append(f"   示例: {s.get('example')}")
        else:
            report_lines.append("\n   未生成具体建议")

        # 原始简历（供参考）
        report_lines.append(f"\n" + "=" * 70)
        report_lines.append("📄 原始简历（供参考修改）")
        report_lines.append("=" * 70)
        report_lines.append(state['original_resume'])

        report_lines.append(f"\n" + "=" * 70)
        report_lines.append("✅ 分析完成")
        report_lines.append("=" * 70)

        return '\n'.join(report_lines)

    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")