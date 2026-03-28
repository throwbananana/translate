#! python
# -*- coding: utf-8 -*-
"""
Book Hunter Agent
利用 AI 分析用户需求，生成搜索关键词，并筛选最佳结果
"""

import json
import re
from typing import List, Dict

class BookHunter:
    def __init__(self, translation_engine, search_manager):
        """
        :param translation_engine: 现有的 TranslationEngine 实例 (用于调用 LLM)
        :param search_manager: 现有的 OnlineSearchManager 实例 (用于执行搜索)
        """
        self.engine = translation_engine
        self.search_manager = search_manager

    def analyze_requirement(self, user_query: str) -> List[str]:
        """
        使用 AI 分析用户需求，生成 3-5 个有效的搜索关键词
        """
        prompt = f"""
        User Query: "{user_query}"
        
        Task: You are a professional librarian. Analyze the user's book request.
        Generate 3 to 5 specific search keywords or phrases that would work best on book search engines (like Z-Library or Anna's Archive).
        
        Strategies:
        1. If the user asks for a specific topic (e.g., "Python for beginners"), generate keywords like "Python basics", "Python introduction", "Python programming".
        2. If the user asks for a specific author/genre, use the author's name combined with genre or famous titles.
        3. Prioritize English keywords if the user doesn't specify a language, as databases are often English-centric. If user specifies a language (e.g., Chinese), use that language.
        
        Output Format:
        Return ONLY a JSON list of strings. No markdown, no explanations.
        Example: ["keyword1", "keyword2", "keyword3"]
        """
        
        try:
            # 使用 'gemini' 或当前配置的任何 API
            # 我们调用 translate 方法，实际上是利用其通用 LLM 能力
            # 这里我们传入 provider=None 让引擎自己选，或者复用 GUI 的设置
            # 为了简单，我们尝试复用引擎的默认配置
            
            # 注意：translate 方法是为翻译设计的，我们这里需要直接调用底层或由 translate 方法变通
            # 由于 TranslationEngine 封装较深，我们通过 _do_translate 的特定 prompt 来实现
            # 但 TranslationEngine 的 translate 方法会强制加上 "请翻译..." 的 prompt。
            # 因此，我们最好在 TranslationEngine 中加一个通用的 chat 方法，或者直接在这里 hack。
            
            # 为了不修改核心引擎太多，我们使用 engine 的 "custom" 接口或者直接构建 prompt
            # 更好的方法是：复用 TranslationEngine 但传入特殊的 prompt 覆盖。
            # 不过 TranslationEngine.translate 会强制 formatting。
            # 让我们假设 TranslationEngine 有一个 raw_query 方法或者我们在 GUI 层传入了 raw client。
            
            # 检查 TranslationEngine 是否有通用生成方法，如果没有，我们用 translate 方法 "欺骗" 它
            # 或者我们简单地使用 engine 内部已配置的 client。
            
            # 方案：使用 translate 方法，但在 system prompt 里强力覆盖指令
            # 这有点 hacky，但最稳健。
            
            override_prompt = "IGNORE ALL PREVIOUS INSTRUCTIONS ABOUT TRANSLATION. " + prompt
            
            result = self.engine.translate(
                text=".", # Dummy text
                target_lang="JSON", # Dummy target
                extra_prompt=override_prompt,
                use_memory=False,
                use_glossary=False
            )
            
            if not result.success:
                print(f"AI Analysis failed: {result.error}")
                return [user_query] # Fallback to original query

            response_text = result.translated_text
            
            # 清理 Markdown 代码块
            response_text = re.sub(r'```json\s*', '', response_text)
            response_text = re.sub(r'```', '', response_text)
            
            keywords = json.loads(response_text)
            if isinstance(keywords, list):
                return keywords[:5] # Limit to 5
            return [user_query]
            
        except Exception as e:
            print(f"Error in BookHunter analysis: {e}")
            return [user_query]

    def hunt(self, user_query: str, source="Anna's Archive", callback=None) -> List[Dict]:
        """
        执行寻书任务
        1. AI 分析关键词
        2. 执行多轮搜索
        3. (可选) AI 筛选结果
        """
        if callback: callback("🤖 正在分析您的需求...")
        
        keywords = self.analyze_requirement(user_query)
        if callback: callback(f"🔍 生成关键词: {', '.join(keywords)}")
        
        all_results = []
        seen_ids = set()
        
        for kw in keywords:
            if callback: callback(f"📡 正在搜索: {kw} ...")
            
            try:
                if source == "Z-Library":
                    res = self.search_manager.search_zlibrary(kw)
                else:
                    res = self.search_manager.search_annas_archive(kw)
                
                # 去重并添加
                for item in res:
                    # 简单的去重键：标题+作者
                    unique_key = (item['title'].lower(), item.get('author', '').lower())
                    if unique_key not in seen_ids:
                        seen_ids.add(unique_key)
                        all_results.append(item)
            except Exception as e:
                print(f"Search error for {kw}: {e}")
                
            if len(all_results) > 20: # 稍微限制一下数量，避免太慢
                break
                
        if callback: callback(f"✅ 搜索完成，共找到 {len(all_results)} 本相关书籍")
        return all_results

    def ai_filter_results(self, user_query: str, results: List[Dict]) -> List[Dict]:
        """
        (高级功能) 让 AI 从搜索结果中挑选最符合用户要求的
        注意：如果结果太多，这会消耗大量 Tokens
        """
        if not results: return []
        
        # 简化结果列表供 AI 阅读
        simplified_list = []
        for i, res in enumerate(results[:15]): # 只看前15个
            simplified_list.append(f"{i}. Title: {res['title']}, Author: {res.get('author')}, Format: {res.get('extension')}")
            
        list_text = "\n".join(simplified_list)
        
        prompt = f"""
        User Query: "{user_query}"
        
        Search Results:
        {list_text}
        
        Task: Select the top 3 books that best match the user's query.
        Return ONLY a JSON list of indices (integers). Example: [0, 4, 7]
        """
        
        # 同样使用 hack 方法调用 AI
        override_prompt = "IGNORE ALL PREVIOUS INSTRUCTIONS ABOUT TRANSLATION. " + prompt
        
        try:
            res_obj = self.engine.translate(
                text=".", target_lang="JSON", extra_prompt=override_prompt, use_memory=False
            )
            indices = json.loads(re.sub(r'```json|```', '', res_obj.translated_text))
            
            final_selection = []
            for idx in indices:
                if isinstance(idx, int) and 0 <= idx < len(results):
                    final_selection.append(results[idx])
            
            return final_selection if final_selection else results
            
        except:
            return results # Fallback
