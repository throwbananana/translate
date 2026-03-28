#! python
# -*- coding: utf-8 -*-
"""
成本估算模块 (Cost Estimator)
根据字符数/Token数和模型定价估算翻译成本
"""

import math
import re

class CostEstimator:
    # 定价表 (单位: USD per 1M tokens) - 截至 2024/2025 参考价
    PRICING = {
        'gemini-2.5-flash': {'input': 0.10, 'output': 0.40}, # 假设值
        'gemini-2.5-pro': {'input': 1.25, 'output': 5.00},
        'gemini-1.5-flash': {'input': 0.075, 'output': 0.30},
        'gemini-1.5-pro': {'input': 1.25, 'output': 5.00},
        'gpt-3.5-turbo': {'input': 0.50, 'output': 1.50},
        'gpt-4o': {'input': 2.50, 'output': 10.00},
        'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
        'claude-3-haiku': {'input': 0.25, 'output': 1.25},
        'claude-3-sonnet': {'input': 3.00, 'output': 15.00},
        'claude-3-opus': {'input': 15.00, 'output': 75.00},
        'deepseek-chat': {'input': 0.14, 'output': 0.28}, # 假设值
        'lm_studio': {'input': 0, 'output': 0} # 本地免费
    }

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        简易 Token 估算
        中文：约 0.6-0.8 chars/token -> 1 char ≈ 1.5 tokens (保守)
        英文：约 4 chars/token -> 1 char ≈ 0.25 tokens
        这里使用保守混合估算法
        """
        if not text:
            return 0
            
        # 统计中文字符
        zh_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        # 统计其他字符
        other_chars = len(text) - zh_chars
        
        # 估算公式
        total_tokens = int(zh_chars * 1.5 + other_chars * 0.3)
        return total_tokens

    @classmethod
    def calculate_cost(cls, model_name: str, text: str) -> dict:
        """
        计算预计成本
        
        Returns:
            {
                'input_tokens': int,
                'output_tokens': int,
                'total_tokens': int,
                'cost_usd': float,
                'currency': str
            }
        """
        input_tokens = cls.estimate_tokens(text)
        # 假设输出长度是输入的 1.2 倍 (翻译通常会变长一点，特别是中译英)
        # 或者 0.8 倍 (英译中)
        # 这里取 1.0 作为平均参考
        output_tokens = input_tokens 
        
        # 模糊匹配模型价格
        price = {'input': 0, 'output': 0}
        model_lower = model_name.lower()
        
        found_model = "unknown"
        for key, val in cls.PRICING.items():
            if key in model_lower:
                price = val
                found_model = key
                break
                
        total_cost = (input_tokens / 1_000_000 * price['input']) + \
                     (output_tokens / 1_000_000 * price['output'])
                     
        return {
            'input_tokens': input_tokens,
            'estimated_output_tokens': output_tokens,
            'total_estimated_tokens': input_tokens + output_tokens,
            'cost_usd': round(total_cost, 4),
            'matched_model': found_model
        }
