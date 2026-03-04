#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Importer Module
用于从 URL 提取正文内容
"""

import requests
from bs4 import BeautifulSoup
import re

class WebImporter:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch_content(self, url):
        """
        从 URL 抓取并提取正文
        
        Returns:
            title (str), content (str)
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            # 自动检测编码
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. 提取标题
            title = ""
            if soup.title:
                title = soup.title.string.strip()
            if not title:
                h1 = soup.find('h1')
                if h1:
                    title = h1.get_text(strip=True)
            
            # 2. 移除干扰元素
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript']):
                tag.decompose()
                
            # 3. 提取正文 (简单启发式)
            # 优先寻找 article 标签
            article = soup.find('article')
            if article:
                content_node = article
            else:
                # 寻找包含最多 p 标签的 div
                max_p = 0
                best_div = None
                for div in soup.find_all('div'):
                    p_count = len(div.find_all('p', recursive=False))
                    if p_count > max_p:
                        max_p = p_count
                        best_div = div
                
                content_node = best_div if best_div else soup.body

            # 4. 提取文本
            text_parts = []
            if content_node:
                for p in content_node.find_all(['p', 'h2', 'h3', 'h4', 'li']):
                    txt = p.get_text(strip=True)
                    if len(txt) > 5: # 忽略太短的
                        text_parts.append(txt)
            
            full_text = "\n\n".join(text_parts)
            
            if not full_text:
                raise ValueError("未能提取到有效正文")
                
            return title, full_text

        except Exception as e:
            raise Exception(f"网页抓取失败: {str(e)}")
