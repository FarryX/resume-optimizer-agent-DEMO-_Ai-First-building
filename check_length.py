# check_length.py - 检查优化前后的长度变化
import os
import sys

def check_length():
    """检查优化前后文件长度"""
    
    original_file = input("请输入原文文件路径: ").strip()
    optimized_file = input("请输入优化后文件路径: ").strip()
    
    if not os.path.exists(original_file):
        print("原文文件不存在")
        return
    
    if not os.path.exists(optimized_file):
        print("优化文件不存在")
        return
    
    with open(original_file, 'r', encoding='utf-8') as f:
        original = f.read()
    
    with open(optimized_file, 'r', encoding='utf-8') as f:
        optimized = f.read()
    
    original_len = len(original)
    optimized_len = len(optimized)
    change = optimized_len - original_len
    change_percent = (change / original_len) * 100
    
    print("\n" + "=" * 50)
    print("长度对比报告")
    print("=" * 50)
    print(f"原文长度: {original_len} 字")
    print(f"优化后长度: {optimized_len} 字")
    print(f"变化: {'+' if change > 0 else ''}{change} 字 ({change_percent:+.1f}%)")
    
    if change < 0:
        print("\n⚠️ 警告：内容被缩短了！")
        print("建议：检查优化逻辑，确保保留原文")
    else:
        print("\n✅ 内容长度正常，未丢失信息")

if __name__ == "__main__":
    check_length()