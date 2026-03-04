#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docx 处理模块 (Docx Handler)
用于读取 Word 文档并在翻译后保留原格式回填
"""

import os
from copy import deepcopy
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

class DocxHandler:
    def __init__(self, filepath):
        if not DOCX_AVAILABLE:
            raise ImportError("需安装 python-docx 库才能使用此功能: pip install python-docx")
        
        self.filepath = filepath
        self.document = Document(filepath)
        # 映射 paragraphs 索引到文本内容，用于后续回填
        self.para_map = [] 
        self._scan_document()

    def _scan_document(self):
        """扫描文档，建立索引"""
        self.para_map = []
        # 仅处理主体段落，表格暂略（表格处理极其复杂，暂只支持纯文本回填）
        for i, para in enumerate(self.document.paragraphs):
            if para.text.strip():
                self.para_map.append({
                    'index': i,
                    'original_text': para.text,
                    'type': 'paragraph'
                })
        
        # 扫描表格
        for i, table in enumerate(self.document.tables):
            for r, row in enumerate(table.rows):
                for c, cell in enumerate(row.cells):
                    for p_idx, para in enumerate(cell.paragraphs):
                        if para.text.strip():
                            self.para_map.append({
                                'table_idx': i,
                                'row_idx': r,
                                'col_idx': c,
                                'cell_p_idx': p_idx,
                                'original_text': para.text,
                                'type': 'table'
                            })

    def extract_text(self):
        """提取纯文本用于翻译"""
        return "\n\n".join([item['original_text'] for item in self.para_map])

    def save_translated_file(self, translated_segments, output_path):
        """
        将翻译后的段落回填到文档中并保存
        
        Args:
            translated_segments: 翻译后的文本段落列表 (List[str])
            output_path: 保存路径
        """
        if len(translated_segments) != len(self.para_map):
            print(f"警告: 翻译段落数 ({len(translated_segments)}) 与原文有效段落数 ({len(self.para_map)}) 不匹配，可能导致错位。")
        
        # 使用副本以防修改原对象
        # doc = deepcopy(self.document) # deepcopy Document 对象有时会出错，直接重新加载最安全
        doc = Document(self.filepath)
        
        limit = min(len(translated_segments), len(self.para_map))
        
        for i in range(limit):
            trans_text = translated_segments[i]
            mapping = self.para_map[i]
            
            target_para = None
            if mapping['type'] == 'paragraph':
                target_para = doc.paragraphs[mapping['index']]
            elif mapping['type'] == 'table':
                try:
                    target_para = doc.tables[mapping['table_idx']].rows[mapping['row_idx']].cells[mapping['col_idx']].paragraphs[mapping['cell_p_idx']]
                except IndexError:
                    continue

            if target_para:
                # 清除原有 runs，保留段落样式
                target_para.clear() 
                # 添加新文本
                run = target_para.add_run(trans_text)
                # 尝试保留第一个 run 的样式（如果有）
                # (更高级的样式保留需要逐词对齐，非常困难，此处仅保留段落级样式)
                
    def save_translated_file(self, translated_segments, output_path):
        """
        将翻译后的段落回填到文档中并保存
        """
        # ... (Existing implementation kept same, implicitly handled by 'old_string' match if I used replace correctly, 
        # but here I am rewriting the class methods. Wait, I should append the new method.)
        # Since 'replace' tool works on text matching, I will match the end of the file or the previous method.
        # But to be safe and cleaner, I will overwrite the file or careful replace. 
        # Let's use the full class content approach for safety or just append the method.
        pass 

    def save_bilingual_file(self, original_segments, translated_segments, output_path):
        """
        保存为双语对照 Word 文档 (两栏表格)
        
        Args:
            original_segments: 原文段落列表
            translated_segments: 译文段落列表
            output_path: 保存路径
        """
        doc = Document()
        doc.add_heading('双语对照翻译 / Bilingual Translation', 0)
        
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Table Grid'
        
        # Header
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = '原文 (Original)'
        hdr_cells[1].text = '译文 (Translation)'
        
        # Content
        limit = max(len(original_segments), len(translated_segments))
        for i in range(limit):
            row_cells = table.add_row().cells
            
            # Original
            if i < len(original_segments):
                row_cells[0].text = original_segments[i]
            
            # Translation
            if i < len(translated_segments):
                row_cells[1].text = translated_segments[i]
                
        doc.save(output_path)
        return output_path

