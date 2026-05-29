import asyncio
from llm_client import deepseek_client

async def init_rag():
    """初始化RAG知识库"""
    print("初始化RAG知识库...")
    deepseek_client.initialize_default_knowledge_base()
    print("RAG知识库初始化完成！")
    print("\n知识库内容：")
    print("- job_skills: 职位技能映射（6条）")
    print("- best_practices: 简历最佳实践（5条）")
    print("\n现在可以运行 main.py 体验RAG增强功能")

if __name__ == "__main__":
    asyncio.run(init_rag())