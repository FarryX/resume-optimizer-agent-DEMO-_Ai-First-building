# batch_pdf_optimize.py - 批量处理PDF简历
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.coordinator_agent import CoordinatorAgent
from skills.pdf_processor import PDFProcessor

async def batch_optimize():
    """批量处理所有PDF简历"""
    
    print("=" * 60)
    print("简历优化Agent - 批量PDF处理")
    print("=" * 60)
    
    input_folder = "resumes"
    output_folder = "optimized_results"
    
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    
    # 查找所有PDF
    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"\n📁 请在 '{input_folder}' 文件夹中放入PDF简历文件")
        print(f"   路径: {os.path.abspath(input_folder)}")
        return
    
    print(f"\n📄 找到 {len(pdf_files)} 个PDF文件")
    print("=" * 60)
    
    agent = CoordinatorAgent()
    results = []
    
    # 询问是否统一职位或分别设置
    print("\n请选择职位设置方式:")
    print("1. 所有简历使用相同职位")
    print("2. 分别为每个简历设置职位")
    
    mode = input("请选择 (1/2): ").strip()
    
    common_job = None
    common_edu = None
    
    if mode == "1":
        common_job = input("目标职位: ").strip()
        common_edu = input("教育背景: ").strip()
        if not common_job:
            common_job = "软件工程师"
        if not common_edu:
            common_edu = "本科"
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] 处理: {pdf_file}")
        
        # 读取PDF
        pdf_path = os.path.join(input_folder, pdf_file)
        try:
            resume_text = PDFProcessor.read_pdf(pdf_path)
            if not resume_text.strip():
                print(f"  ⚠️  PDF中未提取到文本，跳过")
                continue
            print(f"  ✅ 读取成功，{len(resume_text)} 字符")
        except Exception as e:
            print(f"  ❌ 读取失败: {e}")
            continue
        
        # 获取职位信息
        if mode == "1":
            job_title = common_job
            education = common_edu
        else:
            print(f"  📝 请为 {pdf_file} 设置:")
            job_title = input(f"     目标职位: ").strip()
            education = input(f"     教育背景: ").strip()
            if not job_title:
                job_title = "软件工程师"
            if not education:
                education = "本科"
        
        # 优化
        print(f"  🔄 优化中...")
        result = await agent.optimize_resume(
            original_resume=resume_text,
            target_job=job_title,
            education=education
        )
        
        if result.get('success'):
            # 保存PDF
            output_name = f"优化_{pdf_file.replace('.pdf', '')}.pdf"
            output_path = os.path.join(output_folder, output_name)
            
            try:
                PDFProcessor.save_to_pdf(result['final_resume'], output_path)
                results.append({
                    'file': pdf_file,
                    'score': result.get('ats_score', 0),
                    'match_rate': result.get('match_rate', 0),
                    'output': output_path
                })
                print(f"  ✅ 完成！ATS评分: {result.get('ats_score', 0)}/100")
            except Exception as e:
                print(f"  ⚠️ PDF保存失败: {e}")
                # 保存为TXT
                txt_path = output_path.replace('.pdf', '.txt')
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(result['final_resume'])
                results.append({
                    'file': pdf_file,
                    'score': result.get('ats_score', 0),
                    'match_rate': result.get('match_rate', 0),
                    'output': txt_path
                })
                print(f"  ✅ 已保存为TXT")
        else:
            print(f"  ❌ 优化失败: {result.get('error')}")
    
    # 显示汇总报告
    print("\n" + "=" * 60)
    print("批量处理完成")
    print("=" * 60)
    
    if results:
        print("\n📊 处理结果汇总:")
        print("-" * 40)
        for r in results:
            print(f"  {r['file']}")
            print(f"    ATS评分: {r['score']}/100")
            print(f"    匹配率: {r['match_rate']:.1f}%")
            print(f"    输出: {os.path.basename(r['output'])}")
        
        avg_score = sum(r['score'] for r in results) / len(results)
        print("-" * 40)
        print(f"  平均ATS评分: {avg_score:.1f}/100")
        print(f"  成功处理: {len(results)}/{len(pdf_files)}")
        
    print(f"\n📁 结果保存在: {os.path.abspath(output_folder)}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(batch_optimize())