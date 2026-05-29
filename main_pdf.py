# main_pdf.py
# 简历优化分析工具 - 支持PDF/TXT输入，只输出分析报告和优化建议

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.coordinator_agent import CoordinatorAgent
from skills.pdf_processor import PDFProcessor


def read_resume_file(file_path: str) -> str:
    """读取简历文件，支持TXT和PDF"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.pdf':
        return PDFProcessor.read_pdf(file_path)
    elif ext in ['.txt', '.md']:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        raise Exception(f"不支持的文件格式: {ext}，请使用 .txt, .md 或 .pdf")


async def main():
    print("=" * 60)
    print("简历优化Agent - 智能分析模式")
    print("=" * 60)
    print("\n📌 重要说明：")
    print("   - 本工具【不会修改】您的原始简历")
    print("   - 只提供优化建议，由您自行决定是否采纳")
    print("   - 当简历足够详细时，只输出建议，不重复打印原文")
    print("=" * 60)

    # 创建文件夹
    input_folder = "resumes"
    output_folder = "optimized_results"
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)

    # 查找支持的文件
    supported_ext = ['.pdf', '.txt', '.md']
    files = []
    for ext in supported_ext:
        files.extend([f for f in os.listdir(input_folder) if f.lower().endswith(ext)])

    if not files:
        print(f"\n📁 请在 '{input_folder}' 文件夹中放入简历文件")
        print(f"   支持格式: PDF, TXT, MD")
        print(f"   路径: {os.path.abspath(input_folder)}")
        print("\n示例:")
        print("   1. 将简历文件放入 resumes 文件夹")
        print("   2. 重新运行本程序")
        return

    print("\n📄 找到以下简历文件:")
    for i, file in enumerate(files, 1):
        file_path = os.path.join(input_folder, file)
        file_size = os.path.getsize(file_path) / 1024
        ext = os.path.splitext(file)[1].upper()
        print(f"   {i}. {file} ({ext}, {file_size:.1f} KB)")

    # 选择文件
    choice = input(f"\n请选择 (1-{len(files)}): ").strip()
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(files):
            print("选择无效")
            return
        selected_file = files[idx]
    except ValueError:
        print("选择无效")
        return

    # 读取文件
    file_path = os.path.join(input_folder, selected_file)
    print(f"\n📖 正在读取: {selected_file}")

    try:
        resume_text = read_resume_file(file_path)
        if not resume_text.strip():
            print("❌ 文件中未提取到文本内容")
            return
        print(f"✅ 成功读取，共 {len(resume_text)} 字符")

        # 显示原文预览（前300字）
        print(f"\n📝 原文预览（前300字）:")
        print("-" * 40)
        print(resume_text[:300])
        if len(resume_text) > 300:
            print("...(内容较长，已截断显示)")
        print("-" * 40)

    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return

    # 输入职位信息
    print("\n" + "-" * 40)
    job_title = input("🎯 目标职位: ").strip()
    if not job_title:
        job_title = "软件工程师"

    education = input("🎓 教育背景: ").strip()
    if not education:
        education = "本科"
    print("-" * 40)

    # 确认是否继续
    print(f"\n⚠️  本工具不会修改您的原始简历，只生成优化建议")
    confirm = input("是否继续? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return

    # 分析简历
    print("\n🔄 正在分析简历...")
    agent = CoordinatorAgent()

    result = await agent.optimize_resume(
        original_resume=resume_text,
        target_job=job_title,
        education=education
    )

    if result is None:
        print("❌ 分析失败：未返回结果")
        return

    # 处理分析结果
    if result.get('success'):
        # 确定输出文件名
        base_name = os.path.splitext(selected_file)[0]
        txt_output = os.path.join(output_folder, f"优化建议_{base_name}.txt")

        final_content = result.get('final_resume', '')

        # 保存报告
        with open(txt_output, 'w', encoding='utf-8') as f:
            f.write(final_content)

        print(f"\n✅ 分析完成！")
        print(f"   ATS评分: {result.get('ats_score', 0)}/100")
        print(f"   关键词匹配率: {result.get('match_rate', 0):.1f}%")

        # 显示模式
        mode = result.get('optimization_mode', 'unknown')
        suggestions = result.get('optimization_suggestions', [])

        if mode == 'suggestions_only':
            print(f"\n📌 模式: 您的简历已足够详细")
            print(f"   💡 仅生成优化建议（不含原文）")
            print(f"   📁 建议报告: {txt_output}")
            print(f"   ✅ 您的原始简历未被修改，请放心")
        else:
            print(f"\n📌 模式: 简历需要改进")
            print(f"   💡 已生成优化建议和原文参考")
            print(f"   📁 报告保存: {txt_output}")

        # 显示建议数量
        if suggestions:
            print(f"\n💡 建议数量: {len(suggestions)}条")

            # 按优先级排序显示前3条
            suggestions_sorted = sorted(suggestions, key=lambda x: x.get('priority', 0), reverse=True)
            print(f"\n📋 主要建议预览:")
            for i, s in enumerate(suggestions_sorted[:3], 1):
                priority_star = "⭐" * s.get('priority', 3)
                print(f"\n   {i}. [{s.get('section', '通用')}] {priority_star}")
                print(f"      {s.get('suggestion', '')[:100]}...")
        else:
            print(f"\n💡 未生成具体建议，您的简历质量很好！")

        # 显示优化日志
        logs = result.get('optimization_log', [])
        if logs:
            print(f"\n📋 处理日志:")
            for log in logs[:3]:
                print(f"   - {log}")

        print(f"\n📁 详细报告已保存至: {os.path.abspath(output_folder)}")
        print(f"   请打开文件查看完整内容")

        # 验证原文未被修改
        if result.get('final_resume') != resume_text and mode == 'suggestions_only':
            print(f"\n⚠️  注意: 报告文件不含原文，原文保存在原文件中")

    else:
        error_msg = result.get('error', '未知错误')
        print(f"\n❌ 分析失败: {error_msg}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
