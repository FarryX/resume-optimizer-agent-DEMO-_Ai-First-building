# llm_client.py - 简化版，无RAG
import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any, List
from config import DeepSeekConfig
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeepSeekClient:
    """DeepSeek API客户端 - 简化版"""
    
    def __init__(self):
        self.api_key = DeepSeekConfig.API_KEY
        self.api_base = DeepSeekConfig.API_BASE
        self.model = DeepSeekConfig.MODEL_NAME
        self.temperature = DeepSeekConfig.TEMPERATURE
        self.max_tokens = DeepSeekConfig.MAX_TOKENS
        
        self.token_usage = {
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cost': 0.0,
            'call_count': 0
        }
        
        DeepSeekConfig.validate()
    
    def estimate_tokens(self, text: str) -> int:
        """估算token数量"""
        if not text:
            return 0
        return len(text) // 1.5
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """截断文本"""
        estimated = self.estimate_tokens(text)
        if estimated <= max_tokens:
            return text
        ratio = max_tokens / estimated
        new_length = int(len(text) * ratio)
        return text[:new_length]
    
    async def chat_completion(self, 
                             messages: List[Dict[str, str]],
                             temperature: Optional[float] = None,
                             max_tokens: Optional[int] = None,
                             max_input_tokens: int = 800) -> str:
        """调用DeepSeek API"""
        
        # 截断输入
        truncated_messages = []
        for msg in messages:
            if msg['role'] == 'user':
                msg['content'] = self.truncate_to_tokens(msg['content'], max_input_tokens)
            truncated_messages.append(msg)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        output_limit = min(max_tokens or self.max_tokens, 500)
        
        payload = {
            "model": self.model,
            "messages": truncated_messages,
            "temperature": temperature or self.temperature,
            "max_tokens": output_limit,
            "stream": False
        }
        
        input_text = ' '.join([m['content'] for m in truncated_messages])
        input_tokens = self.estimate_tokens(input_text)
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            for attempt in range(DeepSeekConfig.MAX_RETRIES):
                try:
                    async with session.post(
                        f"{self.api_base}/chat/completions",
                        headers=headers,
                        json=payload
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            output_text = result['choices'][0]['message']['content']
                            output_tokens = self.estimate_tokens(output_text)
                            
                            # 统计
                            self.token_usage['total_input_tokens'] += input_tokens
                            self.token_usage['total_output_tokens'] += output_tokens
                            self.token_usage['call_count'] += 1
                            
                            input_cost = input_tokens * 0.001 / 1000
                            output_cost = output_tokens * 0.002 / 1000
                            self.token_usage['total_cost'] += input_cost + output_cost
                            
                            elapsed = time.time() - start_time
                            logger.info(f"LLM调用 | 输入:{input_tokens} | 输出:{output_tokens} | 耗时:{elapsed:.2f}s")
                            
                            return output_text
                        else:
                            error_text = await response.text()
                            logger.error(f"API错误 {response.status}: {error_text}")
                            
                            if response.status == 401:
                                raise Exception("API密钥无效")
                            elif response.status == 429:
                                await asyncio.sleep(DeepSeekConfig.RETRY_DELAY * (attempt + 1))
                                continue
                            else:
                                raise Exception(f"API请求失败: {error_text}")
                                
                except aiohttp.ClientError as e:
                    logger.error(f"网络错误 (尝试 {attempt + 1}): {e}")
                    if attempt < DeepSeekConfig.MAX_RETRIES - 1:
                        await asyncio.sleep(DeepSeekConfig.RETRY_DELAY * (attempt + 1))
                    else:
                        raise Exception(f"网络连接失败: {e}")
                        
            raise Exception("达到最大重试次数")
    
    def get_token_stats(self) -> dict:
        """获取Token统计"""
        return {
            'call_count': self.token_usage['call_count'],
            'total_input_tokens': self.token_usage['total_input_tokens'],
            'total_output_tokens': self.token_usage['total_output_tokens'],
            'total_tokens': self.token_usage['total_input_tokens'] + self.token_usage['total_output_tokens'],
            'total_cost': self.token_usage['total_cost'],
            'avg_cost_per_call': self.token_usage['total_cost'] / max(self.token_usage['call_count'], 1)
        }
    
    async def optimize_text(self, prompt: str, context: Dict[str, Any], max_tokens: int = 300) -> str:
        """优化文本"""
        try:
            formatted_prompt = prompt.format(**context)
        except KeyError:
            formatted_prompt = prompt
        
        formatted_prompt = self.truncate_to_tokens(formatted_prompt, 600)
        
        messages = [
            {"role": "system", "content": "你是简历优化专家。只输出结果。"},
            {"role": "user", "content": formatted_prompt}
        ]
        
        try:
            response = await self.chat_completion(messages, max_tokens=max_tokens)
            return response.strip()
        except Exception as e:
            logger.error(f"优化失败: {e}")
            return context.get('content', '')
    
    async def analyze_resume(self, resume_content: str, job_title: str) -> Dict[str, Any]:
        """分析简历 - 简化版"""
        
        truncated_resume = self.truncate_to_tokens(resume_content, 500)
        
        prompt = f"分析简历与{job_title}的匹配度。简历：{truncated_resume}。输出优势、待改进、关键词。"
        
        messages = [
            {"role": "system", "content": "你是HR专家。简短输出。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.chat_completion(messages, max_tokens=300)
            
            analysis = {
                'raw_analysis': response,
                'strengths': [],
                'weaknesses': [],
                'keywords': [],
                'ats_suggestions': []
            }
            
            lines = response.split('\n')
            for line in lines[:15]:
                if '优势' in line or 'strength' in line.lower():
                    if len(analysis['strengths']) < 3:
                        analysis['strengths'].append(line.strip(' -•*')[:50])
                elif '待改进' in line or 'weakness' in line.lower():
                    if len(analysis['weaknesses']) < 3:
                        analysis['weaknesses'].append(line.strip(' -•*')[:50])
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析失败: {e}")
            return {
                'error': str(e),
                'strengths': [],
                'weaknesses': [],
                'keywords': [],
                'ats_suggestions': []
            }


# 全局客户端
deepseek_client = DeepSeekClient()