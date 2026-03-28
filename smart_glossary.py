#! python
# -*- coding: utf-8 -*-
"""
智能术语提取模块 (Smart Glossary)
利用 LLM 分析文本并提取专有名词
"""

import json
import re

class SmartGlossaryExtractor:
    def __init__(self, translation_engine):
        self.engine = translation_engine

    def extract_terms(self, text, api_type='gemini'):
        """
        提取文本中的术语
        
        Args:
            text: 待分析文本
            api_type: 使用的 API 类型 (deprecated, uses engine's current)
            
        Returns:
            List[Tuple[str, str, str]]: [(原文, 建议译文, 类型), ...]
        """
        # 截取前 4000 字，包含足够的上下文
        snippet = text[:4000]
        
        system_prompt = """
        You are a professional terminology extraction tool.
        Analyze the following text and extract key proper nouns (People, Places, Organizations, Special Terms) that appear frequently or seem important.
        
        Output format: JSON Array ONLY. No markdown, no explanations.
        Example:
        [
            {"term": "Harry Potter", "translation": "哈利·波特", "type": "Person"},
            {"term": "Hogwarts", "translation": "霍格沃茨", "type": "Location"}
        ]
        
        Requirements:
        1. "translation": Provide a standard Chinese translation.
        2. "type": One of [Person, Location, Org, Term].
        3. Extract at most 20 most important terms.
        """
        
        try:
            # 这里的技巧是：我们告诉引擎“翻译”这段文本，但通过 extra_prompt 覆盖指令
            # 我们把 snippet 放在 user prompt 位置
            
            # 构造一个特殊的 Prompt
            # 注意：TranslationEngine 默认会加 "请翻译..."
            # 我们通过 hack 方式：让 engine 以为它在翻译，但 system prompt 强行扭转
            
            override = "IGNORE PREVIOUS TRANSLATION INSTRUCTIONS. " + system_prompt
            
            # 暂存旧的 provider 配置 (如果需要特定 model)
            # 这里直接使用 engine 当前的默认配置
            
            result = self.engine.translate(
                text=snippet,
                target_lang="JSON", # 这里的 target_lang 只是给 prompt 用的，实际上我们在 extra_prompt 里指定了 JSON
                extra_prompt=override,
                use_memory=False,
                use_glossary=False
            )
            
            if not result.success:
                print(f"术语提取失败: {result.error}")
                return []
                
            return self.parse_response(result.translated_text)
            
        except Exception as e:
            print(f"术语提取出错: {e}")
            return []
        
    def parse_response(self, response_text):
        """解析 LLM 返回的 JSON"""
        try:
            # 清理 markdown
            text = re.sub(r'```json\s*', '', response_text)
            text = re.sub(r'```', '', text)
            
            # 提取 JSON 数组部分
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                json_str = match.group(0)
                data = json.loads(json_str)
                
                # 转换为 List[Tuple]
                results = []
                for item in data:
                    term = item.get('term')
                    trans = item.get('translation')
                    type_ = item.get('type', 'Term')
                    if term and trans:
                        results.append((term, trans, type_))
                return results
            return []
        except Exception as e:
            print(f"JSON 解析失败: {e}")
            return []
