#! python
# -*- coding: utf-8 -*-
"""
涔︾睄缈昏瘧宸ュ叿 GUI v2.3.1
鏀寔PDF銆乀XT銆丒PUB銆丏OCX銆丮arkdown鏍煎紡鐨勪功绫嶇炕璇?
鍙帴鍏emini API銆丱penAI API銆丆laude API銆丏eepSeek API绛夊绉嶇炕璇慉PI
鏀寔鍔ㄦ€佹坊鍔犲涓湰鍦版ā鍨嬶紝缈昏瘧涓庤В鏋愬姛鑳藉彲鐙珛閫夋嫨涓嶅悓API
浜戠閰嶉鑰楀敖鏃跺彲鑷姩鍒囨崲鍒版湰鍦版ā鍨?
鏂板锛氱炕璇戣蹇嗗簱锛堥伩鍏嶉噸澶嶇炕璇戯級銆佹湳璇〃绠＄悊锛堢粺涓€涓撲笟鏈锛?
v2.3 鏂板锛歅DF OCR鎵弿浠舵敮鎸?(pdfplumber+pdf2image)銆佸彲瑙嗗寲鏈琛ㄧ紪杈戙€佺珷鑺傜洰褰曞鑸€佹壒閲忎换鍔℃柇鐐圭画浼?

渚濊禆搴?
py -m pip install PyPDF2 pdfplumber pdf2image ebooklib beautifulsoup4 google-generativeai openai requests python-docx
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import threading
import sys
import os
import time
import datetime
from pathlib import Path
import re
import json
import shutil
from copy import deepcopy
import hashlib
import uuid

# 鏂囦欢璇诲彇鐩稿叧
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
    EPUB_SUPPORT = True
except ImportError:
    EPUB_SUPPORT = False

# API鐩稿叧
try:
    import google.generativeai as genai
    GEMINI_SUPPORT = True
except ImportError:
    GEMINI_SUPPORT = False

try:
    import openai
    OPENAI_SUPPORT = True
except ImportError:
    OPENAI_SUPPORT = False

try:
    import anthropic
    CLAUDE_SUPPORT = True
except ImportError:
    CLAUDE_SUPPORT = False

try:
    import requests
    REQUESTS_SUPPORT = True
except ImportError:
    REQUESTS_SUPPORT = False

from file_processor import FileProcessor
from runtime_state import RuntimeStateStore
from config_manager import ConfigManager, DEFAULT_CONFIG, get_config_manager
from retry_api_resolver import (
    choose_retry_api_name,
    map_api_name_to_key,
    validate_retry_api_selection,
)
from translation_memory import TranslationMemory, get_translation_memory
from glossary_manager import GlossaryManager, get_glossary_manager
from online_search import OnlineSearchManager
from translation_engine import (
    TranslationEngine,
    apply_runtime_config,
    build_api_config,
    resolve_provider_token,
)
from cost_estimator import CostEstimator
from docx_handler import DocxHandler
from audio_manager import AudioManager
from batch_translation_executor import BatchTranslationExecutor
from smart_glossary import SmartGlossaryExtractor
from book_hunter import BookHunter
from web_importer import WebImporter
from tm_editor import TMEditorDialog
from format_converter import FormatConverterDialog
from cloud_upload import CloudUploader
from community_manager import CommunityManager
from retry_failed_segment_service import RetryFailedSegmentService
from failed_segment_actions import FailedSegmentActions
from failed_segment_controller import FailedSegmentController
from failed_segment_feature import FailedSegmentFeature
from failed_segment_panel import FailedSegmentPanel

DEFAULT_TARGET_LANGUAGE = DEFAULT_CONFIG.get('target_language', "涓枃")
DEFAULT_LM_STUDIO_CONFIG = deepcopy(
    DEFAULT_CONFIG.get('api_configs', {}).get('lm_studio', {
        'api_key': 'lm-studio',
        'model': 'qwen2.5-7b-instruct-1m',
        'base_url': 'http://127.0.0.1:1234/v1'
    })
)

DEFAULT_API_CONFIGS = deepcopy(DEFAULT_CONFIG.get('api_configs', {}))
DEFAULT_SELECTED_TRANSLATION_API = DEFAULT_CONFIG.get('selected_translation_api', 'Gemini API')
DEFAULT_SELECTED_ANALYSIS_API = DEFAULT_CONFIG.get('selected_analysis_api', 'Gemini API')
DEFAULT_SELECTED_RETRY_API = DEFAULT_CONFIG.get('selected_retry_api', '鏈湴 LM Studio')

# 搴旂敤鐗堟湰鍙?
APP_VERSION = "2.3.1"

# 閰嶇疆鏂囦欢鐗堟湰鍙?
CONFIG_VERSION = APP_VERSION

class GlossaryEditorDialog:
    """鏈琛ㄧ紪杈戝櫒瀵硅瘽妗?""
    def __init__(self, parent, glossary_manager):
        self.parent = parent
        self.gm = glossary_manager
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("鏈琛ㄧ鐞?(Glossary Manager)")
        self.dialog.geometry("900x600")
        self.dialog.transient(parent)
        
        self.current_glossary_name = "default"
        self.setup_ui()
        self.refresh_glossary_list()
        self.load_terms()

    def setup_ui(self):
        # 椤堕儴宸ュ叿鏍?
        top_frame = ttk.Frame(self.dialog, padding=10)
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text="閫夋嫨鏈琛?").pack(side=tk.LEFT)
        self.glossary_combo = ttk.Combobox(top_frame, state="readonly", width=20)
        self.glossary_combo.pack(side=tk.LEFT, padx=5)
        self.glossary_combo.bind("<<ComboboxSelected>>", self.on_glossary_change)
        
        ttk.Button(top_frame, text="鏂板缓琛?, command=self.create_glossary).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_frame, text="鍒犻櫎琛?, command=self.delete_glossary).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(top_frame, text="鎼滅储:").pack(side=tk.LEFT, padx=(20, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.LEFT)
        self.search_entry.bind("<KeyRelease>", self.filter_terms)
        
        # 涓棿鍒楄〃鍖哄煙
        list_frame = ttk.Frame(self.dialog, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("source", "target", "notes", "category")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("source", text="鍘熸枃鏈")
        self.tree.heading("target", text="鐩爣缈昏瘧")
        self.tree.heading("notes", text="澶囨敞")
        self.tree.heading("category", text="鍒嗙被")
        
        self.tree.column("source", width=200)
        self.tree.column("target", width=200)
        self.tree.column("notes", width=200)
        self.tree.column("category", width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<Double-1>", self.edit_term)
        
        # 搴曢儴鎸夐挳鍖哄煙
        btn_frame = ttk.Frame(self.dialog, padding=10)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="娣诲姞鏈", command=self.add_term).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="缂栬緫閫変腑", command=self.edit_term).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="鍒犻櫎閫変腑", command=self.delete_term).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="鍒锋柊", command=self.load_terms).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="鍏抽棴", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def refresh_glossary_list(self):
        glossaries = self.gm.list_glossaries()
        names = [g['name'] for g in glossaries]
        if not names:
            self.gm.create_glossary("default", "榛樿鏈琛?)
            names = ["default"]
            
        self.glossary_combo['values'] = names
        if self.current_glossary_name in names:
            self.glossary_combo.set(self.current_glossary_name)
        elif names:
            self.glossary_combo.set(names[0])
            self.current_glossary_name = names[0]
            
    def on_glossary_change(self, event):
        self.current_glossary_name = self.glossary_combo.get()
        self.load_terms()
        
    def load_terms(self):
        self.tree.delete(*self.tree.get_children())
        if not self.current_glossary_name: return
        
        # 纭繚鍔犺浇
        self.gm.load_glossary(self.current_glossary_name)
        terms = self.gm.get_all_terms(self.current_glossary_name)
        
        query = self.search_var.get().lower()
        for term in terms:
            if query and (query not in term['source'].lower() and query not in term.get('target', '').lower()):
                continue
            self.tree.insert("", "end", values=(
                term['source'],
                term.get('target', ''),
                term.get('notes', ''),
                term.get('category', '')
            ))
            
    def filter_terms(self, event):
        self.load_terms()
        
    def add_term(self):
        self.edit_term_dialog(None)
        
    def edit_term(self, event=None):
        selected = self.tree.selection()
        if not selected and event is None: return
        if not selected: return # Double click on empty area
        
        item = self.tree.item(selected[0])
        values = item['values']
        self.edit_term_dialog({
            'source': values[0],
            'target': values[1],
            'notes': values[2],
            'category': values[3]
        })

    def edit_term_dialog(self, term_data):
        is_edit = term_data is not None
        title = "缂栬緫鏈" if is_edit else "娣诲姞鏈"
        
        edit_win = tk.Toplevel(self.dialog)
        edit_win.title(title)
        edit_win.geometry("400x300")
        edit_win.transient(self.dialog)
        edit_win.grab_set()
        
        frame = ttk.Frame(edit_win, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="鍘熸枃鏈:").grid(row=0, column=0, sticky=tk.W, pady=5)
        source_var = tk.StringVar(value=term_data['source'] if is_edit else "")
        source_entry = ttk.Entry(frame, textvariable=source_var, width=30)
        source_entry.grid(row=0, column=1, pady=5)
        if is_edit: source_entry.config(state='readonly') # Source is key, cannot change
        
        ttk.Label(frame, text="鐩爣缈昏瘧:").grid(row=1, column=0, sticky=tk.W, pady=5)
        target_var = tk.StringVar(value=term_data['target'] if is_edit else "")
        ttk.Entry(frame, textvariable=target_var, width=30).grid(row=1, column=1, pady=5)
        
        ttk.Label(frame, text="澶囨敞:").grid(row=2, column=0, sticky=tk.W, pady=5)
        notes_var = tk.StringVar(value=term_data['notes'] if is_edit else "")
        ttk.Entry(frame, textvariable=notes_var, width=30).grid(row=2, column=1, pady=5)
        
        ttk.Label(frame, text="鍒嗙被:").grid(row=3, column=0, sticky=tk.W, pady=5)
        cat_var = tk.StringVar(value=term_data['category'] if is_edit else "")
        ttk.Entry(frame, textvariable=cat_var, width=30).grid(row=3, column=1, pady=5)
        
        def save():
            src = source_var.get().strip()
            tgt = target_var.get().strip()
            if not src or not tgt:
                messagebox.showwarning("閿欒", "鍘熸枃鍜岃瘧鏂囦笉鑳戒负绌?)
                return
            
            if is_edit:
                self.gm.update_term(self.current_glossary_name, src, tgt, notes_var.get(), cat_var.get())
            else:
                self.gm.add_term(self.current_glossary_name, src, tgt, notes_var.get(), cat_var.get())
            
            self.load_terms()
            edit_win.destroy()
            
        ttk.Button(frame, text="淇濆瓨", command=save).grid(row=4, column=0, columnspan=2, pady=20)

    def delete_term(self):
        selected = self.tree.selection()
        if not selected: return
        
        item = self.tree.item(selected[0])
        src = item['values'][0]
        
        if messagebox.askyesno("纭", f"纭畾鍒犻櫎鏈 '{src}' 鍚?"):
            self.gm.remove_term(self.current_glossary_name, src)
            self.load_terms()

    def create_glossary(self):
        name = simpledialog.askstring("鏂板缓鏈琛?, "璇疯緭鍏ユ湳璇〃鍚嶇О (鑻辨枃/鏁板瓧):")
        if name:
            if self.gm.create_glossary(name):
                self.refresh_glossary_list()
                self.glossary_combo.set(name)
                self.on_glossary_change(None)
            else:
                messagebox.showerror("閿欒", "鍒涘缓澶辫触锛屽彲鑳藉悕绉板凡瀛樺湪")

    def delete_glossary(self):
        name = self.current_glossary_name
        if name == "default":
            messagebox.showwarning("璀﹀憡", "涓嶈兘鍒犻櫎榛樿鏈琛?)
            return
            
        if messagebox.askyesno("纭", f"纭畾鍒犻櫎鏈琛?'{name}' 鍚? 姝ゆ搷浣滀笉鍙仮澶?"):
            self.gm.delete_glossary(name)
            self.refresh_glossary_list()
            self.on_glossary_change(None)


class BookTranslatorGUI:
    """涔︾睄缈昏瘧宸ュ叿涓荤晫闈?""

    def __init__(self, root):
        self.root = root
        self.root.title(f"涔︾睄缈昏瘧宸ュ叿 v{APP_VERSION} - 缈昏瘧璁板繂+鏈琛?澶氭湰鍦版ā鍨?)
        self.root.geometry("950x750")

        # 鍒濆鍖栬緟鍔╂ā鍧?
        self.file_processor = FileProcessor()
        self.web_importer = WebImporter()
        self.runtime_state = RuntimeStateStore()

        # 鍒濆鍖栨柊妯″潡
        self.config_manager = get_config_manager()
        runtime_profile = self.config_manager.get_translation_runtime_profile()
        self.segment_size = int(runtime_profile.get('segment_size', 800) or 800)
        self.preview_limit = int(runtime_profile.get('preview_limit', 10000) or 10000)
        self.max_consecutive_failures = int(runtime_profile.get('max_consecutive_failures', 3) or 3)
        self.translation_delay = float(runtime_profile.get('translation_delay', 0.5) or 0.5)
        self.use_translation_memory = bool(runtime_profile.get('use_translation_memory', True))
        self.use_glossary = bool(runtime_profile.get('use_glossary', True))
        self.context_enabled = bool(runtime_profile.get('context_enabled', True))
        self.saved_translation_style = runtime_profile.get('translation_style', '閫氫織灏忚 (Novel)')
        self.saved_target_language = runtime_profile.get('target_language', DEFAULT_TARGET_LANGUAGE)
        self.saved_concurrency = int(runtime_profile.get('concurrency', 1) or 1)
        self.translation_memory = get_translation_memory()
        self.glossary_manager = get_glossary_manager()
        self.online_search_manager = OnlineSearchManager(self.config_manager)
        self.community_manager = CommunityManager()
        
        # 鍒濆鍖栫炕璇戝紩鎿?
        self.translation_engine = TranslationEngine()
        self.translation_engine.set_translation_memory(self.translation_memory)
        self.translation_engine.set_glossary_manager(self.glossary_manager)

        # 鍒濆鍖栨嫇灞曟ā鍧?
        self.audio_manager = AudioManager()
        self.docx_handler = None  # 浠呭湪鍔犺浇 DOCX 鏃跺垵濮嬪寲
        self.smart_glossary = SmartGlossaryExtractor(self.translation_engine)
        self.book_hunter = BookHunter(self.translation_engine, self.online_search_manager)
        self.current_theme = "light"

        # 绋嬪簭閫€鍑烘椂鑷姩淇濆瓨閰嶇疆
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 缈昏瘧鐘舵€?
        self.is_translating = False
        self.current_text = ""
        self.translated_text = ""
        self.translation_thread = None
        self.source_segments = []
        self.translated_segments = []
        self.failed_segments = []
        self.selected_failed_index = None
        # 鏄惁宸插惎鐢ㄦ湰鍦癓M Studio澶囩敤鏂规
        self.lm_studio_fallback_active = False
        # 杩涘害缂撳瓨/鎭㈠鎺у埗
        self.text_signature = None
        self.resume_from_index = 0
        self.consecutive_failures = 0
        self.paused_due_to_failures = False

        # 澶ф枃浠跺鐞?        self.show_full_text = False

        # 鎵归噺澶勭悊鐘舵€?        self.batch_queue = []
        self.load_batch_queue() # Load persistence
        self.is_batch_mode = False
        self.batch_window = None
        self.batch_output_dir = ""

        # 鍙屾爮瀵圭収鐘舵€?
        self.sync_scroll_enabled = True

        # API閰嶇疆
        self.api_configs = deepcopy(DEFAULT_API_CONFIGS)
        self.custom_local_models = {}  # 鑷畾涔夋湰鍦版ā鍨嬪瓨鍌?        self.target_language_var = tk.StringVar(value=self.saved_target_language or DEFAULT_TARGET_LANGUAGE)

        # 鐙珛鐨勭炕璇戝拰瑙ｆ瀽API閫夋嫨
        self.translation_api_var = tk.StringVar(value=DEFAULT_SELECTED_TRANSLATION_API)
        self.analysis_api_var = tk.StringVar(value=DEFAULT_SELECTED_ANALYSIS_API)
        retry_default_api = DEFAULT_SELECTED_RETRY_API if OPENAI_SUPPORT else DEFAULT_SELECTED_TRANSLATION_API
        self.retry_api_var = tk.StringVar(value=retry_default_api)

        # 瑙ｆ瀽鐩稿叧鐘舵€?        self.analysis_segments = []  # 姣忔鐨勮В鏋愮粨鏋?        self.is_analyzing = False
        self.analysis_thread = None
        self.retry_failed_segment_service = RetryFailedSegmentService()
        self.failed_segment_actions = FailedSegmentActions(self)
        self.failed_segment_feature = FailedSegmentFeature(self)

        self.setup_ui()
        self.failed_segment_controller = FailedSegmentController(self, getattr(self, 'failed_panel', None))
        self.failed_segment_feature.attach_actions(self.failed_segment_actions)
        self.failed_segment_feature.attach_controller(self.failed_segment_controller)
        self.failed_segment_feature.attach_panel(getattr(self, 'failed_panel', None))
        self.load_config()
        self.try_resume_cached_progress()

    def load_batch_queue(self):
        """鍔犺浇鎵归噺浠诲姟鍒楄〃"""
        try:
            self.batch_queue = self.runtime_state.load_batch_queue()
        except Exception as e:
            print(f"Failed to load batch queue: {e}")
            self.batch_queue = []

    def save_batch_queue(self):
        """淇濆瓨鎵归噺浠诲姟鍒楄〃"""
        try:
            self.runtime_state.save_batch_queue(self.batch_queue)
        except Exception as e:
            print(f"Failed to save batch queue: {e}")

    def setup_ui(self):
        """璁剧疆鐢ㄦ埛鐣岄潰"""
        # 鍒涘缓鑿滃崟鏍?
        self.create_menu_bar()

        # 鍒涘缓涓绘鏋?(Root container)
        root_container = ttk.Frame(self.root, padding="5")
        root_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        root_container.columnconfigure(0, weight=1)
        root_container.rowconfigure(0, weight=1)

        # === 椤堕儴涓诲垎椤?(Main Notebook) ===
        self.main_notebook = ttk.Notebook(root_container)
        self.main_notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # TAB 1: 缈昏瘧宸ヤ綔鍙?
        self.workstation_frame = ttk.Frame(self.main_notebook, padding="10")
        self.main_notebook.add(self.workstation_frame, text="缈昏瘧宸ヤ綔鍙?)
        
        # TAB 2: 鍦ㄧ嚎涔﹀煄 (澶ч〉绛?
        self.library_frame = ttk.Frame(self.main_notebook, padding="10")
        self.main_notebook.add(self.library_frame, text="鍦ㄧ嚎涔﹀煄")
        
        # 鍒濆鍖栨悳绱㈤〉绛?
        self.setup_search_tab()

        # 閰嶇疆宸ヤ綔鍙版潈閲?
        self.workstation_frame.columnconfigure(0, weight=1)
        self.workstation_frame.rowconfigure(2, weight=1) # content_frame is row 2
        
        # 鎸囧悜宸ヤ綔鍙帮紝淇濇寔鍚庣画浠ｇ爜鍏煎
        main_frame = self.workstation_frame

        # 1. 鏂囦欢閫夋嫨鍖哄煙
        file_frame = ttk.LabelFrame(main_frame, text="鏂囦欢閫夋嫨", padding="10")
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)

        ttk.Label(file_frame, text="閫夋嫨鏂囦欢:").grid(row=0, column=0, sticky=tk.W)
        self.file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path_var, state='readonly').grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=5
        )
        ttk.Button(file_frame, text="娴忚...", command=self.browse_file).grid(
            row=0, column=2, padx=5
        )
        ttk.Button(file_frame, text="鎵归噺浠诲姟...", command=self.open_batch_window).grid(
            row=0, column=3, padx=5
        )
        ttk.Button(file_frame, text="鏈琛ㄧ鐞?, command=self.open_glossary_editor).grid(
            row=0, column=4, padx=5
        )

        # 鏀寔鐨勬牸寮忔彁绀?
        formats = []
        if PDF_SUPPORT:
            formats.append("PDF")
        if EPUB_SUPPORT:
            formats.append("EPUB")
        formats.append("TXT")

        support_label = f"鏀寔鏍煎紡: {', '.join(formats)}"
        ttk.Label(file_frame, text=support_label, foreground="gray").grid(
            row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0)
        )

        # 鏂囦欢澶у皬鍜岄瑙堟帶鍒?
        preview_frame = ttk.Frame(file_frame)
        preview_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))

        self.file_info_var = tk.StringVar(value="")
        ttk.Label(preview_frame, textvariable=self.file_info_var, foreground="blue").pack(
            side=tk.LEFT
        )
        
        # 鎴愭湰浼扮畻鏍囩
        self.cost_var = tk.StringVar(value="")
        ttk.Label(preview_frame, textvariable=self.cost_var, foreground="green").pack(
            side=tk.LEFT, padx=(10, 0)
        )

        self.toggle_preview_btn = ttk.Button(
            preview_frame,
            text="鏄剧ず瀹屾暣鍘熸枃",
            command=self.toggle_full_text_display,
            state='disabled'
        )
        self.toggle_preview_btn.pack(side=tk.RIGHT, padx=5)

        # 2. API閰嶇疆鍖哄煙锛堥噸鏋勶細鍙屼笅鎷夋 + 鏈湴妯″瀷绠＄悊锛?
        api_frame = ttk.LabelFrame(main_frame, text="API閰嶇疆", padding="10")
        api_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        api_frame.columnconfigure(1, weight=1)

        # 鑾峰彇鍙敤API鍒楄〃
        available_apis = self.get_all_available_apis()
        api_names = [name for name, _, _ in available_apis]

        # 缈昏瘧API閫夋嫨
        ttk.Label(api_frame, text="缈昏瘧API:").grid(row=0, column=0, sticky=tk.W)
        self.translation_api_combo = ttk.Combobox(
            api_frame,
            textvariable=self.translation_api_var,
            values=api_names,
            state='readonly',
            width=22
        )
        self.translation_api_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        self.translation_api_combo.bind('<<ComboboxSelected>>', self.on_api_type_change)
        ttk.Button(api_frame, text="閰嶇疆", command=lambda: self.open_api_config_for('translation')).grid(
            row=0, column=2, padx=5
        )

        # 瑙ｆ瀽API閫夋嫨
        ttk.Label(api_frame, text="瑙ｆ瀽API:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.analysis_api_combo = ttk.Combobox(
            api_frame,
            textvariable=self.analysis_api_var,
            values=api_names,
            state='readonly',
            width=22
        )
        self.analysis_api_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=(5, 0))
        ttk.Button(api_frame, text="閰嶇疆", command=lambda: self.open_api_config_for('analysis')).grid(
            row=1, column=2, padx=5, pady=(5, 0)
        )

        # 鏈湴妯″瀷绠＄悊鎸夐挳
        model_btn_frame = ttk.Frame(api_frame)
        model_btn_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(8, 0))
        ttk.Button(model_btn_frame, text="+ 娣诲姞鏈湴妯″瀷", command=self.open_add_local_model_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(model_btn_frame, text="绠＄悊鏈湴妯″瀷", command=self.open_manage_local_models_dialog).pack(side=tk.LEFT)

        # API鐘舵€?
        self.api_status_var = tk.StringVar(value="鏈厤缃?)
        self.api_status_label = ttk.Label(api_frame, textvariable=self.api_status_var, foreground="orange")
        self.api_status_label.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))

        # 鐩爣璇█
        ttk.Label(api_frame, text="鐩爣璇█:").grid(row=4, column=0, sticky=tk.W, pady=(5, 0))
        lang_options = ["涓枃", "鑻辨枃", "English", "鏃ヨ", "闊╄", "寰疯", "娉曡"]
        lang_combo = ttk.Combobox(
            api_frame,
            textvariable=self.target_language_var,
            values=lang_options,
            state='normal',
            width=22
        )
        lang_combo.grid(row=4, column=1, sticky=tk.W, padx=5, pady=(5, 0))

        # 鏂板锛氱炕璇戦鏍?
        ttk.Label(api_frame, text="缈昏瘧椋庢牸:").grid(row=5, column=0, sticky=tk.W, pady=(5, 0))
        self.style_var = tk.StringVar(value=self.saved_translation_style)
        style_options = ["鐩磋瘧 (Literal)", "閫氫織灏忚 (Novel)", "瀛︽湳涓撲笟 (Academic)", "姝︿緺/鍙ら (Wuxia)", "鏂伴椈/濯掍綋 (News)"]
        style_combo = ttk.Combobox(
            api_frame,
            textvariable=self.style_var,
            values=style_options,
            state='readonly',
            width=22
        )
        style_combo.grid(row=5, column=1, sticky=tk.W, padx=5, pady=(5, 0))

        # 鏂板锛氬苟鍙戣缃紙閫熷害 vs 璐ㄩ噺锛?
        ttk.Label(api_frame, text="骞跺彂绾跨▼:").grid(row=6, column=0, sticky=tk.W, pady=(5, 0))
        
        concurrency_frame = ttk.Frame(api_frame)
        concurrency_frame.grid(row=6, column=1, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        self.concurrency_var = tk.IntVar(value=self.saved_concurrency)
        self.concurrency_scale = tk.Scale(
            concurrency_frame, 
            from_=1, to=10, 
            orient=tk.HORIZONTAL, 
            variable=self.concurrency_var,
            length=140,
            showvalue=0,
            command=self.update_concurrency_label
        )
        self.concurrency_scale.pack(side=tk.LEFT, padx=(5, 5))
        
        self.concurrency_label = ttk.Label(concurrency_frame, text=f"{self.concurrency_var.get()} (楂樿川閲忔ā寮?")
        self.concurrency_label.pack(side=tk.LEFT)
        
        # 鎻愮ず淇℃伅
        self.concurrency_hint_var = tk.StringVar(value="")
        ttk.Label(api_frame, textvariable=self.concurrency_hint_var, foreground="gray", font=('', 8)).grid(row=7, column=0, columnspan=3, sticky=tk.W, pady=(2, 0))
        self.update_concurrency_label(self.concurrency_var.get())

        ttk.Label(
            api_frame,
            text="API閰嶉鐢ㄥ敖鏃跺皢鑷姩鍒囨崲鍒版湰鍦版ā鍨?,
            foreground="gray",
            font=('', 8)
        ).grid(row=8, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))

        # 鍏煎鏃т唬鐮侊細淇濈暀api_type_var鏄犲皠
        self.api_type_var = self.translation_api_var

        # 3. 缈昏瘧鍐呭鏄剧ず鍖哄煙
        content_frame = ttk.LabelFrame(main_frame, text="缈昏瘧鍐呭", padding="10")
        content_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)

        # === 渚ц竟鏍忎笌涓诲唴瀹瑰垎鍓?===
        self.content_paned = tk.PanedWindow(content_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        self.content_paned.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 宸︿晶鐩綍鏍?(TOC)
        self.sidebar_frame = ttk.Frame(self.content_paned, width=200)
        self.content_paned.add(self.sidebar_frame, minsize=150)
        
        ttk.Label(self.sidebar_frame, text="绔犺妭鐩綍 (鑷姩璇嗗埆)").pack(anchor=tk.W, padx=5, pady=5)
        self.toc_tree = ttk.Treeview(self.sidebar_frame, show="tree", selectmode="browse")
        self.toc_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar_toc = ttk.Scrollbar(self.sidebar_frame, orient=tk.VERTICAL, command=self.toc_tree.yview)
        scrollbar_toc.pack(side=tk.RIGHT, fill=tk.Y)
        self.toc_tree.configure(yscrollcommand=scrollbar_toc.set)
        self.toc_tree.bind("<<TreeviewSelect>>", self.on_toc_click)

        # 鍙充晶涓昏 Notebook
        self.notebook = ttk.Notebook(self.content_paned)
        self.content_paned.add(self.notebook, minsize=500)

        # 鍘熸枃鏍囩椤?
        original_frame = ttk.Frame(self.notebook)
        self.notebook.add(original_frame, text="鍘熸枃")
        original_frame.columnconfigure(0, weight=1)
        original_frame.rowconfigure(0, weight=1)

        self.original_text = scrolledtext.ScrolledText(
            original_frame, wrap=tk.WORD, height=15
        )
        self.original_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 璇戞枃鏍囩椤?
        translated_frame = ttk.Frame(self.notebook)
        self.notebook.add(translated_frame, text="璇戞枃")
        translated_frame.columnconfigure(0, weight=1)
        translated_frame.rowconfigure(0, weight=1)

        self.translated_text_widget = scrolledtext.ScrolledText(
            translated_frame, wrap=tk.WORD, height=15
        )
        self.translated_text_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 鍙屾爮瀵圭収鏍囩椤?
        self.setup_comparison_tab()

        # 澶辫触娈佃惤鏍囩椤?        preferred_retry = choose_retry_api_name(
            api_names,
            current_retry=self.retry_api_var.get(),
            translation_api_name=self.translation_api_var.get(),
        )
        if preferred_retry != self.retry_api_var.get():
            self.retry_api_var.set(preferred_retry)

        self.failed_panel = FailedSegmentPanel(
            parent_notebook=self.notebook,
            retry_api_var=self.retry_api_var,
            api_names=api_names,
            on_select=self.on_failed_select,
            on_retry=self.retry_failed_segment,
            on_save_manual=self.save_manual_translation,
            on_open_retry_api=lambda: self.open_api_config_for('retry'),
        )
        self.failed_listbox = self.failed_panel.failed_listbox
        self.failed_source_text = self.failed_panel.failed_source_text
        self.manual_translation_text = self.failed_panel.manual_translation_text
        self.retry_api_combo = self.failed_panel.retry_api_combo
        self.failed_status_var = self.failed_panel.failed_status_var

        # 瑙ｆ瀽鏍囩椤?        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="瑙ｆ瀽")
        analysis_frame.columnconfigure(1, weight=1)
        analysis_frame.rowconfigure(1, weight=1)

        ttk.Label(
            analysis_frame,
            text="瀵圭炕璇戞钀借繘琛岃В鏋愯瑙ｏ紙鎯呰妭瑙ｈ銆佹蹇佃В閲婄瓑锛?,
            foreground="gray"
        ).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))

        # 宸︿晶锛氭钀藉垪琛?
        analysis_list_frame = ttk.Frame(analysis_frame)
        analysis_list_frame.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.W), padx=(0, 10))

        ttk.Label(analysis_list_frame, text="娈佃惤鍒楄〃").pack(anchor=tk.W)
        self.analysis_listbox = tk.Listbox(analysis_list_frame, width=30, height=12)
        self.analysis_listbox.pack(fill=tk.Y, expand=True)
        self.analysis_listbox.bind('<<ListboxSelect>>', self.on_analysis_segment_select)

        # 鍙充晶锛氳В鏋愬唴瀹规樉绀?
        analysis_detail_frame = ttk.Frame(analysis_frame)
        analysis_detail_frame.grid(row=1, column=1, sticky=(tk.N, tk.S, tk.E, tk.W))
        analysis_detail_frame.columnconfigure(0, weight=1)
        analysis_detail_frame.rowconfigure(1, weight=1)

        ttk.Label(analysis_detail_frame, text="瑙ｆ瀽鍐呭").grid(row=0, column=0, sticky=tk.W)
        self.analysis_text = scrolledtext.ScrolledText(
            analysis_detail_frame, wrap=tk.WORD, height=12
        )
        self.analysis_text.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

        # 瑙ｆ瀽鎸夐挳
        analysis_btn_frame = ttk.Frame(analysis_frame)
        analysis_btn_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        ttk.Button(analysis_btn_frame, text="瑙ｆ瀽閫変腑娈佃惤", command=self.analyze_selected_segment).pack(side=tk.LEFT, padx=5)
        ttk.Button(analysis_btn_frame, text="澶嶅埗瑙ｆ瀽", command=self.copy_analysis_content).pack(side=tk.LEFT, padx=5)

        self.analysis_status_var = tk.StringVar(value="缈昏瘧瀹屾垚鍚庡彲杩涜瑙ｆ瀽")
        ttk.Label(analysis_frame, textvariable=self.analysis_status_var, foreground="gray").grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=(5, 0)
        )

        # 4. 杩涘害鍜屾帶鍒跺尯鍩?
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        control_frame.columnconfigure(0, weight=1)

        # 杩涘害鏉?
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            control_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        # 杩涘害鏂囨湰
        self.progress_text_var = tk.StringVar(value="灏辩华")
        ttk.Label(control_frame, textvariable=self.progress_text_var).grid(
            row=1, column=0, sticky=tk.W
        )

        # 5. 鎿嶄綔鎸夐挳鍖哄煙锛堝垎涓よ锛?
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))

        # 绗竴琛岋細缈昏瘧鐩稿叧鎸夐挳
        self.translate_btn = ttk.Button(
            button_frame, text="寮€濮嬬炕璇?, command=self.start_translation
        )
        self.translate_btn.grid(row=0, column=0, padx=5, pady=2)

        self.stop_btn = ttk.Button(
            button_frame, text="鍋滄", command=self.stop_translation, state='disabled'
        )
        self.stop_btn.grid(row=0, column=1, padx=5, pady=2)

        self.analyze_all_btn = ttk.Button(
            button_frame, text="涓€閿В鏋愬叏閮?, command=self.start_batch_analysis
        )
        self.analyze_all_btn.grid(row=0, column=2, padx=5, pady=2)

        self.stop_analysis_btn = ttk.Button(
            button_frame, text="鍋滄瑙ｆ瀽", command=self.stop_analysis, state='disabled'
        )
        self.stop_analysis_btn.grid(row=0, column=3, padx=5, pady=2)

        ttk.Button(
            button_frame, text="瀵煎嚭璇戞枃", command=self.export_translation
        ).grid(row=0, column=4, padx=5, pady=2)

        ttk.Button(
            button_frame, text="瀵煎嚭鍙岃涔?, command=self.export_bilingual_epub
        ).grid(row=0, column=5, padx=5, pady=2)

        ttk.Button(
            button_frame, text="瀵煎嚭鏈夊０涔?, command=self.export_audiobook
        ).grid(row=0, column=6, padx=5, pady=2)

        ttk.Button(
            button_frame, text="瀵煎嚭瑙ｆ瀽", command=self.export_analysis
        ).grid(row=0, column=7, padx=5, pady=2)

        ttk.Button(
            button_frame, text="娓呯┖", command=self.clear_all
        ).grid(row=0, column=8, padx=5, pady=2)

    def setup_comparison_tab(self):
        """璁剧疆鍙屾爮瀵圭収鏍囩椤?""
        comp_frame = ttk.Frame(self.notebook)
        self.notebook.add(comp_frame, text="鍙屾爮瀵圭収")
        
        # 椤堕儴宸ュ叿鏍?
        toolbar = ttk.Frame(comp_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        self.sync_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(toolbar, text="鍚屾婊氬姩", variable=self.sync_scroll_var).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="淇濆瓨鍙充晶淇敼", command=self.save_comparison_edits).pack(side=tk.LEFT, padx=10)
        
        # 鍒嗗壊绐楀彛
        paned = tk.PanedWindow(comp_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 宸︿晶鍘熸枃锛堝彧璇伙級
        left_frame = ttk.LabelFrame(paned, text="鍘熸枃")
        paned.add(left_frame, minsize=100)
        
        self.comp_source_text = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, height=15)
        self.comp_source_text.pack(fill=tk.BOTH, expand=True)
        self.comp_source_text.config(state='disabled')
        
        # 鍙充晶璇戞枃锛堝彲缂栬緫锛?
        right_frame = ttk.LabelFrame(paned, text="璇戞枃 (鍙紪杈?")
        paned.add(right_frame, minsize=100)
        
        self.comp_target_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, height=15)
        self.comp_target_text.pack(fill=tk.BOTH, expand=True)
        
        # 缁戝畾婊氬姩浜嬩欢
        self.comp_source_text.vbar.config(command=self._on_source_scroll)
        self.comp_target_text.vbar.config(command=self._on_target_scroll)
        
        # 榧犳爣婊氳疆缁戝畾 (Windows/Linux)
        self.comp_source_text.bind("<MouseWheel>", lambda e: self._on_mousewheel(e, self.comp_target_text))
        self.comp_target_text.bind("<MouseWheel>", lambda e: self._on_mousewheel(e, self.comp_source_text))
        
        # 鍒濆鍒嗗壊浣嶇疆 (50%)
        # 闇€瑕佸湪绐楀彛鏄剧ず鍚庤缃墠鍑嗙‘锛岃繖閲屽厛鐣ヨ繃

    def _on_source_scroll(self, *args):
        self.comp_source_text.yview(*args)
        if self.sync_scroll_var.get():
            self.comp_target_text.yview_moveto(args[0])

    def _on_target_scroll(self, *args):
        self.comp_target_text.yview(*args)
        if self.sync_scroll_var.get():
            self.comp_source_text.yview_moveto(args[0])
            
    def _on_mousewheel(self, event, other_widget):
        if self.sync_scroll_var.get():
            # 浼犻€掓粴杞簨浠剁粰鍙︿竴涓帶浠?
            other_widget.yview_scroll(int(-1*(event.delta/120)), "units")
            
    def update_comparison_view(self):
        """鏇存柊鍙屾爮瀵圭収瑙嗗浘鐨勫唴瀹?""
        # 鍑嗗鍘熸枃鏂囨湰锛堟寜娈佃惤鍒嗛殧锛?
        source_display = "\n\n".join(self.source_segments) if self.source_segments else self.current_text
        
        # 鍑嗗璇戞枃鏂囨湰锛堢‘淇濅笌鍘熸枃娈佃惤瀵瑰簲锛?
        target_segments_display = list(self.translated_segments)
        # 琛ラ綈闀垮害
        if len(target_segments_display) < len(self.source_segments):
            target_segments_display.extend([""] * (len(self.source_segments) - len(target_segments_display)))
            
        target_display = "\n\n".join(target_segments_display)
        
        self.comp_source_text.config(state='normal')
        self.comp_source_text.delete('1.0', tk.END)
        self.comp_source_text.insert('1.0', source_display)
        self.comp_source_text.config(state='disabled')
        
        self.comp_target_text.delete('1.0', tk.END)
        self.comp_target_text.insert('1.0', target_display)

    def save_comparison_edits(self):
        """淇濆瓨鍙屾爮瑙嗗浘涓殑淇敼鍒颁富鏁版嵁骞跺悓姝ュ埌璁板繂搴?""
        new_text = self.comp_target_text.get('1.0', tk.END).strip()
        if not new_text:
            return
            
        # 灏濊瘯鎸夊弻鎹㈣绗﹀垎鍓插洖娈佃惤
        new_segments = re.split(r'\n\s*\n', new_text)
        
        # 绠€鍗曠殑瀹屾暣鎬ф鏌?
        if abs(len(new_segments) - len(self.source_segments)) > 5:
            confirm = messagebox.askyesno(
                "娈佃惤鏁伴噺涓嶅尮閰?, 
                f"缂栬緫鍚庣殑娈佃惤鏁?({len(new_segments)}) 涓庡師鏂囨钀芥暟 ({len(self.source_segments)}) 宸紓杈冨ぇ銆俓n"
                "杩欏彲鑳藉鑷村悗缁鐓ч敊浣嶃€俓n\n鏄惁浠嶈淇濆瓨锛?
            )
            if not confirm:
                return

        # 鍚屾鍒扮炕璇戣蹇嗗簱 (Linkage 1)
        count_updated = 0
        target_lang = self.get_target_language()
        
        # 姣旇緝宸紓骞朵繚瀛?
        limit = min(len(new_segments), len(self.source_segments), len(self.translated_segments))
        for i in range(limit):
            old_trans = self.translated_segments[i]
            new_trans = new_segments[i]
            source = self.source_segments[i]
            
            # 濡傛灉鏈夊疄璐ㄦ€т慨鏀?
            if old_trans.strip() != new_trans.strip() and source.strip():
                try:
                    self.translation_memory.store(
                        source_text=source,
                        translated_text=new_trans,
                        target_lang=target_lang,
                        api_provider="manual",
                        model="user_correction",
                        quality_score=100
                    )
                    count_updated += 1
                except Exception as e:
                    print(f"Sync to TM failed for segment {i}: {e}")

        # 鏇存柊涓绘暟鎹?
        self.translated_segments = new_segments
        self.rebuild_translated_text()
        self.save_progress_cache()
        
        msg = "淇敼宸蹭繚瀛樺苟鍚屾鍒颁富瑙嗗浘"
        if count_updated > 0:
            msg += f"\n\n宸插皢 {count_updated} 澶勪汉宸ヤ慨姝ｅ悓姝ュ埌缈昏瘧璁板繂搴擄紒"
            
        messagebox.showinfo("鎴愬姛", msg)

    def open_glossary_editor(self):
        """鎵撳紑鏈琛ㄧ紪杈戝櫒"""
        GlossaryEditorDialog(self.root, self.glossary_manager)

    def open_cloud_share(self):
        """鎵撳紑浜戠鍒嗕韩瀵硅瘽妗?""
        dialog = tk.Toplevel(self.root)
        dialog.title("浜戠鍒嗕韩 (Cloud Share)")
        dialog.geometry("600x480")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 1. 鏂囦欢閫夋嫨
        ttk.Label(frame, text="閫夋嫨瑕佷笂浼犵殑鏂囦欢:", font=("", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        file_frame = ttk.Frame(frame)
        file_frame.pack(fill=tk.X, pady=5)
        
        file_path_var = tk.StringVar()
        if self.file_path_var.get():
            file_path_var.set(self.file_path_var.get())
            
        entry = ttk.Entry(file_frame, textvariable=file_path_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        def browse():
            f = filedialog.askopenfilename()
            if f: file_path_var.set(f)
            
        ttk.Button(file_frame, text="娴忚...", command=browse).pack(side=tk.LEFT, padx=5)
        
        # 蹇嵎閫夐」
        quick_frame = ttk.Frame(frame)
        quick_frame.pack(fill=tk.X, pady=5)
        
        def set_current_txt():
            if not self.translated_text:
                messagebox.showinfo("鎻愮ず", "褰撳墠娌℃湁璇戞枃")
                return
            try:
                # Save to a temporary file
                temp_dir = Path("temp_exports")
                temp_dir.mkdir(exist_ok=True)
                
                # Use original filename + _translated.txt
                orig_name = Path(self.file_path_var.get()).stem if self.file_path_var.get() else "translation"
                temp_path = temp_dir / f"{orig_name}_translated.txt"
                
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(self.translated_text)
                file_path_var.set(str(temp_path.absolute()))
            except Exception as e:
                messagebox.showerror("閿欒", str(e))
                
        ttk.Button(quick_frame, text="褰撳墠璇戞枃 (TXT)", command=set_current_txt).pack(side=tk.LEFT, padx=2)
        
        # 2. 鏈嶅姟閫夋嫨
        ttk.Label(frame, text="閫夋嫨鍒嗕韩鏈嶅姟:", font=("", 10, "bold")).pack(anchor=tk.W, pady=(15, 5))
        service_var = tk.StringVar(value="Catbox (姘镐箙/闀挎湡)")
        
        s1 = ttk.Radiobutton(frame, text="Catbox (鎺ㄨ崘 - 姘镐箙鏈夋晥锛屾渶澶?00MB)", variable=service_var, value="Catbox (姘镐箙/闀挎湡)")
        s1.pack(anchor=tk.W)
        
        s2 = ttk.Radiobutton(frame, text="File.io (涓€娆℃€?- 涓嬭浇1娆℃垨2鍛ㄥ悗鍒犻櫎)", variable=service_var, value="File.io (涓€娆℃€?2鍛?")
        s2.pack(anchor=tk.W)
        
        s3 = ttk.Radiobutton(frame, text="Litterbox (涓存椂 - 72灏忔椂鍚庡垹闄?", variable=service_var, value="Litterbox (72灏忔椂)")
        s3.pack(anchor=tk.W)
            
        # 3. 涓婁紶鎸夐挳
        status_var = tk.StringVar(value="鍑嗗灏辩华")
        ttk.Label(frame, textvariable=status_var, foreground="blue").pack(pady=(15, 5))
        
        result_var = tk.StringVar()
        result_entry = ttk.Entry(frame, textvariable=result_var, state='readonly', font=("Consolas", 10))
        result_entry.pack(fill=tk.X, pady=5)
        
        def copy_link():
            if result_var.get():
                self.root.clipboard_clear()
                self.root.clipboard_append(result_var.get())
                messagebox.showinfo("澶嶅埗鎴愬姛", "閾炬帴宸插鍒跺埌鍓创鏉?)
        
        copy_btn = ttk.Button(frame, text="澶嶅埗閾炬帴", command=copy_link, state='disabled')
        copy_btn.pack(pady=5)
        
        def start_upload():
            path = file_path_var.get()
            if not path or not os.path.exists(path):
                messagebox.showerror("閿欒", "鏂囦欢涓嶅瓨鍦?)
                return
                
            service = service_var.get()
            status_var.set("姝ｅ湪涓婁紶锛岃绋嶅€?..")
            upload_btn.config(state='disabled')
            dialog.update()
            
            def run():
                try:
                    url = ""
                    if "Catbox" in service:
                        url = CloudUploader.upload_to_catbox(path)
                    elif "Litterbox" in service:
                        url = CloudUploader.upload_to_litterbox(path, time='72h')
                    elif "File.io" in service:
                        url = CloudUploader.upload_to_fileio(path)
                        
                    dialog.after(0, lambda: success(url))
                except Exception as e:
                    dialog.after(0, lambda: fail(str(e)))
            
            threading.Thread(target=run, daemon=True).start()
            
        def success(url):
            status_var.set("涓婁紶鎴愬姛!")
            result_var.set(url)
            upload_btn.config(state='normal')
            copy_btn.config(state='normal')
            messagebox.showinfo("鎴愬姛", f"鏂囦欢涓婁紶鎴愬姛!\n閾炬帴: {url}\n\n璇ラ摼鎺ュ彲鍦ㄤ换浣曞湴鏂硅闂€?)
            
        def fail(msg):
            status_var.set("涓婁紶澶辫触")
            result_var.set("")
            upload_btn.config(state='normal')
            messagebox.showerror("涓婁紶澶辫触", msg)
            
        upload_btn = ttk.Button(frame, text="寮€濮嬩笂浼?, command=start_upload)
        upload_btn.pack(pady=10)
        
        ttk.Label(frame, text="娉ㄦ剰: 璇峰嬁涓婁紶鏁忔劅鎴栭殣绉佹枃浠躲€?, foreground="gray", font=("", 8)).pack(side=tk.BOTTOM, pady=5)

    def generate_toc(self, text):
        """鐢熸垚鐩綍缁撴瀯"""
        self.toc_tree.delete(*self.toc_tree.get_children())
        if not text: return
        
        # 甯歌绔犺妭鍖归厤妯″紡
        patterns = [
            r'(^|\n)\s*(绗琜0-9涓€浜屼笁鍥涗簲鍏竷鍏節鍗佺櫨]+[绔犺妭鍥瀅.{0,30})',
            r'(^|\n)\s*(Chapter\s+[0-9IVX]+.{0,30})',
            r'(^|\n)\s*(\d+\.\s+.{0,30})'
        ]
        
        matches = []
        for pat in patterns:
            for m in re.finditer(pat, text):
                matches.append((m.start(), m.group(0).strip()))
        
        # 鎺掑簭
        matches.sort(key=lambda x: x[0])
        
        # 鍘婚噸涓庤繃婊?
        unique_matches = []
        last_pos = -1
        for pos, title in matches:
            if pos > last_pos + 100: # 鍋囪绔犺妭闂撮殧鑷冲皯100瀛楃
                unique_matches.append((pos, title))
                last_pos = pos
                
        # 濉厖鏍?
        for pos, title in unique_matches:
            self.toc_tree.insert("", "end", text=title, values=(pos,))

    def on_toc_click(self, event):
        """澶勭悊鐩綍鐐瑰嚮璺宠浆"""
        selected = self.toc_tree.selection()
        if not selected: return
        item = self.toc_tree.item(selected[0])
        pos = int(item['values'][0])
        
        # 璺宠浆鍘熸枃
        index = f"1.0 + {pos} chars"
        self.original_text.see(index)
        self.original_text.tag_remove("highlight", "1.0", "end")
        self.original_text.tag_add("highlight", index, f"{index} lineend")
        self.original_text.tag_config("highlight", background="yellow")

    def browse_file(self):
        """娴忚骞堕€夋嫨鏂囦欢"""
        filetypes = [("鎵€鏈夋敮鎸佺殑鏂囦欢", "*.txt *.pdf *.epub")]
        if PDF_SUPPORT:
            filetypes.append(("PDF鏂囦欢", "*.pdf"))
        if EPUB_SUPPORT:
            filetypes.append(("EPUB鏂囦欢", "*.epub"))
        filetypes.append(("鏂囨湰鏂囦欢", "*.txt"))

        filename = filedialog.askopenfilename(
            title="閫夋嫨瑕佺炕璇戠殑涔︾睄",
            filetypes=filetypes
        )

        if filename:
            self.file_path_var.set(filename)
            self.load_file_content(filename)
            # 鍔犺浇鏂版枃浠舵椂娓呯悊鏃х紦瀛?
            self.clear_progress_cache()

    def load_file_content(self, filepath):
        """鍔犺浇鏂囦欢鍐呭"""
        try:
            content = ""
            
            # 浣跨敤 FileProcessor 璇诲彇鏂囦欢
            def update_progress(msg):
                self.progress_text_var.set(msg)
                self.root.update()

            content = self.file_processor.read_file(filepath, progress_callback=update_progress)

            if not content:
                raise ValueError("鏂囦欢鍐呭涓虹┖")

            self.current_text = content
            self.generate_toc(content)
            self.text_signature = self.compute_text_signature(self.current_text)
            self.source_segments = []
            self.translated_segments = []
            self.failed_segments = []
            self.resume_from_index = 0
            self.original_text.delete('1.0', tk.END)
            
            # 缁熻淇℃伅
            char_count = len(content)
            word_count = len(content.split())

            # 鍒ゆ柇鏄惁涓哄ぇ鏂囦欢
            is_large_file = char_count > self.preview_limit

            # 鏇存柊鏄剧ず
            self.update_text_display()

            # 鏇存柊鏂囦欢淇℃伅
            if is_large_file:
                self.file_info_var.set(
                    f"鈿狅笍 澶ф枃浠?({char_count:,} 瀛楃) - 浠呮樉绀哄墠 {self.preview_limit:,} 瀛楃"
                )
                self.toggle_preview_btn.config(state='normal')
            else:
                self.file_info_var.set(f"鉁?宸插姞杞藉畬鏁存枃浠?({char_count:,} 瀛楃)")
                self.toggle_preview_btn.config(state='disabled')

            self.progress_text_var.set(f"宸插姞杞芥枃浠?| 瀛楃鏁? {char_count:,} | 璇嶆暟: {word_count:,}")

            # 浼扮畻鎴愭湰
            model_name = self.api_configs.get(self.get_translation_api_type(), {}).get('model', 'unknown')
            cost_info = CostEstimator.calculate_cost(model_name, content)
            self.cost_var.set(f"棰勪及鎴愭湰: ${cost_info['cost_usd']} (Tokens: {cost_info['total_estimated_tokens']:,})")

            # 濡傛灉鏄?DOCX锛屽垵濮嬪寲澶勭悊鍣?
            if filepath.lower().endswith('.docx'):
                try:
                    self.docx_handler = DocxHandler(filepath)
                    self.file_info_var.set(self.file_info_var.get() + " [DOCX 鏍煎紡淇濈暀宸插氨缁猐")
                except Exception as e:
                    print(f"DOCX 鍒濆鍖栧け璐? {e}")
                    self.docx_handler = None
            else:
                self.docx_handler = None

            # 鎻愮ず淇℃伅
            msg = f"鏂囦欢鍔犺浇鎴愬姛!\n\n瀛楃鏁? {char_count:,}\n璇嶆暟: {word_count:,}\n棰勪及 Tokens: {cost_info['total_estimated_tokens']:,}"
            if is_large_file:
                msg += f"\n\n鈿狅笍 杩欐槸涓€涓ぇ鏂囦欢锛乗n涓轰簡鎬ц兘锛岄瑙堢獥鍙ｄ粎鏄剧ず鍓?{self.preview_limit:,} 瀛楃銆俓n\n缈昏瘧鏃朵細浣跨敤瀹屾暣鏂囨湰銆?
            messagebox.showinfo("鎴愬姛", msg)

        except Exception as e:
            messagebox.showerror("閿欒", f"鍔犺浇鏂囦欢澶辫触:\n{str(e)}")

    # ==================== 鎵归噺澶勭悊鍔熻兘 ====================

    def open_batch_window(self):
        """鎵撳紑鎵归噺浠诲姟绠＄悊绐楀彛"""
        if self.batch_window and self.batch_window.winfo_exists():
            self.batch_window.lift()
            return

        self.batch_window = tk.Toplevel(self.root)
        self.batch_window.title("鎵归噺缈昏瘧浠诲姟")
        self.batch_window.geometry("600x450")
        
        # 椤堕儴璇存槑
        ttk.Label(
            self.batch_window, 
            text="鎵归噺娣诲姞鏂囦欢锛岀▼搴忓皢鑷姩閫愪釜缈昏瘧骞跺鍑恒€俓n璇风‘淇滱PI閰嶉鍏呰冻鎴栧惎鐢ㄤ簡鏈湴妯″瀷鍥為€€銆?,
            justify=tk.LEFT, padding=10
        ).pack(fill=tk.X)
        
        # 浠诲姟鍒楄〃
        list_frame = ttk.Frame(self.batch_window, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.batch_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED)
        self.batch_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.batch_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.batch_listbox.config(yscrollcommand=scrollbar.set)
        
        # 鏇存柊鍒楄〃鏄剧ず
        self.update_batch_list()
        
        # 搴曢儴鎸夐挳
        btn_frame = ttk.Frame(self.batch_window, padding=10)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="娣诲姞鏂囦欢...", command=self.add_batch_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="绉婚櫎閫変腑", command=self.remove_batch_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="娓呯┖鍒楄〃", command=lambda: [self.batch_queue.clear(), self.update_batch_list()]).pack(side=tk.LEFT, padx=5)
        
        ttk.Frame(btn_frame).pack(side=tk.LEFT, expand=True) # Spacer
        
        self.batch_start_btn = ttk.Button(btn_frame, text="寮€濮嬫壒閲忓鐞?, command=self.start_batch_processing)
        self.batch_start_btn.pack(side=tk.RIGHT, padx=5)

    def update_batch_list(self):
        """鏇存柊鎵归噺浠诲姟鍒楄〃鏄剧ず"""
        if not hasattr(self, 'batch_listbox') or not self.batch_listbox.winfo_exists():
            return
            
        self.batch_listbox.delete(0, tk.END)
        for item in self.batch_queue:
            status_icon = "鈴?
            if item['status'] == 'done': status_icon = "鉁?
            elif item['status'] == 'processing': status_icon = "馃攧"
            elif item['status'] == 'failed': status_icon = "鉂?
            
            self.batch_listbox.insert(tk.END, f"{status_icon} {Path(item['path']).name} ({item['status']})")

    def add_batch_files(self):
        """娣诲姞鏂囦欢鍒版壒閲忛槦鍒?""
        filenames = filedialog.askopenfilenames(
            title="閫夋嫨瑕佹壒閲忕炕璇戠殑鏂囦欢",
            filetypes=[("鏀寔鐨勬枃浠?, "*.txt *.pdf *.epub *.docx *.md")]
        )
        if filenames:
            for f in filenames:
                # 鏌ラ噸
                if not any(item['path'] == f for item in self.batch_queue):
                    self.batch_queue.append({
                        'path': f,
                        'status': 'pending'
                    })
            self.save_batch_queue()
            self.update_batch_list()

    def remove_batch_file(self):
        """绉婚櫎閫変腑鐨勬壒閲忎换鍔?""
        indices = self.batch_listbox.curselection()
        if not indices: return
        
        # 浠庡悗寰€鍓嶅垹锛岄伩鍏嶇储寮曞亸绉?
        for i in sorted(indices, reverse=True):
            if i < len(self.batch_queue):
                del self.batch_queue[i]
        self.save_batch_queue()
        self.update_batch_list()

    def start_batch_processing(self):
        """寮€濮嬫壒閲忓鐞?""
        pending = [item for item in self.batch_queue if item['status'] == 'pending']
        if not pending:
            messagebox.showinfo("鎻愮ず", "娌℃湁寰呭鐞嗙殑浠诲姟")
            return
            
        # 閫夋嫨瀵煎嚭鐩綍
        self.batch_output_dir = filedialog.askdirectory(title="閫夋嫨鎵归噺瀵煎嚭鐩綍")
        if not self.batch_output_dir:
            return
            
        self.is_batch_mode = True
        self.process_next_batch_file()
        
        if self.batch_window:
            self.batch_window.destroy()
            self.batch_window = None

    def process_next_batch_file(self):
        """澶勭悊涓嬩竴涓壒閲忔枃浠?""
        if not self.is_batch_mode:
            return

        # 鏌ユ壘涓嬩竴涓?pending 浠诲姟
        next_idx = -1
        for i, item in enumerate(self.batch_queue):
            if item['status'] == 'pending':
                next_idx = i
                break
        
        if next_idx == -1:
            self.is_batch_mode = False
            messagebox.showinfo("鎵归噺瀹屾垚", "鎵€鏈夋壒閲忎换鍔″凡澶勭悊瀹屾瘯锛?)
            return

        # 鏍囪鐘舵€?
        self.batch_queue[next_idx]['status'] = 'processing'
        self.save_batch_queue()
        file_path = self.batch_queue[next_idx]['path']
        
        # 鍔犺浇鏂囦欢
        self.file_path_var.set(file_path)
        # 鑷姩娓呯悊鏃х姸鎬?
        self.clear_all_internal(skip_ui_confirm=True)
        self.load_file_content(file_path)
        
        # 寮€濮嬬炕璇?
        # 浣跨敤 root.after 纭繚 UI 鏇存柊鍚庡啀寮€濮?
        self.root.after(1000, self.start_translation)

    def clear_all_internal(self, skip_ui_confirm=False):
        """鍐呴儴娓呯┖鏂规硶锛屼緵鎵归噺妯″紡璋冪敤"""
        if not skip_ui_confirm and not messagebox.askyesno("纭", "纭畾瑕佹竻绌烘墍鏈夊唴瀹瑰悧?"):
            return
            
        self.file_path_var.set("")
        self.current_text = ""
        self.translated_text = ""
        self.source_segments = []
        self.translated_segments = []
        self.failed_segments = []
        self.selected_failed_index = None
        self.show_full_text = False
        self.original_text.delete('1.0', tk.END)
        self.translated_text_widget.delete('1.0', tk.END)
        self.progress_var.set(0)
        self.progress_text_var.set("灏辩华")
        self.file_info_var.set("")
        self.toggle_preview_btn.config(state='disabled', text="鏄剧ず瀹屾暣鍘熸枃")
        self.refresh_failed_segments_view()
        self.analysis_segments = []
        self.analysis_text.delete('1.0', tk.END)
        self.analysis_listbox.delete(0, tk.END)
        self.analysis_status_var.set("缈昏瘧瀹屾垚鍚庡彲杩涜瑙ｆ瀽")
        self.update_comparison_view()

    def update_concurrency_label(self, val):
        """鏇存柊骞跺彂鏁版爣绛惧拰鎻愮ず"""
        v = int(float(val))
        if v == 1:
            self.concurrency_label.config(text=f"{v} (楂樿川閲?")
            self.concurrency_hint_var.set("鍗曠嚎绋嬶細鍚敤涓婁笅鏂囪蹇嗭紝缈昏瘧璐ㄩ噺鏈€楂?)
        else:
            self.concurrency_label.config(text=f"{v} (楂橀€?")
            self.concurrency_hint_var.set("澶氱嚎绋嬶細閫熷害蹇紝浣嗘棤涓婁笅鏂囪蹇嗭紙鎺ㄨ崘灏忚/澶ф枃浠讹級")

    def on_api_type_change(self, event=None):
        """API绫诲瀷鏀瑰彉鏃舵洿鏂扮姸鎬?""
        self.update_api_status()

    def update_api_status(self):
        """鏇存柊API閰嶇疆鐘舵€?""
        api_type = self.get_current_api_type()
        config = self.api_configs.get(api_type, {})

        if config.get('api_key'):
            self.api_status_var.set("宸查厤缃?API Key")
            self.api_status_label.config(foreground="green")
        else:
            self.api_status_var.set("鏈厤缃?API Key")
            self.api_status_label.config(foreground="orange")

    def get_current_api_type(self):
        """鑾峰彇褰撳墠閫夋嫨鐨凙PI绫诲瀷"""
        api_name = self.api_type_var.get()
        api_map = {
            "Gemini API": "gemini",
            "OpenAI API": "openai",
            "鏈湴 LM Studio": "lm_studio",
            "鑷畾涔堿PI": "custom"
        }
        return api_map.get(api_name, "gemini")

    def get_target_language(self):
        """鑾峰彇鐢ㄦ埛璁剧疆鐨勭洰鏍囪瑷€"""
        target = (self.target_language_var.get() or "").strip()
        return target if target else DEFAULT_TARGET_LANGUAGE

    def is_target_language_chinese(self, target_language=None):
        """鍒ゆ柇鐩爣璇█鏄惁涓轰腑鏂?""
        target = (target_language or self.get_target_language() or "").lower()
        return any(key in target for key in ["涓枃", "姹夎", "chinese", "zh"])

    def is_target_language_english(self, target_language=None):
        """鍒ゆ柇鐩爣璇█鏄惁涓鸿嫳鏂?""
        target = (target_language or self.get_target_language() or "").lower()
        return any(key in target for key in ["鑻辨枃", "鑻辫", "english", "en"])

    def compute_text_signature(self, text):
        """璁＄畻鏂囨湰绛惧悕鐢ㄤ簬鏂偣鎭㈠"""
        return hashlib.md5(text.encode('utf-8')).hexdigest() if text else None

    def save_progress_cache(self):
        """淇濆瓨褰撳墠缈昏瘧杩涘害鍒扮鐩?""
        try:
            if not self.current_text or not self.source_segments:
                return

            data = {
                'file_path': self.file_path_var.get(),
                'signature': self.text_signature,
                'source_segments': self.source_segments,
                'translated_segments': self.translated_segments,
                'failed_segments': self.failed_segments,
                'lm_studio_fallback_active': self.lm_studio_fallback_active,
                'target_language': self.get_target_language(),
                'resume_from_index': len(self.translated_segments)
            }
            self.runtime_state.save_progress(data)
        except Exception as e:
            print(f"淇濆瓨杩涘害缂撳瓨澶辫触: {e}")

    def clear_progress_cache(self):
        """娓呴櫎缈昏瘧杩涘害缂撳瓨"""
        try:
            self.runtime_state.clear_progress()
        except Exception as e:
            print(f"娓呴櫎杩涘害缂撳瓨澶辫触: {e}")

    def try_resume_cached_progress(self):
        """鍚姩鏃舵鏌ュ苟璇㈤棶鏄惁鎭㈠鏈畬鎴愯繘搴?""
        try:
            cache = self.runtime_state.load_progress()
        except Exception as e:
            print(f"璇诲彇杩涘害缂撳瓨澶辫触: {e}")
            return

        if not cache:
            return

        file_path = cache.get('file_path')
        signature = cache.get('signature')
        if not file_path or not Path(file_path).exists():
            print("杩涘害缂撳瓨瀵瑰簲鐨勬枃浠朵笉瀛樺湪锛屽凡蹇界暐")
            self.clear_progress_cache()
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as rf:
                content = rf.read()
        except Exception as e:
            print(f"璇诲彇缂撳瓨鏂囦欢澶辫触: {e}")
            self.clear_progress_cache()
            return

        current_sig = self.compute_text_signature(content)
        if signature != current_sig:
            print("鏂囦欢鍐呭宸插彉鍖栵紝鏃犳硶鎭㈠杩涘害锛屽凡娓呴櫎缂撳瓨")
            self.clear_progress_cache()
            return

        # 鎭㈠鐘舵€?
        self.file_path_var.set(file_path)
        self.current_text = content
        self.text_signature = signature
        self.source_segments = cache.get('source_segments', [])
        self.translated_segments = cache.get('translated_segments', [])
        self.failed_segments = cache.get('failed_segments', [])
        self.lm_studio_fallback_active = cache.get('lm_studio_fallback_active', False)
        self.resume_from_index = cache.get('resume_from_index', len(self.translated_segments))
        cached_target = cache.get('target_language')
        if cached_target:
            self.target_language_var.set(cached_target)

        # 鏇存柊鐣岄潰鏄剧ず
        self.update_text_display()
        self.translated_text = "\n\n".join(self.translated_segments)
        self.update_translated_text(self.translated_text)

        total_segments = len(self.source_segments) or 1
        progress = (len(self.translated_segments) / total_segments) * 100
        self.progress_var.set(progress)
        self.progress_text_var.set(f"妫€娴嬪埌鏈畬鎴愮殑缈昏瘧杩涘害锛坽len(self.translated_segments)}/{total_segments} 娈碉級")

        continue_resume = messagebox.askyesno(
            "缁х画鏈畬鎴愮殑缈昏瘧",
            f"妫€娴嬪埌鏈畬鎴愮殑缈昏瘧浠诲姟锛歕n鏂囦欢: {Path(file_path).name}\n杩涘害: {len(self.translated_segments)}/{total_segments}\n\n鏄惁缁х画锛?
        )
        if not continue_resume:
            # 鏀惧純鎭㈠锛屾竻鐞嗙紦瀛樺苟閲嶇疆鐘舵€?
            self.clear_progress_cache()
            self.translated_segments = []
            self.source_segments = []
            self.failed_segments = []
            self.resume_from_index = 0
            self.translated_text = ""
            self.translated_text_widget.delete('1.0', tk.END)
            self.progress_var.set(0)
            self.progress_text_var.set("灏辩华")

    def open_api_config_for(self, purpose='translation'):
        """鎵撳紑API閰嶇疆瀵硅瘽妗嗭紙鏍规嵁缈昏瘧銆佽В鏋愭垨閲嶈瘯閫夋嫨锛?""
        if purpose == 'translation':
            api_type = self.get_translation_api_type()
        elif purpose == 'analysis':
            api_type = self.get_analysis_api_type()
        else:
            api_type = self.get_retry_api_type()

        # 濡傛灉鏄嚜瀹氫箟鏈湴妯″瀷锛屾墦寮€缂栬緫瀵硅瘽妗?
        if api_type in self.custom_local_models:
            self.open_edit_local_model_dialog(api_type)
        else:
            self.open_api_config(api_type)

    def open_add_local_model_dialog(self):
        """鎵撳紑娣诲姞鏈湴妯″瀷瀵硅瘽妗?""
        dialog = tk.Toplevel(self.root)
        dialog.title("娣诲姞鏈湴妯″瀷")
        dialog.geometry("480x320")
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(1, weight=1)

        # 妯″瀷鏄剧ず鍚嶇О
        ttk.Label(frame, text="鏄剧ず鍚嶇О:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=name_var, width=40).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        # Base URL
        ttk.Label(frame, text="Base URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        url_var = tk.StringVar(value="http://127.0.0.1:1234/v1")
        ttk.Entry(frame, textvariable=url_var, width=40).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        # Model ID
        ttk.Label(frame, text="Model ID:").grid(row=2, column=0, sticky=tk.W, pady=5)
        model_var = tk.StringVar()
        ttk.Entry(frame, textvariable=model_var, width=40).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        # API Key (鍙€?
        ttk.Label(frame, text="API Key:").grid(row=3, column=0, sticky=tk.W, pady=5)
        key_var = tk.StringVar(value="lm-studio")
        ttk.Entry(frame, textvariable=key_var, width=40).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        # 甯姪鏂囨湰
        ttk.Label(
            frame,
            text="鎻愮ず: 鏈湴妯″瀷浣跨敤OpenAI鍏煎鎺ュ彛鏍煎紡\n渚嬪 LM Studio, Ollama, vLLM 绛?,
            foreground="gray",
            justify=tk.LEFT
        ).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=10)

        def test_connection():
            """娴嬭瘯鏈湴妯″瀷杩炴帴"""
            if not OPENAI_SUPPORT:
                messagebox.showerror("閿欒", "缂哄皯 openai 搴擄紝鏃犳硶娴嬭瘯杩炴帴")
                return

            test_url = url_var.get().strip()
            test_model = model_var.get().strip()
            test_key = key_var.get().strip() or "lm-studio"

            if not test_url or not test_model:
                messagebox.showwarning("璀﹀憡", "璇峰～鍐?Base URL 鍜?Model ID")
                return

            try:
                client = openai.OpenAI(api_key=test_key, base_url=test_url)
                response = client.chat.completions.create(
                    model=test_model,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5
                )
                messagebox.showinfo("鎴愬姛", f"杩炴帴娴嬭瘯鎴愬姛!\n鍝嶅簲: {response.choices[0].message.content[:50]}")
            except Exception as e:
                messagebox.showerror("杩炴帴澶辫触", f"鏃犳硶杩炴帴鍒版湰鍦版ā鍨?\n{str(e)}")

        def save_model():
            name = name_var.get().strip()
            url = url_var.get().strip()
            model = model_var.get().strip()
            key = key_var.get().strip() or "lm-studio"

            if not name:
                messagebox.showwarning("璀﹀憡", "璇疯緭鍏ユ樉绀哄悕绉?)
                return
            if not url:
                messagebox.showwarning("璀﹀憡", "璇疯緭鍏?Base URL")
                return
            if not model:
                messagebox.showwarning("璀﹀憡", "璇疯緭鍏?Model ID")
                return

            try:
                self.add_custom_local_model(
                    name=name,
                    display_name=name,
                    base_url=url,
                    model_id=model,
                    api_key=key
                )
                messagebox.showinfo("鎴愬姛", f"鏈湴妯″瀷 '{name}' 宸叉坊鍔?)
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("閿欒", str(e))

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="娴嬭瘯杩炴帴", command=test_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="淇濆瓨", command=save_model).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="鍙栨秷", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def open_manage_local_models_dialog(self):
        """鎵撳紑绠＄悊鏈湴妯″瀷瀵硅瘽妗?""
        dialog = tk.Toplevel(self.root)
        dialog.title("绠＄悊鏈湴妯″瀷")
        dialog.geometry("550x400")
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        ttk.Label(frame, text="宸叉坊鍔犵殑鏈湴妯″瀷:", font=('', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        # 妯″瀷鍒楄〃妗嗘灦
        list_frame = ttk.Frame(frame)
        list_frame.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.E, tk.W), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        listbox = tk.Listbox(list_frame, height=12, font=('', 10))
        listbox.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        listbox.config(yscrollcommand=scrollbar.set)

        # 璇︽儏鏄剧ず
        detail_var = tk.StringVar(value="閫夋嫨涓€涓ā鍨嬫煡鐪嬭鎯?)
        detail_label = ttk.Label(frame, textvariable=detail_var, foreground="gray", wraplength=500, justify=tk.LEFT)
        detail_label.grid(row=2, column=0, sticky=tk.W, pady=(0, 10))

        def refresh_list():
            listbox.delete(0, tk.END)
            if not self.custom_local_models:
                listbox.insert(tk.END, "(鏆傛棤鑷畾涔夋湰鍦版ā鍨?")
                detail_var.set("鐐瑰嚮銆? 娣诲姞鏈湴妯″瀷銆嶆寜閽坊鍔犳柊妯″瀷")
                return

            for key, config in self.custom_local_models.items():
                listbox.insert(tk.END, f"{config['display_name']} ({config['base_url']})")

        def on_select(event=None):
            selection = listbox.curselection()
            if not selection or not self.custom_local_models:
                return

            keys = list(self.custom_local_models.keys())
            if selection[0] >= len(keys):
                return

            key = keys[selection[0]]
            config = self.custom_local_models[key]
            detail_var.set(
                f"鍚嶇О: {config['display_name']}\n"
                f"Base URL: {config['base_url']}\n"
                f"Model ID: {config['model_id']}\n"
                f"API Key: {config.get('api_key', 'lm-studio')}"
            )

        listbox.bind('<<ListboxSelect>>', on_select)

        def delete_selected():
            selection = listbox.curselection()
            if not selection or not self.custom_local_models:
                messagebox.showinfo("鎻愮ず", "璇峰厛閫夋嫨瑕佸垹闄ょ殑妯″瀷")
                return

            keys = list(self.custom_local_models.keys())
            if selection[0] >= len(keys):
                return

            key = keys[selection[0]]
            config = self.custom_local_models[key]

            if messagebox.askyesno("纭鍒犻櫎", f"纭畾鍒犻櫎妯″瀷 '{config['display_name']}'?"):
                self.remove_custom_local_model(key)
                refresh_list()
                detail_var.set("閫夋嫨涓€涓ā鍨嬫煡鐪嬭鎯?)

        def edit_selected():
            selection = listbox.curselection()
            if not selection or not self.custom_local_models:
                messagebox.showinfo("鎻愮ず", "璇峰厛閫夋嫨瑕佺紪杈戠殑妯″瀷")
                return

            keys = list(self.custom_local_models.keys())
            if selection[0] >= len(keys):
                return

            key = keys[selection[0]]
            dialog.destroy()
            self.open_edit_local_model_dialog(key)

        refresh_list()

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, sticky=tk.W)
        ttk.Button(btn_frame, text="缂栬緫", command=edit_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="鍒犻櫎", command=delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="鍏抽棴", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def open_edit_local_model_dialog(self, model_key):
        """鎵撳紑缂栬緫鏈湴妯″瀷瀵硅瘽妗?""
        if model_key not in self.custom_local_models:
            messagebox.showerror("閿欒", f"妯″瀷 '{model_key}' 涓嶅瓨鍦?)
            return

        config = self.custom_local_models[model_key]

        dialog = tk.Toplevel(self.root)
        dialog.title(f"缂栬緫鏈湴妯″瀷: {config['display_name']}")
        dialog.geometry("480x320")
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(1, weight=1)

        # 妯″瀷鏄剧ず鍚嶇О
        ttk.Label(frame, text="鏄剧ず鍚嶇О:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar(value=config['display_name'])
        ttk.Entry(frame, textvariable=name_var, width=40).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        # Base URL
        ttk.Label(frame, text="Base URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        url_var = tk.StringVar(value=config['base_url'])
        ttk.Entry(frame, textvariable=url_var, width=40).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        # Model ID
        ttk.Label(frame, text="Model ID:").grid(row=2, column=0, sticky=tk.W, pady=5)
        model_var = tk.StringVar(value=config['model_id'])
        ttk.Entry(frame, textvariable=model_var, width=40).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        # API Key
        ttk.Label(frame, text="API Key:").grid(row=3, column=0, sticky=tk.W, pady=5)
        key_var = tk.StringVar(value=config.get('api_key', 'lm-studio'))
        ttk.Entry(frame, textvariable=key_var, width=40).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        def test_connection():
            if not OPENAI_SUPPORT:
                messagebox.showerror("閿欒", "缂哄皯 openai 搴?)
                return
            try:
                client = openai.OpenAI(
                    api_key=key_var.get().strip() or "lm-studio",
                    base_url=url_var.get().strip()
                )
                response = client.chat.completions.create(
                    model=model_var.get().strip(),
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5
                )
                messagebox.showinfo("鎴愬姛", "杩炴帴娴嬭瘯鎴愬姛!")
            except Exception as e:
                messagebox.showerror("杩炴帴澶辫触", str(e))

        def save_changes():
            self.custom_local_models[model_key] = {
                'display_name': name_var.get().strip(),
                'base_url': url_var.get().strip(),
                'model_id': model_var.get().strip(),
                'api_key': key_var.get().strip() or "lm-studio",
                'created_at': config.get('created_at', '')
            }
            self.refresh_api_dropdowns()
            self.save_config()
            messagebox.showinfo("鎴愬姛", "妯″瀷閰嶇疆宸叉洿鏂?)
            dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="娴嬭瘯杩炴帴", command=test_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="淇濆瓨", command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="鍙栨秷", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def open_api_config(self, api_type=None):
        """鎵撳紑API閰嶇疆瀵硅瘽妗?""
        if api_type is None:
            api_type = self.get_current_api_type()
        config = self.api_configs[api_type]

        config_window = tk.Toplevel(self.root)
        config_window.title(f"{self.api_type_var.get()} 閰嶇疆")
        config_window.geometry("500x350")
        config_window.transient(self.root)
        config_window.grab_set()

        frame = ttk.Frame(config_window, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        frame.columnconfigure(1, weight=1)

        # API Key
        ttk.Label(frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=5)
        api_key_var = tk.StringVar(value=config.get('api_key', ''))
        ttk.Entry(frame, textvariable=api_key_var, width=50).grid(
            row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5
        )

        # Model
        ttk.Label(frame, text="妯″瀷:").grid(row=1, column=0, sticky=tk.W, pady=5)
        model_var = tk.StringVar(value=config.get('model', ''))
        ttk.Entry(frame, textvariable=model_var, width=50).grid(
            row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5
        )

        # Base URL (for OpenAI compatible APIs)
        if api_type in ['openai', 'custom', 'lm_studio', 'deepseek']:
            ttk.Label(frame, text="Base URL:").grid(row=2, column=0, sticky=tk.W, pady=5)
            base_url_var = tk.StringVar(value=config.get('base_url', ''))
            ttk.Entry(frame, textvariable=base_url_var, width=50).grid(
                row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5
            )
            ttk.Label(
                frame,
                text="(鍙€夛紝鐢ㄤ簬鑷畾涔夋湇鍔℃垨浠ｇ悊)",
                foreground="gray"
            ).grid(row=3, column=1, sticky=tk.W, pady=5)
        else:
            base_url_var = tk.StringVar(value='')

        # 璇存槑鏂囨湰
        help_text = {
            'gemini': "璇峰湪 Google AI Studio 鑾峰彇 API Key\n妯″瀷绀轰緥: gemini-2.5-flash, gemini-2.5-pro",
            'openai': "璇峰湪 OpenAI 鑾峰彇 API Key\n妯″瀷绀轰緥: gpt-3.5-turbo, gpt-4",
            'claude': "璇峰湪 Anthropic Console 鑾峰彇 API Key\n妯″瀷绀轰緥: claude-haiku-4-5-20251001",
            'deepseek': "璇峰湪 DeepSeek 寮€鏀惧钩鍙拌幏鍙?API Key\n妯″瀷绀轰緥: deepseek-chat",
            'custom': (
                "杈撳叆鍏煎OpenAI API鏍煎紡鐨勮嚜瀹氫箟鏈嶅姟\n"
                "Base URL绀轰緥: https://api.example.com/v1\n"
                "鏈湴LM Studio绀轰緥: http://127.0.0.1:1234/v1 (妯″瀷濡?qwen2.5-7b-instruct-1m)"
            ),
            'lm_studio': (
                "杩炴帴鏈湴 LM Studio 鎻愪緵鐨?OpenAI 鍏煎鎺ュ彛\n"
                "榛樿鍦板潃: http://127.0.0.1:1234/v1\n"
                "璇风‘淇?LM Studio Server 宸插惎鍔ㄥ苟鍔犺浇鐩爣妯″瀷"
            )
        }

        help_label = ttk.Label(
            frame,
            text=help_text.get(api_type, ''),
            foreground="gray",
            justify=tk.LEFT
        )
        help_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=10)

        # 娴嬭瘯杩炴帴鎸夐挳
        def test_connection():
            """娴嬭瘯API杩炴帴"""
            test_api_key = api_key_var.get().strip()
            test_model = model_var.get().strip()

            if not test_api_key:
                messagebox.showwarning("璀﹀憡", "璇峰厛杈撳叆API Key")
                return

            if not test_model:
                messagebox.showwarning("璀﹀憡", "璇峰厛杈撳叆妯″瀷鍚嶇О")
                return

            # 鏄剧ず娴嬭瘯涓彁绀?
            test_btn.config(state='disabled', text="娴嬭瘯涓?..")
            config_window.update()

            try:
                # 浣跨敤 TranslationEngine 鐨勬祴璇曞姛鑳?                test_engine = TranslationEngine()
                test_api_config = build_api_config(api_type, {
                    'api_key': test_api_key,
                    'model': test_model,
                    'base_url': base_url_var.get().strip(),
                    'temperature': 0.2,
                })
                if test_api_config is None:
                    raise ValueError("璇峰厛閰嶇疆鏈夋晥鐨?API Key")

                test_engine.add_api_config(api_type, test_api_config)
                success, msg = test_engine.test_connection(api_type)
                
                if success:
                    messagebox.showinfo("鎴愬姛", f"鉁?API杩炴帴娴嬭瘯鎴愬姛锛乗n\n{msg}")
                else:
                    messagebox.showerror("娴嬭瘯澶辫触", f"鉁?API杩炴帴娴嬭瘯澶辫触\n\n{msg}")

            except Exception as e:
                messagebox.showerror("娴嬭瘯澶辫触", f"鉁?API杩炴帴娴嬭瘯澶辫触\n\n閿欒: {str(e)}\n\n璇锋鏌ラ厤缃槸鍚︽纭?)

            finally:
                test_btn.config(state='normal', text="娴嬭瘯杩炴帴")

        # 淇濆瓨鎸夐挳
        def save_config():
            new_api_key = api_key_var.get().strip()
            new_model = model_var.get().strip()

            # 楠岃瘉杈撳叆
            if not new_api_key:
                messagebox.showwarning("璀﹀憡", "API Key涓嶈兘涓虹┖")
                return

            if not new_model:
                messagebox.showwarning("璀﹀憡", "妯″瀷鍚嶇О涓嶈兘涓虹┖")
                return

            # 淇濆瓨閰嶇疆
            self.api_configs[api_type]['api_key'] = new_api_key
            self.api_configs[api_type]['model'] = new_model
            if api_type in ['openai', 'custom', 'lm_studio', 'deepseek']:
                self.api_configs[api_type]['base_url'] = base_url_var.get().strip()

            # 鑷姩淇濆瓨鍒版枃浠?
            self.save_config(show_message=True)
            self.update_api_status()
            config_window.destroy()
            messagebox.showinfo("鎴愬姛", "鉁?API閰嶇疆宸蹭繚瀛榎n鉁?宸茶嚜鍔ㄥ垱寤哄浠絓n\n閰嶇疆灏嗗湪涓嬫鍚姩鏃惰嚜鍔ㄥ姞杞?)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)

        test_btn = ttk.Button(button_frame, text="娴嬭瘯杩炴帴", command=test_connection)
        test_btn.grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="淇濆瓨", command=save_config).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="鍙栨秷", command=config_window.destroy).grid(row=0, column=2, padx=5)

    def merge_api_configs(self, incoming_configs):
        """灏嗙鐩橀厤缃笌榛樿鍊煎悎骞讹紝纭繚鏂板瓧娈垫湁榛樿鍊?""
        incoming_configs = incoming_configs or {}

        for name, defaults in DEFAULT_API_CONFIGS.items():
            merged = deepcopy(defaults)
            merged.update(incoming_configs.get(name, {}))
            self.api_configs[name] = merged

        # 淇濈暀鏈煡鐨勬墿灞曢厤缃紝閬垮厤鎰忓涓㈠け
        for extra_key, extra_val in incoming_configs.items():
            if extra_key not in self.api_configs:
                self.api_configs[extra_key] = extra_val

    def migrate_config_v1_to_v2(self, old_config):
        """灏唙1閰嶇疆杩佺Щ鍒皏2鏍煎紡"""
        new_config = {
            'version': CONFIG_VERSION,
            'api_configs': old_config.get('api_configs', {}),
            'custom_local_models': {},
            'target_language': old_config.get('target_language', DEFAULT_TARGET_LANGUAGE),
            'selected_translation_api': 'Gemini API',
            'selected_analysis_api': 'Gemini API'
        }
        return new_config

    def get_all_available_apis(self):
        """鑾峰彇鎵€鏈夊彲鐢ㄧ殑API鍒楄〃锛堝唴缃?鑷畾涔夋湰鍦版ā鍨嬶級"""
        apis = []

        # 鍐呯疆API
        if GEMINI_SUPPORT:
            apis.append(("Gemini API", "gemini", "builtin"))
        if OPENAI_SUPPORT:
            apis.append(("OpenAI API", "openai", "builtin"))
            apis.append(("DeepSeek API", "deepseek", "builtin"))
            apis.append(("鏈湴 LM Studio", "lm_studio", "builtin"))
        if CLAUDE_SUPPORT:
            apis.append(("Claude API", "claude", "builtin"))
        if REQUESTS_SUPPORT:
            apis.append(("鑷畾涔堿PI", "custom", "builtin"))

        # 鑷畾涔夋湰鍦版ā鍨?
        for key, config in self.custom_local_models.items():
            display_name = config.get('display_name', key)
            apis.append((f"[鏈湴] {display_name}", key, "custom_local"))

        return apis

    def add_custom_local_model(self, name, display_name, base_url, model_id, api_key="lm-studio"):
        """娣诲姞鑷畾涔夋湰鍦版ā鍨?""
        from datetime import datetime

        # 鐢熸垚鍞竴閿悕
        key = name.lower().replace(" ", "_").replace("-", "_")
        if key in self.api_configs or key in self.custom_local_models:
            raise ValueError(f"妯″瀷鍚嶇О '{name}' 宸插瓨鍦?)

        self.custom_local_models[key] = {
            'display_name': display_name,
            'base_url': base_url,
            'model_id': model_id,
            'api_key': api_key,
            'created_at': datetime.now().isoformat()
        }

        # 鍒锋柊涓嬫媺妗?
        self.refresh_api_dropdowns()
        self.save_config()
        return key

    def remove_custom_local_model(self, key):
        """鍒犻櫎鑷畾涔夋湰鍦版ā鍨?""
        if key in self.custom_local_models:
            del self.custom_local_models[key]
            self.refresh_api_dropdowns()
            self.save_config()
            return True
        return False

    def refresh_api_dropdowns(self):
        """鍒锋柊缈昏瘧鍜岃В鏋愮殑API涓嬫媺妗?""
        apis = self.get_all_available_apis()
        api_names = [name for name, _, _ in apis]

        if hasattr(self, 'translation_api_combo'):
            current_trans = self.translation_api_var.get()
            self.translation_api_combo['values'] = api_names
            # 淇濇寔褰撳墠閫夋嫨锛屽鏋滀粛鐒舵湁鏁?
            if current_trans not in api_names and api_names:
                self.translation_api_var.set(api_names[0])

        if hasattr(self, 'analysis_api_combo'):
            current_analysis = self.analysis_api_var.get()
            self.analysis_api_combo['values'] = api_names
            if current_analysis not in api_names and api_names:
                self.analysis_api_var.set(api_names[0])

        if hasattr(self, 'retry_api_combo'):
            self.retry_api_combo['values'] = api_names
            preferred_retry = choose_retry_api_name(
                api_names,
                current_retry=self.retry_api_var.get(),
                translation_api_name=self.translation_api_var.get(),
            )
            if preferred_retry != self.retry_api_var.get():
                self.retry_api_var.set(preferred_retry)
        if hasattr(self, 'failed_segment_feature'):
            self.failed_segment_feature.update_retry_api_names(api_names)

    def _map_api_name_to_key(self, api_name):
        """灏嗘樉绀哄悕绉版槧灏勫埌API閿?""
        return map_api_name_to_key(api_name, self.custom_local_models)

    def ensure_retry_api_ready(self):
        """楠岃瘉澶辫触娈甸噸璇?API 鏄惁鍙敤锛涘繀瑕佹椂寮曞鐢ㄦ埛瀹屾垚閰嶇疆銆?""
        result = validate_retry_api_selection(
            api_name=self.retry_api_var.get(),
            api_configs=self.api_configs,
            custom_local_models=self.custom_local_models,
            openai_support=OPENAI_SUPPORT,
        )

        if result.is_ready:
            return result.api_type

        if result.error_message:
            if result.requires_user_action:
                messagebox.showwarning("璀﹀憡", result.error_message)
            else:
                messagebox.showerror("閿欒", result.error_message)

        if result.edit_local_model:
            self.open_edit_local_model_dialog(result.api_type)
        elif result.open_api_config:
            self.open_api_config(result.api_type)

        return None

    def get_translation_api_type(self):
        """鑾峰彇褰撳墠閫夋嫨鐨勭炕璇慉PI绫诲瀷"""
        api_name = self.translation_api_var.get()
        return self._map_api_name_to_key(api_name)

    def get_analysis_api_type(self):
        """鑾峰彇褰撳墠閫夋嫨鐨勮В鏋怉PI绫诲瀷"""
        api_name = self.analysis_api_var.get()
        return self._map_api_name_to_key(api_name)

    def get_retry_api_type(self):
        """鑾峰彇澶辫触娈佃惤閲嶈瘯鏃堕€夋嫨鐨凙PI绫诲瀷"""
        api_name = self.retry_api_var.get()
        return self._map_api_name_to_key(api_name)

    def _build_runtime_profile_payload(self):
        """鏋勫缓褰撳墠 GUI 闇€瑕佹寔涔呭寲鐨勯厤缃揩鐓с€?""
        return {
            'api_configs': deepcopy(self.api_configs),
            'custom_local_models': deepcopy(self.custom_local_models),
            'target_language': self.get_target_language(),
            'selected_translation_api': self.translation_api_var.get(),
            'selected_analysis_api': self.analysis_api_var.get(),
            'selected_retry_api': self.retry_api_var.get(),
        }

    def _apply_runtime_profile(self, profile):
        """灏嗛厤缃鐞嗗櫒涓殑杩愯鏃跺揩鐓у簲鐢ㄥ洖 GUI 鐘舵€併€?""
        profile = profile or {}
        self.merge_api_configs(profile.get('api_configs', {}))
        self.custom_local_models = profile.get('custom_local_models', {})

        target_language = profile.get('target_language', DEFAULT_TARGET_LANGUAGE)
        self.target_language_var.set(target_language or DEFAULT_TARGET_LANGUAGE)

        saved_trans_api = profile.get('selected_translation_api', DEFAULT_SELECTED_TRANSLATION_API)
        saved_analysis_api = profile.get('selected_analysis_api', DEFAULT_SELECTED_ANALYSIS_API)
        saved_retry_api = profile.get('selected_retry_api')
        self.translation_api_var.set(saved_trans_api)
        self.analysis_api_var.set(saved_analysis_api)

        default_retry_api = DEFAULT_SELECTED_RETRY_API if OPENAI_SUPPORT else saved_trans_api
        self.retry_api_var.set(saved_retry_api or default_retry_api)

    def save_config(self, show_message=False):
        """淇濆瓨閰嶇疆鍒扮敤鎴烽厤缃洰褰曘€?""
        try:
            translation_profile = {
                'target_language': self.get_target_language(),
                'translation_style': self.style_var.get() if hasattr(self, 'style_var') else self.saved_translation_style,
                'concurrency': self.concurrency_var.get() if hasattr(self, 'concurrency_var') else self.saved_concurrency,
                'segment_size': self.segment_size,
                'preview_limit': self.preview_limit,
                'max_consecutive_failures': self.max_consecutive_failures,
                'translation_delay': self.translation_delay,
                'use_translation_memory': self.use_translation_memory,
                'use_glossary': self.use_glossary,
                'context_enabled': self.context_enabled,
            }
            self.config_manager.update_translation_runtime_profile(translation_profile, save=False)

            payload = self._build_runtime_profile_payload()
            success = self.config_manager.update_ui_runtime_profile(
                api_configs=payload['api_configs'],
                custom_local_models=payload['custom_local_models'],
                target_language=payload['target_language'],
                selected_translation_api=payload['selected_translation_api'],
                selected_analysis_api=payload['selected_analysis_api'],
                selected_retry_api=payload['selected_retry_api'],
                create_backup=True,
            )
            if not success:
                raise RuntimeError('ConfigManager.save returned False')

            if show_message:
                print(f"鉁?閰嶇疆宸茶嚜鍔ㄤ繚瀛? {self.config_manager.config_path}")
        except Exception as e:
            error_msg = f"淇濆瓨閰嶇疆澶辫触: {e}"
            print(error_msg)
            if show_message:
                messagebox.showerror("閿欒", error_msg)

    def backup_config(self):
        """鍏煎鏃ц皟鐢紝澶囦唤宸茬敱 ConfigManager.save 缁熶竴澶勭悊銆?""
        try:
            self.config_manager.save(create_backup=True)
        except Exception as e:
            print(f"澶囦唤閰嶇疆澶辫触: {e}")

    def load_config(self):
        """浠庣敤鎴烽厤缃洰褰曞姞杞介厤缃€?""
        try:
            runtime_profile = self.config_manager.get_translation_runtime_profile()
            self.segment_size = int(runtime_profile.get('segment_size', 800) or 800)
            self.preview_limit = int(runtime_profile.get('preview_limit', 10000) or 10000)
            self.max_consecutive_failures = int(runtime_profile.get('max_consecutive_failures', 3) or 3)
            self.translation_delay = float(runtime_profile.get('translation_delay', 0.5) or 0.5)
            self.use_translation_memory = bool(runtime_profile.get('use_translation_memory', True))
            self.use_glossary = bool(runtime_profile.get('use_glossary', True))
            self.context_enabled = bool(runtime_profile.get('context_enabled', True))
            self.saved_translation_style = runtime_profile.get('translation_style', '閫氫織灏忚 (Novel)')
            self.saved_concurrency = int(runtime_profile.get('concurrency', 1) or 1)

            self._apply_runtime_profile(self.config_manager.get_ui_runtime_profile())

            if hasattr(self, 'style_var'):
                self.style_var.set(self.saved_translation_style)
            if hasattr(self, 'concurrency_var'):
                self.concurrency_var.set(self.saved_concurrency)
                self.update_concurrency_label(self.saved_concurrency)

            self.update_api_status()
            self.refresh_api_dropdowns()
            configured_count = len([k for k, v in self.api_configs.items() if v.get('api_key')])
            local_count = len(self.custom_local_models)
            print(f"鉁?閰嶇疆宸插姞杞? {configured_count} 涓狝PI宸查厤缃? {local_count} 涓嚜瀹氫箟鏈湴妯″瀷")
        except Exception as e:
            error_msg = f"鍔犺浇閰嶇疆澶辫触: {e}"
            print(error_msg)
            if self.restore_from_backup():
                print("鉁?宸蹭粠澶囦唤鎭㈠閰嶇疆")
            else:
                messagebox.showwarning("璀﹀憡", f"{error_msg}\n灏嗕娇鐢ㄩ粯璁ら厤缃?)

    def restore_from_backup(self):
        """浠庢渶鏂板浠芥仮澶嶉厤缃€?""
        try:
            if not self.config_manager._restore_from_backup():
                return False
            self.load_config()
            return True
        except Exception as e:
            print(f"浠庡浠芥仮澶嶅け璐? {e}")
            return False

    def on_closing(self):
        """绋嬪簭閫€鍑烘椂鐨勫鐞嗭紙鑷姩淇濆瓨閰嶇疆锛?""
        # 濡傛灉姝ｅ湪缈昏瘧锛岃闂敤鎴?
        if self.is_translating:
            if not messagebox.askyesno("纭閫€鍑?, "缈昏瘧姝ｅ湪杩涜涓紝纭畾瑕侀€€鍑哄悧锛焅n\n閰嶇疆灏嗚嚜鍔ㄤ繚瀛?):
                return

        # 鑷姩淇濆瓨閰嶇疆
        try:
            self.save_config(show_message=False)
            print("鉁?閰嶇疆宸茶嚜鍔ㄤ繚瀛?)
        except Exception as e:
            print(f"淇濆瓨閰嶇疆鏃跺嚭閿? {e}")

        # 鍏抽棴绐楀彛
        self.root.destroy()

    def start_translation(self):
        """寮€濮嬬炕璇?""
        if not self.current_text:
            messagebox.showwarning("璀﹀憡", "璇峰厛鍔犺浇瑕佺炕璇戠殑鏂囦欢")
            return

        api_type = self.get_translation_api_type()

        # 妫€鏌PI閰嶇疆锛氬唴缃瓵PI闇€瑕丄PI Key锛岃嚜瀹氫箟鏈湴妯″瀷闇€瑕侀厤缃?
        if api_type in self.custom_local_models:
            config = self.custom_local_models[api_type]
            if not config.get('base_url') or not config.get('model_id'):
                messagebox.showwarning("璀﹀憡", "璇峰厛閰嶇疆鏈湴妯″瀷鐨?Base URL 鍜?Model ID")
                self.open_edit_local_model_dialog(api_type)
                return
        else:
            config = self.api_configs.get(api_type, {})
            if not config.get('api_key'):
                messagebox.showwarning("璀﹀憡", "璇峰厛閰嶇疆API Key")
                self.open_api_config(api_type)
                return

        # 璁＄畻绛惧悕鐢ㄤ簬鏂偣鎭㈠鍒ゆ柇
        current_signature = self.compute_text_signature(self.current_text)
        resume_possible = (
            self.text_signature == current_signature
            and self.source_segments
            and 0 < len(self.translated_segments) < len(self.source_segments)
        )

        # 鏄惁浠庢柇鐐圭户缁?
        self.resume_from_index = 0
        if resume_possible:
            resume = messagebox.askyesno(
                "缁х画缈昏瘧",
                f"妫€娴嬪埌涓婃鏈畬鎴愮殑缈昏瘧锛屾槸鍚︿粠绗?{len(self.translated_segments) + 1} 娈电户缁紵"
            )
            if resume:
                self.resume_from_index = len(self.translated_segments)
                # 纭繚璇戞枃闀垮害涓庤捣濮嬫瀵归綈
                if len(self.translated_segments) > self.resume_from_index:
                    self.translated_segments = self.translated_segments[:self.resume_from_index]
            else:
                self.translated_segments = []
                self.source_segments = []
                self.failed_segments = []
        else:
            self.translated_segments = []
            self.source_segments = []
            self.failed_segments = []

        # 寮€濮嬬炕璇?
        self.lm_studio_fallback_active = False
        self.consecutive_failures = 0
        self.paused_due_to_failures = False
        self.is_translating = True
        self.translate_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.progress_var.set(
            (self.resume_from_index / max(len(self.source_segments), 1)) * 100
            if self.resume_from_index and self.source_segments else 0
        )
        if not self.resume_from_index:
            self.translated_text = ""
            self.translated_text_widget.delete('1.0', tk.END)
        self.failed_segments = []
        self.selected_failed_index = None
        self.refresh_failed_segments_view()

        # 鍦ㄦ柊绾跨▼涓墽琛岀炕璇?
        self.translation_thread = threading.Thread(target=self.translate_text, daemon=True)
        self.translation_thread.start()

    def stop_translation(self):
        """鍋滄缈昏瘧"""
        self.is_translating = False
        self.translate_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.progress_text_var.set("缈昏瘧宸插仠姝?)

    def sync_engine_config(self):
        """鍚屾閰嶇疆鍒扮炕璇戝紩鎿?""
        apply_runtime_config(
            self.translation_engine,
            self.api_configs,
            self.custom_local_models,
            clear_existing=True,
        )

    def translate_text(self):
        """鎵ц缈昏瘧锛堝湪鍚庡彴绾跨▼涓紝鏀寔骞跺彂锛?""
        try:
            # 鍚屾閰嶇疆鍒板紩鎿?
            self.sync_engine_config()
            
            # 鑾峰彇褰撳墠缈昏瘧API绫诲瀷
            api_type = self.get_translation_api_type()
            self.consecutive_failures = 0

            # 鍑嗗
            self.root.after(0, self.progress_text_var.set, "姝ｅ湪杩涜鏂囨湰鍒嗘...")

            # 浣跨敤 FileProcessor 杩涜鍒嗘
            self.source_segments = self.file_processor.split_text_into_segments(self.current_text, max_length=self.segment_size)
            total_segments = len(self.source_segments)
            self.text_signature = self.compute_text_signature(self.current_text)
            start_index = min(self.resume_from_index or 0, total_segments)

            self.root.after(0, self.progress_text_var.set, f"鏂囨湰宸插垎涓?{total_segments} 娈碉紝鍑嗗寮€濮嬬炕璇?..")
            if start_index:
                self.root.after(
                    0,
                    self.progress_var.set,
                    (start_index / total_segments) * 100 if total_segments else 0
                )
                self.root.after(
                    0,
                    self.progress_text_var.set,
                    f"缁х画缈昏瘧锛氫粠绗?{start_index + 1} 娈靛紑濮?.."
                )

            # 棰勫～鍏呯炕璇戝垪琛紝纭繚绱㈠紩瀵归綈
            if len(self.translated_segments) < total_segments:
                self.translated_segments.extend([""] * (total_segments - len(self.translated_segments)))

            # 鑾峰彇骞跺彂璁剧疆
            max_workers = self.concurrency_var.get()
            remaining_segments = max(total_segments - start_index, 0)
            max_workers = max(1, min(max_workers, remaining_segments or 1))
            if max_workers > 1:
                self.root.after(0, self.progress_text_var.set, f"姝ｅ湪骞跺彂缈昏瘧 (绾跨▼鏁? {max_workers})...")

            checkpoint_every = 1 if max_workers == 1 else 5

            def _translate_segment(idx, segment, context):
                return self.translate_segment(api_type, segment, context)

            def _on_progress(completed_count, total_count):
                progress = (completed_count / total_count) * 100 if total_count else 0
                self.root.after(0, self.progress_var.set, progress)
                self.root.after(0, self.progress_text_var.set, f"姝ｅ湪缈昏瘧... {completed_count}/{total_count} 娈?)

            def _on_checkpoint(translated_segments, completed_count):
                self.translated_segments = list(translated_segments)
                self.translated_text = "\n\n".join(seg for seg in self.translated_segments if seg)
                self.save_progress_cache()
                self.root.after(0, self.update_translated_text, self.translated_text)

            def _on_error(idx, error_text):
                print(f"缈昏瘧娈佃惤 {idx + 1} 澶辫触: {error_text}")

            executor = BatchTranslationExecutor(
                source_segments=self.source_segments,
                translated_segments=self.translated_segments,
                start_index=start_index,
                max_workers=max_workers,
                max_consecutive_failures=self.max_consecutive_failures,
                delay_seconds=self.translation_delay,
                checkpoint_every=checkpoint_every,
                use_context=self.context_enabled and max_workers == 1,
                should_continue=lambda: self.is_translating,
                translate_segment=_translate_segment,
                on_progress=_on_progress,
                on_checkpoint=_on_checkpoint,
                on_error=_on_error,
            )
            batch_result = executor.run()
            self.translated_segments = batch_result.translated_segments
            self.consecutive_failures = batch_result.consecutive_failures
            self.paused_due_to_failures = batch_result.paused_due_to_failures
            self.resume_from_index = batch_result.resume_from_index
            self.translated_text = "\n\n".join(seg for seg in self.translated_segments if seg)
            self.root.after(0, self.update_translated_text, self.translated_text)
            self.save_progress_cache()

            # 缈昏瘧瀹屾垚鍚庣殑澶勭悊
            if self.is_translating and not self.paused_due_to_failures:
                # 鏈€缁堟洿鏂颁竴娆″畬鏁存枃鏈?
                self.translated_text = "\n\n".join(self.translated_segments)
                self.root.after(0, self.update_translated_text, self.translated_text)
                
                self.root.after(0, self.progress_text_var.set, "姝ｅ湪妫€鏌ヨ瘧鏂?..")
                # 鏆傛椂鍙湪鍗曠嚎绋嬫ā寮忎笅閲嶈瘯锛屽苟鍙戞ā寮忎笅閲嶈瘯閫昏緫杈冨鏉?
                if max_workers == 1:
                    self.verify_and_retry_segments(api_type)

                self.root.after(0, self.refresh_failed_segments_view)
                self.root.after(0, self.progress_var.set, 100)
                
                failed_count = sum(1 for s in self.translated_segments if s.startswith("[缈昏瘧閿欒") or s.startswith("[鏈炕璇?))
                status_msg = (
                    f"缈昏瘧瀹屾垚锛屾湁 {failed_count} 娈靛彲鑳介渶瑕佹鏌?
                    if failed_count else "缈昏瘧瀹屾垚!"
                )
                self.root.after(0, self.progress_text_var.set, status_msg)
                self.root.after(0, self.on_translation_complete)
                if failed_count == 0:
                    self.clear_progress_cache()
            else:
                status_msg = "缈昏瘧宸插仠姝?
                if self.paused_due_to_failures:
                    status_msg = "宸叉殏鍋滐紝绛夊緟API鎭㈠鍚庡彲缁х画"
                self.root.after(0, self.progress_text_var.set, status_msg)

        except Exception as e:
            self.root.after(
                0,
                messagebox.showerror,
                "閿欒",
                f"缈昏瘧杩囩▼涓嚭閿?\n{str(e)}"
            )
        finally:
            self.root.after(0, self.translate_btn.config, {'state': 'normal'})
            self.root.after(0, self.stop_btn.config, {'state': 'disabled'})
            self.is_translating = False

    def detect_language(self, text):
        """绠€鍗曠殑璇█妫€娴嬶細妫€鏌ユ槸鍚︿富瑕佹槸涓枃"""
        if not text or len(text.strip()) == 0:
            return 'unknown'

        # 缁熻涓枃瀛楃
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(re.findall(r'\S', text))

        if total_chars == 0:
            return 'unknown'

        chinese_ratio = chinese_chars / total_chars

        # 濡傛灉涓枃鍗犳瘮瓒呰繃60%锛岃涓烘槸涓枃
        if chinese_ratio > 0.6:
            return 'zh'
        # 濡傛灉涓枃鍗犳瘮寰堜綆锛屽彲鑳芥槸鑻辨枃鎴栧叾浠栬瑷€
        elif chinese_ratio < 0.1:
            return 'en'
        else:
            return 'mixed'

    def translate_segment(self, api_type, text, context=None):
        """鎸夊綋鍓岮PI绫诲瀷缈昏瘧鍗曟鏂囨湰锛堜娇鐢ㄧ粺涓€缈昏瘧寮曟搸锛?""
        target_language = self.get_target_language()
        target_is_chinese = self.is_target_language_chinese(target_language)
        target_is_english = self.is_target_language_english(target_language)

        # 妫€娴嬭瑷€锛屽鏋滃凡缁忔槸鐩爣璇█灏辫烦杩囩炕璇?
        lang = self.detect_language(text)
        if (target_is_chinese and lang == 'zh') or (target_is_english and lang == 'en'):
            return text
            
        provider = resolve_provider_token(api_type, self.custom_local_models)

        # 鏋勫缓椋庢牸鎻愮ず
        style = self.style_var.get() if hasattr(self, 'style_var') else self.saved_translation_style
        style_prompt_map = {
            "鐩磋瘧 (Literal)": "璇疯繘琛岀簿鍑嗙洿璇戯紝涓ユ牸淇濈暀鍘熸枃鐨勫彞瀛愮粨鏋勫拰璇皵锛屼笉瑕佽繃搴︽剰璇戙€?,
            "閫氫織灏忚 (Novel)": "璇烽噰鐢ㄩ€氫織灏忚鐨勭瑪娉曪紝鐢ㄨ瘝鐢熷姩銆佹祦鐣咃紝娉ㄩ噸鎯呰妭鐨勮繛璐€у拰浜虹墿璇皵鐨勮嚜鐒讹紝绗﹀悎鐩爣璇█璇昏€呯殑闃呰涔犳儻銆?,
            "瀛︽湳涓撲笟 (Academic)": "璇烽噰鐢ㄥ鏈鏍硷紝鐢ㄨ瘝涓ヨ皑銆佷笓涓氾紝鍙ュ紡瑙勮寖锛岀‘淇濇湳璇噯纭紝閫傚悎瀛︽湳鐮旂┒鎴栦笓涓氫汉澹槄璇汇€?,
            "姝︿緺/鍙ら (Wuxia)": "璇烽噰鐢ㄤ腑鍥藉彜鍏告渚犳垨鍙ら灏忚鐨勭瑪瑙︼紝鐢ㄨ瘝鍏搁泤銆佸彜鏈达紝鍗婃枃鍗婄櫧锛屾敞閲嶆剰澧冪殑娓叉煋銆?,
            "鏂伴椈/濯掍綋 (News)": "璇烽噰鐢ㄦ柊闂绘姤閬撶殑椋庢牸锛屽瑙傘€佺畝缁冦€佷俊鎭紶杈惧噯纭紝绗﹀悎鏂伴椈濯掍綋鐨勮鑼冦€?
        }
        style_guide = style_prompt_map.get(style, "")
        if style_guide:
            style_guide = f"椋庢牸瑕佹眰锛歿style_guide}"
        
        # 璋冪敤缈昏瘧寮曟搸
        # 娉ㄦ剰锛歟ngine浼氳嚜鍔ㄥ鐞嗙炕璇戣蹇嗐€佹湳璇〃銆丄PI璋冪敤銆侀敊璇洖閫€
        result = self.translation_engine.translate(
            text=text,
            target_lang=target_language,
            provider=provider,
            use_memory=self.use_translation_memory,
            use_glossary=self.use_glossary,
            context=context,
            extra_prompt=style_guide
        )
        
        if result.success:
            return result.translated_text
        else:
            # 濡傛灉澶辫触锛屾姏鍑哄紓甯镐互渚夸笂灞傛崟鑾峰鐞嗭紙濡傝褰曞け璐ユ钀斤級
            raise Exception(result.error or "鏈煡缈昏瘧閿欒")



    def is_translation_incomplete(self, translated, source, target_language=None):
        """妫€娴嬭瘧鏂囨槸鍚﹀紓甯告垨鏈畬鎴?""
        target_language = target_language or self.get_target_language()
        target_is_chinese = self.is_target_language_chinese(target_language)
        target_is_english = self.is_target_language_english(target_language)

        if not translated or not translated.strip():
            return True

        normalized = translated.strip()
        if normalized.startswith("[缈昏瘧閿欒") or normalized.startswith("[鏈炕璇?) or normalized.startswith("[寰呮墜鍔ㄧ炕璇?):
            return True

        # 鏄庢樉杩囩煭鎴栦笌鍘熸枃鐩稿悓瑙嗕负鏈畬鎴?
        if len(normalized) < 5:
            return True
        if normalized == source.strip():
            return True

        min_length_ratio = 0.2 if target_is_chinese else 0.15
        if len(source) > 50 and len(normalized) < len(source) * min_length_ratio:
            return True

        # 璇█/瀛楃鍗犳瘮妫€鏌ワ細璇戞枃缂哄皯涓枃鎴栦粛浠ヨ嫳鏂?鏃ユ枃涓轰富鍒欒涓烘湭瀹屾垚
        def count_chars(text, pattern):
            return len(re.findall(pattern, text))

        chinese_chars = count_chars(normalized, r'[\u4e00-\u9fff]')
        latin_chars = count_chars(normalized, r'[A-Za-z]')
        japanese_chars = count_chars(normalized, r'[\u3040-\u30ff\u31f0-\u31ff]')
        total_chars = len(re.findall(r'\S', normalized)) or 1  # 閬垮厤闄?

        chinese_ratio = chinese_chars / total_chars
        latin_ratio = latin_chars / total_chars
        japanese_ratio = japanese_chars / total_chars

        source_has_latin = bool(re.search(r'[A-Za-z]', source))
        source_has_japanese = bool(re.search(r'[\u3040-\u30ff\u31f0-\u31ff]', source))

        if target_is_chinese:
            # 鍘熸枃鏄嫳鏂?鏃ユ枃锛屼笖璇戞枃涓枃姣斾緥浣庯紝鍒欏垽瀹氭湭瀹屾垚
            if source_has_latin and chinese_ratio < 0.2:
                return True
            if source_has_japanese and chinese_ratio < 0.2:
                return True

            # 璇戞枃鏁翠綋缂哄皯涓枃涓斾粛浠ヨ嫳鏂?鏃ユ枃涓轰富
            if chinese_ratio < 0.15 and (latin_ratio > 0.35 or japanese_ratio > 0.2):
                return True

            # 鏄庢樉浠ヨ嫳鏂囨垨鏃ユ枃鍗犱富瀵间篃瑙嗕负鏈畬鎴?
            if latin_ratio > 0.6 or japanese_ratio > 0.3:
                return True
        elif target_is_english:
            # 鑻辨枃鐩爣鏃讹紝濡傛灉璇戞枃浠嶄互涓枃涓轰富鎴栨槑鏄捐繃鐭垯瑙嗕负鏈畬鎴?
            if chinese_ratio > 0.3 and chinese_ratio > latin_ratio:
                return True
            if latin_ratio < 0.15 and len(source) > 50:
                return True
        else:
            # 鍏朵粬鐩爣璇█锛氬彧鍋氬熀纭€瀹屾暣鎬ф鏌ワ紝閬垮厤璇垽
            if chinese_ratio > 0.6 and target_language:
                return True

        return False

    def verify_and_retry_segments(self, api_type):
        """缈昏瘧瀹屾垚鍚庢鏌ュ苟鑷姩閲嶈瘯澶辫触娈佃惤"""
        failed = []
        target_language = self.get_target_language()
        for idx, (source, translated) in enumerate(zip(self.source_segments, self.translated_segments)):
            if self.is_translation_incomplete(translated, source, target_language=target_language):
                try:
                    retry_text = self.translate_segment(api_type, source)
                except Exception as e:
                    retry_text = f"[缈昏瘧閿欒: {str(e)}]\n{source}"

                if not self.is_translation_incomplete(retry_text, source, target_language=target_language):
                    self.translated_segments[idx] = retry_text
                else:
                    placeholder = f"[寰呮墜鍔ㄧ炕璇?- 娈?{idx + 1}]"
                    self.translated_segments[idx] = placeholder
                    failed.append({
                        'index': idx,
                        'source': source,
                        'last_error': translated
                    })

        self.failed_segments = failed
        self.save_progress_cache()

    def refresh_failed_segments_view(self):
        """鍒锋柊澶辫触娈佃惤鍒楄〃鍜岀姸鎬?""
        if hasattr(self, 'failed_segment_feature'):
            self.failed_segment_feature.refresh()

    def on_failed_select(self, event=None):
        """閫変腑澶辫触娈佃惤鏃跺睍绀鸿鎯?""
        if hasattr(self, 'failed_segment_feature'):
            self.failed_segment_feature.handle_selection()

    def get_selected_failed_segment(self):
        """杩斿洖褰撳墠閫変腑鐨勫け璐ユ淇℃伅銆?""
        if hasattr(self, 'failed_segment_feature'):
            return self.failed_segment_feature.get_selected_segment()
        return None

    def retry_failed_segment(self):
        """瀵归€変腑澶辫触娈佃惤閲嶆柊缈昏瘧"""
        self.failed_segment_feature.retry_selected()

    def save_manual_translation(self):
        """灏嗘墜鍔ㄨ瘧鏂囧啓鍥炲搴旀钀藉苟淇濆瓨鍒拌蹇嗗簱"""
        self.failed_segment_feature.save_manual_translation()

    def rebuild_translated_text(self):
        """鏍规嵁鍒嗘璇戞枃閲嶅缓瀹屾暣璇戞枃"""
        self.translated_text = "\n\n".join(self.translated_segments) if self.translated_segments else ""
        self.update_translated_text(self.translated_text)



    def update_translated_text(self, text):
        """鏇存柊璇戞枃鏄剧ず"""
        self.translated_text_widget.delete('1.0', tk.END)
        self.translated_text_widget.insert('1.0', text)
        # 鑷姩婊氬姩鍒板簳閮?
        self.translated_text_widget.see(tk.END)
        # 鍚屾鏇存柊瀵圭収瑙嗗浘
        self.update_comparison_view()

    def on_translation_complete(self):
        """缈昏瘧瀹屾垚鍚庣殑澶勭悊"""
        # 鍒锋柊瑙ｆ瀽鍒楄〃锛屼互渚跨敤鎴峰彲浠ヨ繘琛岃В鏋?
        self.refresh_analysis_listbox()
        # 纭繚瀵圭収瑙嗗浘涔熸槸鏈€鏂扮殑
        self.update_comparison_view()

        # 鎵归噺妯″紡澶勭悊
        if self.is_batch_mode:
            # 鑷姩瀵煎嚭
            self.auto_export_batch_file()
            # 鏍囪褰撳墠浠诲姟瀹屾垚
            for item in self.batch_queue:
                if item['status'] == 'processing':
                    item['status'] = 'done'
                    break
            self.save_batch_queue()
            # 缁х画涓嬩竴涓?
            self.root.after(2000, self.process_next_batch_file)
            return

        if self.failed_segments:
            self.notebook.select(4)  # 鍒囨崲鍒板け璐ユ钀芥爣绛鹃〉 (绱㈠紩: 0鎼滅储, 1鍘熸枃, 2璇戞枃, 3瀵圭収, 4澶辫触)
            message = f"缈昏瘧瀹屾垚锛屼絾 {len(self.failed_segments)} 涓钀介渶瑕佹墜鍔ㄧ炕璇戞垨閲嶈瘯銆?
            messagebox.showwarning("瀹屾垚", message)
        else:
            self.notebook.select(1)  # 鍒囨崲鍒拌瘧鏂囨爣绛鹃〉
            messagebox.showinfo("瀹屾垚", "缈昏瘧宸插畬鎴?")

    def auto_export_batch_file(self):
        """鎵归噺妯″紡涓嬬殑鑷姩瀵煎嚭"""
        if not self.batch_output_dir or not self.translated_text:
            return
            
        try:
            target_language = self.get_target_language()
            safe_lang = re.sub(r'[\\/:*?"<>|]', "_", target_language).strip()
            original_path = Path(self.file_path_var.get())
            
            # 瀵煎嚭绾枃鏈?
            txt_name = f"{original_path.stem}_{safe_lang}璇戞枃.txt"
            txt_path = Path(self.batch_output_dir) / txt_name
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(self.translated_text)
                
            print(f"鎵归噺瀵煎嚭鎴愬姛: {txt_path}")
            
        except Exception as e:
            print(f"鎵归噺瀵煎嚭澶辫触: {e}")
            # 鏍囪涓哄け璐ヤ絾缁х画
            for item in self.batch_queue:
                if item['status'] == 'processing':
                    item['status'] = 'failed'

    def export_translation(self):
        """瀵煎嚭缈昏瘧缁撴灉"""
        if not self.translated_text or not self.translated_text.strip():
            messagebox.showwarning("璀﹀憡", "娌℃湁鍙鍑虹殑璇戞枃\n\n璇峰厛瀹屾垚缈昏瘧鍚庡啀瀵煎嚭")
            return

        # 寤鸿榛樿鏂囦欢鍚?
        original_file = self.file_path_var.get()
        target_language = self.get_target_language()
        safe_lang = re.sub(r'[\\/:*?"<>|]', "_", target_language).strip() or "璇戞枃"
        
        # 鎵╁睍鍚嶅鐞?
        ext = ".txt"
        file_types = [("鏂囨湰鏂囦欢", "*.txt")]
        
        # 濡傛灉鏄?DOCX 涓斿鐞嗗櫒灏辩华锛岄粯璁ゅ鍑?DOCX
        if self.docx_handler and original_file.lower().endswith('.docx'):
            ext = ".docx"
            file_types = [("Word 鏂囨。", "*.docx"), ("鏂囨湰鏂囦欢", "*.txt")]

        if original_file:
            base_name = Path(original_file).stem
            default_name = f"{base_name}_{safe_lang}璇戞枃{ext}"
        else:
            default_name = f"{safe_lang}璇戞枃{ext}"

        filename = filedialog.asksaveasfilename(
            title="淇濆瓨璇戞枃",
            defaultextension=ext,
            initialfile=default_name,
            filetypes=file_types
        )

        if filename:
            try:
                # 妫€鏌ユ槸鍚﹀鍑轰负 DOCX
                if filename.lower().endswith('.docx') and self.docx_handler:
                    self.docx_handler.save_translated_file(self.translated_segments, filename)
                    messagebox.showinfo("鎴愬姛", f"鏍煎紡淇濈暀鐨?Word 鏂囨。宸蹭繚瀛樺埌:\n{filename}")
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(self.translated_text)
                    messagebox.showinfo("鎴愬姛", f"璇戞枃宸蹭繚瀛樺埌:\n{filename}")

                # 瀹屾暣瀵煎嚭鍚庢竻闄よ繘搴︾紦瀛?
                if self.source_segments and len(self.translated_segments) == len(self.source_segments):
                    self.clear_progress_cache()
            except Exception as e:
                messagebox.showerror("閿欒", f"淇濆瓨鏂囦欢澶辫触:\n{str(e)}")

    def export_audiobook(self):
        """瀵煎嚭鏈夊０涔?""
        if not self.translated_text:
            messagebox.showwarning("璀﹀憡", "娌℃湁鍙鍑虹殑璇戞枃")
            return
            
        ok, msg = self.audio_manager.check_dependency()
        if not ok:
            messagebox.showerror("閿欒", msg)
            return

        # 閫夋嫨璇煶瑙掕壊
        dialog = tk.Toplevel(self.root)
        dialog.title("瀵煎嚭鏈夊０涔?)
        dialog.geometry("400x200")
        
        ttk.Label(dialog, text="閫夋嫨璇煶瑙掕壊:").pack(pady=10)
        
        voices = self.audio_manager.get_voices()
        voice_var = tk.StringVar(value='zh-CN-XiaoxiaoNeural')
        voice_combo = ttk.Combobox(dialog, textvariable=voice_var, values=list(voices.keys()))
        voice_combo.pack(pady=5)
        
        # 鏄剧ず鍙嬪ソ鐨勫悕绉?
        name_label = ttk.Label(dialog, text=voices[voice_var.get()])
        name_label.pack(pady=5)
        
        def on_voice_change(event):
            name_label.config(text=voices.get(voice_var.get(), ""))
        voice_combo.bind('<<ComboboxSelected>>', on_voice_change)
        
        def do_export():
            output_path = filedialog.asksaveasfilename(
                title="淇濆瓨鏈夊０涔?,
                defaultextension=".mp3",
                filetypes=[("MP3 闊抽", "*.mp3")]
            )
            if not output_path:
                return
                
            dialog.destroy()
            
            # 鍚庡彴鐢熸垚
            def run_gen():
                self.progress_text_var.set("姝ｅ湪鐢熸垚鏈夊０涔?(杩欏彲鑳介渶瑕佸嚑鍒嗛挓)...")
                try:
                    self.audio_manager.generate_audiobook(
                        self.translated_text[:100000], # 闄愬埗闀垮害闃叉杩囬暱澶辫触锛屽疄闄呭簲鍒嗘
                        output_path, 
                        voice_var.get()
                    )
                    messagebox.showinfo("鎴愬姛", f"鏈夊０涔﹀凡鐢熸垚: {output_path}")
                except Exception as e:
                    messagebox.showerror("澶辫触", f"鐢熸垚澶辫触: {e}")
                finally:
                    self.progress_text_var.set("灏辩华")
                    
            threading.Thread(target=run_gen).start()
            
        ttk.Button(dialog, text="寮€濮嬬敓鎴?, command=do_export).pack(pady=20)

    def update_text_display(self):
        """鏇存柊鏂囨湰鏄剧ず锛堥瑙堟垨瀹屾暣锛?""
        if not self.current_text:
            return

        self.original_text.delete('1.0', tk.END)

        char_count = len(self.current_text)
        is_large_file = char_count > self.preview_limit

        if is_large_file and not self.show_full_text:
            # 鏄剧ず棰勮
            preview_text = self.current_text[:self.preview_limit]
            preview_text += f"\n\n{'='*60}\n"
            preview_text += f"鈿狅笍 棰勮妯″紡锛氫粎鏄剧ず鍓?{self.preview_limit:,} / {char_count:,} 瀛楃\n"
            preview_text += f"鐐瑰嚮涓婃柟'鏄剧ず瀹屾暣鍘熸枃'鎸夐挳鏌ョ湅鍏ㄦ枃\n"
            preview_text += f"{'='*60}"
            self.original_text.insert('1.0', preview_text)
        else:
            # 鏄剧ず瀹屾暣鏂囨湰
            self.original_text.insert('1.0', self.current_text)

    def toggle_full_text_display(self):
        """鍒囨崲鏄剧ず瀹屾暣鏂囨湰鎴栭瑙?""
        if not self.current_text:
            return

        self.show_full_text = not self.show_full_text
        char_count = len(self.current_text)

        if self.show_full_text:
            # 鍒囨崲鍒板畬鏁存樉绀?
            self.toggle_preview_btn.config(text="浠呮樉绀洪瑙?)
            self.file_info_var.set(f"鉁?鏄剧ず瀹屾暣鏂囦欢 ({char_count:,} 瀛楃)")
            self.progress_text_var.set("姝ｅ湪鍔犺浇瀹屾暣鏂囨湰...")
            self.root.update()

            # 浣跨敤after寤惰繜鏇存柊锛岄伩鍏嶇晫闈㈠喕缁?
            self.root.after(100, self._update_full_text)
        else:
            # 鍒囨崲鍒伴瑙?
            self.toggle_preview_btn.config(text="鏄剧ず瀹屾暣鍘熸枃")
            self.file_info_var.set(
                f"鈿狅笍 澶ф枃浠?({char_count:,} 瀛楃) - 浠呮樉绀哄墠 {self.preview_limit:,} 瀛楃"
            )
            self.update_text_display()
            self.progress_text_var.set(f"宸插姞杞芥枃浠?| 瀛楃鏁? {char_count:,}")

    def _update_full_text(self):
        """鏇存柊瀹屾暣鏂囨湰锛堝湪寤惰繜鍚庢墽琛岋級"""
        self.update_text_display()
        char_count = len(self.current_text)
        word_count = len(self.current_text.split())
        self.progress_text_var.set(
            f"宸插姞杞藉畬鏁存枃浠?| 瀛楃鏁? {char_count:,} | 璇嶆暟: {word_count:,}"
        )

    def clear_all(self):
        """娓呯┖鎵€鏈夊唴瀹?""
        self.clear_all_internal(skip_ui_confirm=False)

    # ==================== 瑙ｆ瀽鍔熻兘鏂规硶 ====================

    def refresh_analysis_listbox(self):
        """鍒锋柊瑙ｆ瀽鏍囩椤电殑娈佃惤鍒楄〃"""
        self.analysis_listbox.delete(0, tk.END)

        if not self.translated_segments:
            self.analysis_status_var.set("缈昏瘧瀹屾垚鍚庡彲杩涜瑙ｆ瀽")
            return

        # 鍒濆鍖栬В鏋愮粨鏋滃垪琛紙濡傛灉灏氭湭鍒濆鍖栨垨闀垮害涓嶅尮閰嶏級
        if len(self.analysis_segments) != len(self.translated_segments):
            self.analysis_segments = [''] * len(self.translated_segments)

        for i, seg in enumerate(self.translated_segments):
            # 鏄剧ず娈佃惤缂栧彿鍜岄瑙堬紙鍓?0瀛楃锛?
            preview = seg[:30].replace('\n', ' ') + ('...' if len(seg) > 30 else '')
            status = "鉁? if self.analysis_segments[i] else "鈼?
            self.analysis_listbox.insert(tk.END, f"{status} 娈佃惤 {i+1}: {preview}")

        analyzed_count = sum(1 for s in self.analysis_segments if s)
        total_count = len(self.translated_segments)
        self.analysis_status_var.set(f"宸茶В鏋?{analyzed_count}/{total_count} 娈?)

    def on_analysis_segment_select(self, event=None):
        """褰撶敤鎴烽€夋嫨瑙ｆ瀽鍒楄〃涓殑鏌愪竴娈垫椂锛屾樉绀哄搴斿唴瀹?""
        selection = self.analysis_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        if idx >= len(self.translated_segments):
            return

        # 鏄剧ず鍘熸枃銆佽瘧鏂囧拰瑙ｆ瀽锛堝鏋滄湁锛?
        source = self.source_segments[idx] if idx < len(self.source_segments) else ""
        translated = self.translated_segments[idx]
        analysis = self.analysis_segments[idx] if idx < len(self.analysis_segments) else ""

        self.analysis_text.delete('1.0', tk.END)
        self.analysis_text.insert(tk.END, f"銆愬師鏂囥€慭n{source}\n\n")
        self.analysis_text.insert(tk.END, f"銆愯瘧鏂囥€慭n{translated}\n\n")
        if analysis:
            self.analysis_text.insert(tk.END, f"銆愯В鏋愩€慭n{analysis}")
        else:
            self.analysis_text.insert(tk.END, '銆愯В鏋愩€慭n锛堝皻鏈В鏋愶紝鐐瑰嚮"瑙ｆ瀽閫変腑娈佃惤"鎸夐挳杩涜瑙ｆ瀽锛?)

    def analyze_selected_segment(self):
        """瑙ｆ瀽褰撳墠閫変腑鐨勫崟涓钀?""
        selection = self.analysis_listbox.curselection()
        if not selection:
            messagebox.showwarning("璀﹀憡", "璇峰厛鍦ㄥ垪琛ㄤ腑閫夋嫨涓€涓钀?)
            return

        idx = selection[0]
        if idx >= len(self.translated_segments):
            return

        # 妫€鏌ユ槸鍚︽鍦ㄨВ鏋?
        if self.is_analyzing:
            messagebox.showinfo("鎻愮ず", "姝ｅ湪瑙ｆ瀽涓紝璇风◢鍊?..")
            return

        self.analysis_status_var.set(f"姝ｅ湪瑙ｆ瀽娈佃惤 {idx+1}...")

        # 鍦ㄥ悗鍙扮嚎绋嬩腑鎵ц瑙ｆ瀽
        def analyze_worker():
            try:
                source = self.source_segments[idx] if idx < len(self.source_segments) else ""
                translated = self.translated_segments[idx]

                result = self.call_api_for_analysis(source, translated)

                # 淇濆瓨瑙ｆ瀽缁撴灉
                if idx < len(self.analysis_segments):
                    self.analysis_segments[idx] = result

                # 鏇存柊UI
                self.root.after(0, self._update_analysis_ui_after_single, idx, result)

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("瑙ｆ瀽澶辫触", f"瑙ｆ瀽娈佃惤 {idx+1} 鏃跺嚭閿?\n{e}"))
                self.root.after(0, lambda: self.analysis_status_var.set("瑙ｆ瀽澶辫触"))

        threading.Thread(target=analyze_worker, daemon=True).start()

    def _update_analysis_ui_after_single(self, idx, result):
        """鍗曟瑙ｆ瀽瀹屾垚鍚庢洿鏂癠I"""
        # 鍒锋柊鍒楄〃鏄剧ず鐘舵€?
        self.refresh_analysis_listbox()
        # 閲嶆柊閫変腑璇ユ钀藉苟鏄剧ず瑙ｆ瀽缁撴灉
        self.analysis_listbox.selection_clear(0, tk.END)
        self.analysis_listbox.selection_set(idx)
        self.analysis_listbox.see(idx)
        self.on_analysis_segment_select()

    def start_batch_analysis(self):
        """寮€濮嬫壒閲忚В鏋愭墍鏈夊凡缈昏瘧娈佃惤"""
        if not self.translated_segments:
            messagebox.showwarning("璀﹀憡", "璇峰厛瀹屾垚缈昏瘧鍚庡啀杩涜瑙ｆ瀽")
            return

        if self.is_analyzing:
            messagebox.showinfo("鎻愮ず", "姝ｅ湪瑙ｆ瀽涓紝璇风◢鍊?..")
            return

        if self.is_translating:
            messagebox.showwarning("璀﹀憡", "璇风瓑寰呯炕璇戝畬鎴愬悗鍐嶈繘琛岃В鏋?)
            return

        # 纭鏄惁瑕嗙洊宸叉湁瑙ｆ瀽
        existing_count = sum(1 for s in self.analysis_segments if s)
        if existing_count > 0:
            if not messagebox.askyesno("纭", f"宸叉湁 {existing_count} 娈佃В鏋愮粨鏋滐紝鏄惁鍏ㄩ儴閲嶆柊瑙ｆ瀽锛?):
                return

        # 鍒濆鍖栬В鏋愮粨鏋滃垪琛?
        self.analysis_segments = [''] * len(self.translated_segments)
        self.is_analyzing = True

        # 鏇存柊鎸夐挳鐘舵€?
        self.analyze_all_btn.config(state='disabled')
        self.stop_analysis_btn.config(state='normal')

        self.analysis_thread = threading.Thread(target=self._batch_analysis_worker, daemon=True)
        self.analysis_thread.start()

    def stop_analysis(self):
        """鍋滄鎵归噺瑙ｆ瀽"""
        if self.is_analyzing:
            self.is_analyzing = False
            self.analysis_status_var.set("姝ｅ湪鍋滄瑙ｆ瀽...")

    def _batch_analysis_worker(self):
        """鎵归噺瑙ｆ瀽鍚庡彴宸ヤ綔绾跨▼"""
        total = len(self.translated_segments)
        success_count = 0
        fail_count = 0

        for i, translated in enumerate(self.translated_segments):
            if not self.is_analyzing:
                # 鐢ㄦ埛鍙栨秷
                break

            source = self.source_segments[i] if i < len(self.source_segments) else ""

            self.root.after(0, lambda idx=i: self.analysis_status_var.set(f"姝ｅ湪瑙ｆ瀽 {idx+1}/{total}..."))
            self.root.after(0, lambda idx=i: self.progress_text_var.set(f"瑙ｆ瀽杩涘害: {idx+1}/{total}"))

            try:
                result = self.call_api_for_analysis(source, translated)
                self.analysis_segments[i] = result
                success_count += 1
            except Exception as e:
                print(f"瑙ｆ瀽娈佃惤 {i+1} 澶辫触: {e}")
                self.analysis_segments[i] = f"[瑙ｆ瀽澶辫触: {e}]"
                fail_count += 1

            # 鏇存柊杩涘害
            progress = (i + 1) / total * 100
            self.root.after(0, lambda p=progress: self.progress_var.set(p))

            # 姣忚В鏋愬畬涓€娈靛埛鏂板垪琛?
            self.root.after(0, self.refresh_analysis_listbox)

            # 閬垮厤API闄愭祦
            time.sleep(0.5)

        was_cancelled = not self.is_analyzing
        self.is_analyzing = False

        # 鎭㈠鎸夐挳鐘舵€?
        self.root.after(0, lambda: self.analyze_all_btn.config(state='normal'))
        self.root.after(0, lambda: self.stop_analysis_btn.config(state='disabled'))

        self.root.after(0, lambda: self.progress_var.set(100))
        if was_cancelled:
            self.root.after(0, lambda: self.analysis_status_var.set(
                f"瑙ｆ瀽宸插仠姝€傛垚鍔?{success_count} 娈碉紝澶辫触 {fail_count} 娈?
            ))
            self.root.after(0, lambda: self.progress_text_var.set("瑙ｆ瀽宸插仠姝?))
        else:
            self.root.after(0, lambda: self.analysis_status_var.set(
                f"瑙ｆ瀽瀹屾垚锛佹垚鍔?{success_count} 娈碉紝澶辫触 {fail_count} 娈?
            ))
            self.root.after(0, lambda: self.progress_text_var.set("瑙ｆ瀽瀹屾垚"))
        self.root.after(0, self.refresh_analysis_listbox)

    def call_api_for_analysis(self, source_text, translated_text):
        """璋冪敤API杩涜娈佃惤瑙ｆ瀽"""
        api_type = self.get_analysis_api_type()
        target_language = self.get_target_language()

        # 鏋勫缓瑙ｆ瀽鎻愮ず璇?
        prompt = f"""璇峰浠ヤ笅缈昏瘧鍐呭杩涜璇︾粏瑙ｆ瀽鍜岃瑙ｃ€?

銆愬師鏂囥€?
{source_text}

銆愯瘧鏂囥€?
{translated_text}

璇蜂粠浠ヤ笅瑙掑害杩涜瑙ｆ瀽锛?
1. 鍐呭姒傝锛氱畝瑕佹鎷繖娈垫枃瀛楃殑涓昏鍐呭
2. 鍏抽敭淇℃伅锛氭寚鍑哄叾涓殑鍏抽敭姒傚康銆佷汉鐗┿€佷簨浠舵垨璁虹偣
3. 缈昏瘧璇存槑锛氬鏈夌壒娈婃湳璇垨琛ㄨ揪锛岃鏄庣炕璇戠殑澶勭悊鏂瑰紡
4. 寤朵几鎬濊€冿細鎻愪緵鐩稿叧鐨勮儗鏅煡璇嗘垨鎬濊€冭搴?

璇风敤{target_language}鍥炵瓟銆?""

        # 鏍规嵁API绫诲瀷璋冪敤瀵瑰簲鐨勮В鏋愭柟娉?
        if api_type in self.custom_local_models:
            return self._analyze_with_custom_local_model(api_type, prompt)
        elif api_type == 'gemini':
            return self._analyze_with_gemini(prompt)
        elif api_type == 'openai':
            return self._analyze_with_openai(prompt)
        elif api_type == 'custom':
            return self._analyze_with_custom_api(prompt)
        elif api_type == 'lm_studio':
            return self._analyze_with_lm_studio(prompt)
        else:
            raise ValueError(f"涓嶆敮鎸佺殑瑙ｆ瀽API绫诲瀷: {api_type}")

    def _analyze_with_custom_local_model(self, model_key, prompt):
        """浣跨敤鑷畾涔夋湰鍦版ā鍨嬭繘琛岃В鏋?""
        if not OPENAI_SUPPORT:
            raise ImportError("缂哄皯 openai 搴擄紝鏃犳硶璋冪敤鏈湴妯″瀷")

        if model_key not in self.custom_local_models:
            raise ValueError(f"鏈湴妯″瀷 '{model_key}' 鏈厤缃?)

        config = self.custom_local_models[model_key]

        client = openai.OpenAI(
            api_key=config.get('api_key', 'lm-studio'),
            base_url=config['base_url']
        )

        response = client.chat.completions.create(
            model=config['model_id'],
            messages=[
                {"role": "system", "content": "浣犳槸涓€涓笓涓氱殑鏂囨湰鍒嗘瀽鍔╂墜锛屾搮闀垮缈昏瘧鍐呭杩涜娣卞害瑙ｆ瀽鍜岃瑙ｃ€?},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        return response.choices[0].message.content

    def _analyze_with_gemini(self, prompt):
        """浣跨敤Gemini API杩涜瑙ｆ瀽"""
        if not GEMINI_SUPPORT:
            raise ImportError("缂哄皯 google-generativeai 搴?)

        api_key = self.api_configs['gemini'].get('api_key', '')
        model_name = self.api_configs['gemini'].get('model', 'gemini-2.5-flash')

        if not api_key:
            raise ValueError("鏈厤缃?Gemini API Key")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)

        return response.text

    def _analyze_with_openai(self, prompt):
        """浣跨敤OpenAI API杩涜瑙ｆ瀽"""
        if not OPENAI_SUPPORT:
            raise ImportError("缂哄皯 openai 搴?)

        api_key = self.api_configs['openai'].get('api_key', '')
        model_name = self.api_configs['openai'].get('model', 'gpt-3.5-turbo')
        base_url = self.api_configs['openai'].get('base_url', '')

        if not api_key:
            raise ValueError("鏈厤缃?OpenAI API Key")

        client_kwargs = {'api_key': api_key}
        if base_url:
            client_kwargs['base_url'] = base_url

        client = openai.OpenAI(**client_kwargs)
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "浣犳槸涓€涓笓涓氱殑鏂囨湰鍒嗘瀽鍔╂墜锛屾搮闀垮缈昏瘧鍐呭杩涜娣卞害瑙ｆ瀽鍜岃瑙ｃ€?},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        return response.choices[0].message.content

    def _analyze_with_custom_api(self, prompt):
        """浣跨敤鑷畾涔堿PI杩涜瑙ｆ瀽"""
        if not REQUESTS_SUPPORT:
            raise ImportError("缂哄皯 requests 搴?)

        api_key = self.api_configs['custom'].get('api_key', '')
        model_name = self.api_configs['custom'].get('model', '')
        base_url = self.api_configs['custom'].get('base_url', '')

        if not base_url:
            raise ValueError("鏈厤缃嚜瀹氫箟API鍦板潃")

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "浣犳槸涓€涓笓涓氱殑鏂囨湰鍒嗘瀽鍔╂墜锛屾搮闀垮缈昏瘧鍐呭杩涜娣卞害瑙ｆ瀽鍜岃瑙ｃ€?},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }

        response = requests.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=data,
            timeout=120
        )
        response.raise_for_status()

        result = response.json()
        return result['choices'][0]['message']['content']

    def _analyze_with_lm_studio(self, prompt):
        """浣跨敤LM Studio鏈湴妯″瀷杩涜瑙ｆ瀽"""
        if not OPENAI_SUPPORT:
            raise ImportError("缂哄皯 openai 搴?)

        config = self.api_configs.get('lm_studio', DEFAULT_LM_STUDIO_CONFIG)

        client = openai.OpenAI(
            api_key=config.get('api_key', 'lm-studio'),
            base_url=config.get('base_url', 'http://127.0.0.1:1234/v1')
        )

        response = client.chat.completions.create(
            model=config.get('model', 'qwen2.5-7b-instruct-1m'),
            messages=[
                {"role": "system", "content": "浣犳槸涓€涓笓涓氱殑鏂囨湰鍒嗘瀽鍔╂墜锛屾搮闀垮缈昏瘧鍐呭杩涜娣卞害瑙ｆ瀽鍜岃瑙ｃ€?},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        return response.choices[0].message.content

    def copy_analysis_content(self):
        """澶嶅埗瑙ｆ瀽鍐呭鍒板壀璐存澘"""
        content = self.analysis_text.get('1.0', tk.END).strip()
        if not content:
            messagebox.showinfo("鎻愮ず", "娌℃湁鍙鍒剁殑鍐呭")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("鎴愬姛", "宸插鍒跺埌鍓创鏉?)

    def export_analysis(self):
        """瀵煎嚭瑙ｆ瀽缁撴灉"""
        if not self.analysis_segments or not any(self.analysis_segments):
            messagebox.showwarning("璀﹀憡", "娌℃湁鍙鍑虹殑瑙ｆ瀽鍐呭\n璇峰厛瀹屾垚娈佃惤瑙ｆ瀽")
            return

        # 鐢熸垚榛樿鏂囦欢鍚?
        original_file = self.file_path_var.get()
        if original_file:
            base_name = Path(original_file).stem
            default_name = f"{base_name}_瑙ｆ瀽.txt"
        else:
            default_name = "瑙ｆ瀽缁撴灉.txt"

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("鏂囨湰鏂囦欢", "*.txt"), ("鎵€鏈夋枃浠?, "*.*")],
            initialfile=default_name,
            title="瀵煎嚭瑙ｆ瀽缁撴灉"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("涔︾睄缈昏瘧宸ュ叿 - 娈佃惤瑙ｆ瀽缁撴灉\n")
                f.write("=" * 60 + "\n\n")

                for i, (source, translated, analysis) in enumerate(zip(
                    self.source_segments,
                    self.translated_segments,
                    self.analysis_segments
                )):
                    f.write(f"{'='*40}\n")
                    f.write(f"娈佃惤 {i+1}\n")
                    f.write(f"{'='*40}\n\n")
                    f.write(f"銆愬師鏂囥€慭n{source}\n\n")
                    f.write(f"銆愯瘧鏂囥€慭n{translated}\n\n")
                    f.write(f"銆愯В鏋愩€慭n{analysis if analysis else '锛堟湭瑙ｆ瀽锛?}\n\n")

            analyzed_count = sum(1 for s in self.analysis_segments if s)
            total_count = len(self.analysis_segments)
            messagebox.showinfo(
                "瀵煎嚭鎴愬姛",
                f"瑙ｆ瀽缁撴灉宸蹭繚瀛樺埌:\n{file_path}\n\n"
                f"鍏?{total_count} 娈碉紝宸茶В鏋?{analyzed_count} 娈?
            )

        except Exception as e:
            messagebox.showerror("瀵煎嚭澶辫触", f"淇濆瓨鏂囦欢鏃跺嚭閿?\n{e}")

    def export_bilingual_epub(self):
        """瀵煎嚭鍙岃瀵圭収 EPUB 鐢靛瓙涔?""
        if not self.translated_segments:
            messagebox.showwarning("璀﹀憡", "娌℃湁鍙鍑虹殑璇戞枃")
            return

        # 妫€鏌ユ槸鍚﹀畨瑁呬簡 ebooklib
        if not EPUB_SUPPORT:
            messagebox.showerror("閿欒", "鏈畨瑁?ebooklib 搴擄紝鏃犳硶瀵煎嚭 EPUB銆俓n璇疯繍琛?py -m pip install ebooklib")
            return

        # 閫夋嫨淇濆瓨璺緞
        original_file = self.file_path_var.get()
        default_name = f"{Path(original_file).stem}_鍙岃鐗?epub" if original_file else "鍙岃涔︾睄.epub"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".epub",
            filetypes=[("EPUB 鐢靛瓙涔?, "*.epub")],
            initialfile=default_name,
            title="瀵煎嚭鍙岃 EPUB"
        )
        
        if not file_path:
            return

        try:
            # 鍒涘缓 EPUB 涔︾睄
            book = epub.EpubBook()
            
            # 璁剧疆鍏冩暟鎹?
            title = Path(original_file).stem if original_file else "Translation"
            book.set_identifier(str(uuid.uuid4()))
            book.set_title(f"{title} (鍙岃鐗?")
            book.set_language(self.get_target_language())
            book.add_author("Book Translator AI")

            # 鍒涘缓绔犺妭
            chapters = []
            # 灏嗘瘡 50 娈典綔涓轰竴涓珷鑺傦紝閬垮厤鍗曢〉杩囬暱
            chunk_size = 50
            total_segments = len(self.source_segments)
            
            # 绠€鍗曠殑 CSS 鏍峰紡
            style = """
                body { font-family: sans-serif; }
                .segment { margin-bottom: 1.5em; border-bottom: 1px dashed #ccc; padding-bottom: 1em; }
                .original { color: #666; font-size: 0.9em; margin-bottom: 0.5em; }
                .translation { color: #000; font-size: 1.0em; font-weight: bold; }
            """
            css_item = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
            book.add_item(css_item)

            for i in range(0, total_segments, chunk_size):
                chunk_source = self.source_segments[i:i+chunk_size]
                chunk_trans = self.translated_segments[i:i+chunk_size]
                
                # 纭繚闀垮害涓€鑷?
                if len(chunk_trans) < len(chunk_source):
                    chunk_trans.extend([""] * (len(chunk_source) - len(chunk_trans)))

                # 鏋勫缓 HTML 鍐呭
                html_content = ["<h1>绗?{} 閮ㄥ垎</h1>".format(i // chunk_size + 1)]
                for src, trans in zip(chunk_source, chunk_trans):
                    # 澶勭悊鎹㈣绗?
                    src_html = src.replace("\n", "<br/>")
                    trans_html = trans.replace("\n", "<br/>")
                    
                    html_content.append(f"""
                    <div class="segment">
                        <div class="original">{src_html}</div>
                        <div class="translation">{trans_html}</div>
                    </div>
                    """)

                chapter = epub.EpubHtml(title=f"Part {i // chunk_size + 1}", file_name=f"part_{i // chunk_size + 1}.xhtml", lang='zh')
                chapter.content = "".join(html_content)
                chapter.add_item(css_item)
                
                book.add_item(chapter)
                chapters.append(chapter)

            # 瀹氫箟涔︾睄楠ㄦ灦
            book.toc = tuple(chapters)
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            book.spine = ['nav'] + chapters

            # 淇濆瓨鏂囦欢
            epub.write_epub(file_path, book, {})
            
            messagebox.showinfo("鎴愬姛", f"鍙岃 EPUB 宸插鍑?\n{file_path}")

        except Exception as e:
            messagebox.showerror("瀵煎嚭澶辫触", f"鐢熸垚 EPUB 鏃跺嚭閿?\n{e}")

    # --- 鍦ㄧ嚎鎼滅储鐩稿叧鏂规硶 ---
    def setup_search_tab(self):
        """璁剧疆鍦ㄧ嚎涔﹀煄锛氬寘鍚?'鍏ㄧ綉鎼滅储' 鍜?'绀惧尯鍥句功棣? 涓や釜瀛愭爣绛?""
        
        # 鍒涘缓瀛?Notebook
        self.library_notebook = ttk.Notebook(self.library_frame)
        self.library_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 1. 鍏ㄧ綉鎼滅储 Tab (鍘熸湁鐨勫姛鑳?
        search_tab_frame = ttk.Frame(self.library_notebook)
        self.library_notebook.add(search_tab_frame, text="鍏ㄧ綉鎼滅储 (Z-Lib/Anna)")
        
        self._build_global_search_ui(search_tab_frame)
        
        # 2. 绀惧尯鍥句功棣?Tab (鏂板姛鑳?
        community_tab_frame = ttk.Frame(self.library_notebook)
        self.library_notebook.add(community_tab_frame, text="绀惧尯鍥句功棣?(Community Library)")
        
        self._build_community_ui(community_tab_frame)

    def _build_community_ui(self, parent):
        """鏋勫缓绀惧尯鍥句功棣?UI"""
        # 宸ュ叿鏍?
        toolbar = ttk.Frame(parent, padding=10)
        toolbar.pack(fill=tk.X)
        
        ttk.Label(toolbar, text="馃摎 绀惧尯鍏变韩涔︾睄", font=("", 12, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.comm_status_var = tk.StringVar(value="灏辩华")
        ttk.Label(toolbar, textvariable=self.comm_status_var, foreground="gray").pack(side=tk.LEFT, padx=10)
        
        # 鎸夐挳缁?
        btn_frame = ttk.Frame(toolbar)
        btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(btn_frame, text="鍒锋柊鍒楄〃", command=self.refresh_community_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="馃摛 涓婁紶鍒嗕韩", command=self.open_community_upload).pack(side=tk.LEFT, padx=5)
        
        # 绠＄悊鍛樺叆鍙?
        self.admin_btn = ttk.Button(btn_frame, text="馃洝锔?鍥句功棣嗙鐞?, command=self.open_admin_audit)
        self.admin_btn.pack(side=tk.LEFT, padx=5)
        
        # 鍒楄〃鍖哄煙
        columns = ("title", "author", "description", "uploader", "size", "date")
        self.comm_tree = ttk.Treeview(parent, columns=columns, show="headings")
        
        self.comm_tree.heading("title", text="鏍囬")
        self.comm_tree.heading("author", text="浣滆€?)
        self.comm_tree.heading("description", text="绠€浠?)
        self.comm_tree.heading("uploader", text="涓婁紶鑰?)
        self.comm_tree.heading("size", text="澶у皬")
        self.comm_tree.heading("date", text="鏃ユ湡")
        
        self.comm_tree.column("title", width=200)
        self.comm_tree.column("author", width=100)
        self.comm_tree.column("description", width=300)
        self.comm_tree.column("uploader", width=80)
        self.comm_tree.column("size", width=80)
        self.comm_tree.column("date", width=100)
        
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.comm_tree.yview)
        self.comm_tree.configure(yscrollcommand=scrollbar.set)
        
        self.comm_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # 鍙抽敭鑿滃崟
        self.comm_menu = tk.Menu(parent, tearoff=0)
        self.comm_menu.add_command(label="涓嬭浇骞跺鍏?, command=self.download_community_book)
        self.comm_menu.add_command(label="澶嶅埗閾炬帴", command=self.copy_community_link)
        
        self.comm_tree.bind("<Button-3>", lambda e: self.comm_menu.post(e.x_root, e.y_root))
        self.comm_tree.bind("<Double-1>", lambda e: self.download_community_book())
        
        # 鍒濆鍔犺浇
        self.refresh_community_list()

    def refresh_community_list(self):
        """鍒锋柊绀惧尯涔︾睄鍒楄〃"""
        self.comm_tree.delete(*self.comm_tree.get_children())
        try:
            books = self.community_manager.get_public_books()
            for b in books:
                self.comm_tree.insert("", "end", values=(
                    b.get('title', 'Unknown'),
                    b.get('author', 'Unknown'),
                    b.get('description', ''),
                    b.get('uploader', 'Anon'),
                    b.get('size', ''),
                    b.get('date', '')
                ), tags=(b['url'],)) # Store URL in tag
        except Exception as e:
            messagebox.showerror("鍒锋柊澶辫触", str(e))

    def download_community_book(self):
        """涓嬭浇绀惧尯涔︾睄"""
        selected = self.comm_tree.selection()
        if not selected: return
        item = self.comm_tree.item(selected[0])
        url = self.comm_tree.item(selected[0], "tags")[0]
        title = item['values'][0]
        
        if messagebox.askyesno("涓嬭浇", f"纭畾涓嬭浇涔︾睄: {title}?"):
            try:
                # Reuse web importer logic or simple download
                self.progress_text_var.set(f"姝ｅ湪涓嬭浇: {title}...")
                
                def run():
                    try:
                        resp = requests.get(url)
                        if resp.status_code == 200:
                            # Save to temp
                            ext = ".pdf" if url.endswith(".pdf") else ".txt" # Simple heuristic
                            if "epub" in url: ext = ".epub"
                            
                            path = Path("downloads") / f"{title}{ext}"
                            path.parent.mkdir(exist_ok=True)
                            
                            with open(path, 'wb') as f:
                                f.write(resp.content)
                                
                            self.root.after(0, lambda: self._load_downloaded_book(str(path)))
                        else:
                            raise Exception(f"Download failed: {resp.status_code}")
                    except Exception as e:
                        self.root.after(0, lambda: messagebox.showerror("閿欒", str(e)))
                
                threading.Thread(target=run, daemon=True).start()
                
            except Exception as e:
                messagebox.showerror("閿欒", str(e))

    def _load_downloaded_book(self, path):
        if messagebox.askyesno("涓嬭浇瀹屾垚", "涓嬭浇鎴愬姛锛佹槸鍚︾珛鍗冲姞杞界炕璇戯紵"):
            self.file_path_var.set(path)
            self.load_file_content(path)
            # Switch to Workstation tab
            self.main_notebook.select(0)

    def copy_community_link(self):
        selected = self.comm_tree.selection()
        if not selected: return
        url = self.comm_tree.item(selected[0], "tags")[0]
        self.root.clipboard_clear()
        self.root.clipboard_append(url)

    def open_community_upload(self):
        """鎵撳紑涓婁紶鍒嗕韩瀵硅瘽妗?""
        dialog = tk.Toplevel(self.root)
        dialog.title("涓婁紶涔︾睄鍒扮ぞ鍖?)
        dialog.geometry("500x450")
        
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="1. 閫夋嫨鏂囦欢").pack(anchor=tk.W)
        file_var = tk.StringVar()
        f_entry = ttk.Entry(frame, textvariable=file_var)
        f_entry.pack(fill=tk.X)
        ttk.Button(frame, text="娴忚", command=lambda: file_var.set(filedialog.askopenfilename())).pack(anchor=tk.E, pady=2)
        
        ttk.Label(frame, text="2. 涔︾睄淇℃伅").pack(anchor=tk.W, pady=(10, 0))
        
        ttk.Label(frame, text="鏍囬:").pack(anchor=tk.W)
        title_var = tk.StringVar()
        ttk.Entry(frame, textvariable=title_var).pack(fill=tk.X)
        
        ttk.Label(frame, text="浣滆€?").pack(anchor=tk.W)
        author_var = tk.StringVar()
        ttk.Entry(frame, textvariable=author_var).pack(fill=tk.X)
        
        ttk.Label(frame, text="绠€浠?").pack(anchor=tk.W)
        desc_var = tk.StringVar()
        ttk.Entry(frame, textvariable=desc_var).pack(fill=tk.X)
        
        ttk.Label(frame, text="涓婁紶鑰呮樀绉?").pack(anchor=tk.W)
        user_var = tk.StringVar(value="Anonymous")
        ttk.Entry(frame, textvariable=user_var).pack(fill=tk.X)
        
        # === AI 鑷姩璇嗗埆妯″潡 ===
        def auto_fill_metadata():
            path = file_var.get()
            if not path or not os.path.exists(path):
                messagebox.showerror("閿欒", "璇峰厛閫夋嫨鏈夋晥鏂囦欢")
                return
                
            ai_btn.config(state='disabled', text="AI 鍒嗘瀽涓?..")
            self.root.update()
            
            def run_ai():
                try:
                    # 1. 璇诲彇鏂囦欢鍓?8000 瀛楃
                    content = self.file_processor.read_file(path)
                    if not content: raise Exception("鏃犳硶璇诲彇鏂囦欢鍐呭")
                    preview_text = content[:8000]
                    
                    # 2. 鏋勫缓 Prompt
                    prompt = (
                        "浣犳槸涓€涓笓涓氱殑鍥句功绠＄悊鍛樸€傝鍒嗘瀽浠ヤ笅涔︾睄鐗囨锛屽苟鎻愬彇鍏冩暟鎹€俓n"
                        "璇蜂弗鏍艰繑鍥?JSON 鏍煎紡锛屽寘鍚互涓嬪瓧娈碉細\n"
                        "- title: 涔﹀悕 (濡傛灉鏃犳硶纭畾锛屾牴鎹唴瀹规嫙瀹?\n"
                        "- author: 浣滆€?(濡傛灉鏈煡锛屽～ 'Unknown')\n"
                        "- description: 200瀛椾互鍐呯殑绮惧僵绠€浠嬶紝鍖呭惈鏍稿績涓婚銆侀鏍煎拰浜偣銆俓n"
                        "\n"
                        f"涔︾睄鐗囨锛歕n{preview_text}..."
                    )
                    
                    # 3. 璋冪敤缈昏瘧寮曟搸 (澶嶇敤褰撳墠閰嶇疆鐨勮В鏋?缈昏瘧API)
                    # 浼樺厛浣跨敤瑙ｆ瀽API锛屽叾娆＄炕璇慉PI
                    api_type = self.get_analysis_api_type()
                    if not self.api_configs[api_type].get('api_key'):
                        api_type = self.get_translation_api_type()
                        
                    response = self.translation_engine.translate(
                        text=prompt,
                        source_lang="Auto",
                        target_lang="JSON", # Hint for JSON
                        api_type=api_type,
                        api_config=self.api_configs[api_type]
                    )
                    
                    # 4. 瑙ｆ瀽 JSON
                    # 绠€鍗曠殑 JSON 鎻愬彇閫昏緫
                    try:
                        json_str = re.search(r'\{.*\}', response, re.DOTALL).group(0)
                        data = json.loads(json_str)
                        
                        # 鍥炲埌涓荤嚎绋嬫洿鏂?UI
                        self.root.after(0, lambda: update_ui(data))
                    except:
                        # 濡傛灉 AI 娌¤繑鍥炴爣鍑?JSON锛屽皾璇曠畝鍗曠殑鏂囨湰鎻愬彇鎴栨姤閿?
                        print(f"AI Response (Raw): {response}")
                        self.root.after(0, lambda: fail("AI 杩斿洖鏍煎紡闅句互瑙ｆ瀽锛岃閲嶈瘯鎴栨墜鍔ㄥ～鍐欍€?))
                        
                except Exception as e:
                    self.root.after(0, lambda: fail(str(e)))

            def update_ui(data):
                if data.get('title'): title_var.set(data['title'])
                if data.get('author'): author_var.set(data['author'])
                if data.get('description'): desc_var.set(data['description'])
                ai_btn.config(state='normal', text="鉁?AI 鏅鸿兘璇嗗埆 (閲嶆柊鐢熸垚)")
                messagebox.showinfo("鎴愬姛", "AI 宸蹭负鎮ㄨ嚜鍔ㄥ～鍐欎功绫嶄俊鎭紒")

            def fail(msg):
                messagebox.showerror("AI 鍒嗘瀽澶辫触", msg)
                ai_btn.config(state='normal', text="鉁?AI 鏅鸿兘璇嗗埆")

            threading.Thread(target=run_ai, daemon=True).start()

        ai_btn = ttk.Button(frame, text="鉁?AI 鏅鸿兘璇嗗埆 (Auto-Fill)", command=auto_fill_metadata)
        ai_btn.pack(pady=5, fill=tk.X)
        # =======================
        
        def do_upload():
            path = file_var.get()
            if not path or not os.path.exists(path):
                messagebox.showerror("閿欒", "璇烽€夋嫨鏈夋晥鏂囦欢")
                return
            
            btn.config(state='disabled', text="涓婁紶涓?..")
            
            def run():
                try:
                    self.community_manager.submit_book(
                        path,
                        title_var.get() or Path(path).stem,
                        author_var.get() or "Unknown",
                        desc_var.get(),
                        user_var.get()
                    )
                    self.root.after(0, lambda: success())
                except Exception as e:
                    self.root.after(0, lambda: fail(str(e)))
            
            threading.Thread(target=run, daemon=True).start()
            
        def success():
            messagebox.showinfo("鎻愪氦鎴愬姛", "涔︾睄宸蹭笂浼犲苟鍙戝竷鍒扮ぞ鍖猴紒")
            dialog.destroy()
            self.refresh_community_list() # 鑷姩鍒锋柊鍒楄〃
            
        def fail(msg):
            messagebox.showerror("澶辫触", msg)
            btn.config(state='normal', text="绔嬪嵆鍒嗕韩")

        btn = ttk.Button(frame, text="绔嬪嵆鍒嗕韩 (鍏紑)", command=do_upload)
        btn.pack(pady=20, fill=tk.X)

    def open_admin_audit(self):
        """鎵撳紑绠＄悊鍛樼鐞嗙晫闈紙鐢ㄤ簬鍒犻櫎璁板綍锛?""
        pwd = simpledialog.askstring("绠＄悊鍛樼櫥褰?, "璇疯緭鍏ョ鐞嗗憳瀵嗙爜:", show="*")
        if pwd != "admin":
            messagebox.showerror("閿欒", "瀵嗙爜閿欒")
            return
            
        audit_win = tk.Toplevel(self.root)
        audit_win.title("鍥句功棣嗙鐞?(Library Admin)")
        audit_win.geometry("800x500")
        
        # 鍒楄〃
        columns = ("id", "title", "uploader", "date", "status")
        tree = ttk.Treeview(audit_win, columns=columns, show="headings")
        tree.heading("id", text="ID")
        tree.heading("title", text="鏍囬")
        tree.heading("uploader", text="涓婁紶鑰?)
        tree.heading("date", text="鏃ユ湡")
        tree.heading("status", text="鐘舵€?)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def refresh():
            tree.delete(*tree.get_children())
            # 姝ゆ椂鏄剧ず鐨勬槸宸插叕寮€鐨勪功绫嶏紝渚涚鐞嗗憳鍒犻櫎
            books = self.community_manager.get_public_books()
            for b in books:
                tree.insert("", "end", values=(b['id'], b['title'], b['uploader'], b['date'], b.get('status', 'approved')))
        
        refresh()
        
        btn_frame = ttk.Frame(audit_win, padding=10)
        btn_frame.pack(fill=tk.X)
        
        def delete_entry():
            sel = tree.selection()
            if not sel: return
            bid = str(tree.item(sel[0])['values'][0])
            
            if messagebox.askyesno("纭", "纭畾浠庡叕鍏卞垪琛ㄤ腑鍒犻櫎姝や功绫嶅悧锛?):
                # 澶嶇敤 rejection 閫昏緫杩涜鍒犻櫎
                library = self.community_manager.get_public_books()
                new_library = [b for b in library if b['id'] != bid]
                self.community_manager._save_json(self.community_manager.library_file, new_library)
                
                messagebox.showinfo("鎴愬姛", "宸插垹闄?)
                refresh()
                self.refresh_community_list()

        ttk.Button(btn_frame, text="馃棏锔?鍒犻櫎閫変腑鏉＄洰", command=delete_entry).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="鍒锋柊", command=refresh).pack(side=tk.RIGHT, padx=5)

    def _build_global_search_ui(self, search_frame):
        """鍘熸湁鐨勫叏缃戞悳绱I鏋勫缓閫昏緫 (閲嶆瀯鑷?setup_search_tab)"""
        # 浣跨敤 PanedWindow 鍒嗗壊宸﹀彸鍖哄煙
        paned = tk.PanedWindow(search_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        paned.pack(fill=tk.BOTH, expand=True)

        # === 宸︿晶锛氬鍥犵礌绛涢€?===
        sidebar_frame = ttk.Frame(paned, width=220)
        paned.add(sidebar_frame, minsize=180)
        
        # 1. 鍒嗙被閫夋嫨 (澶氶€?
        cat_labelframe = ttk.LabelFrame(sidebar_frame, text="1. 鍒嗙被 (鎸塁trl澶氶€?", padding="5")
        cat_labelframe.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.cat_tree = ttk.Treeview(cat_labelframe, show="tree", selectmode="extended", height=10)
        self.cat_tree.pack(fill=tk.BOTH, expand=True)
        
        categories = {
            "鏂囧 (Fiction)": ["绉戝够 (Sci-Fi)", "濂囧够 (Fantasy)", "鎮枒 (Mystery)", "鎯婃倸 (Thriller)", "娴极 (Romance)", "缁忓吀 (Classics)"],
            "闈炶櫄鏋?(Non-Fiction)": ["鍘嗗彶 (History)", "浼犺 (Biography)", "鍝插 (Philosophy)", "蹇冪悊瀛?(Psychology)", "鍟嗕笟 (Business)"],
            "绉戞妧 (Tech)": ["璁＄畻鏈?(Computer Science)", "缂栫▼ (Programming)", "AI (Artificial Intelligence)", "鐗╃悊 (Physics)", "鏁板 (Math)"],
            "鐢熸椿 (Lifestyle)": ["鐑归オ (Cooking)", "鍋ュ悍 (Health)", "鏃呮父 (Travel)", "鑹烘湳 (Art)"],
            "婕敾 (Comics)": ["Manga", "Graphic Novels"]
        }
        
        for main_cat, sub_cats in categories.items():
            parent = self.cat_tree.insert("", "end", text=main_cat, open=True)
            for sub in sub_cats:
                self.cat_tree.insert(parent, "end", text=sub)

        # 2. 璇█閫夋嫨 (澶氶€?
        lang_labelframe = ttk.LabelFrame(sidebar_frame, text="2. 璇█ (澶氶€?", padding="5")
        lang_labelframe.pack(fill=tk.X, padx=2, pady=2)
        
        self.lang_vars = {}
        # 浣跨敤鏍囧噯浠ｇ爜: zh, en, ja, ko, fr, de
        languages = [("涓枃", "zh"), ("鑻辫", "en"), ("鏃ヨ", "ja"), 
                     ("闊╄", "ko"), ("娉曡", "fr"), ("寰疯", "de")]
        
        for i, (lbl, val) in enumerate(languages):
            var = tk.BooleanVar()
            self.lang_vars[val] = var
            cb = ttk.Checkbutton(lang_labelframe, text=lbl, variable=var)
            cb.grid(row=i//2, column=i%2, sticky="w", padx=2)

        # 3. 鎼滅储鎸夐挳
        btn_frame = ttk.Frame(sidebar_frame, padding="5")
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="馃攳 搴旂敤绛涢€夊苟鎼滅储", command=self.on_sidebar_search_click).pack(fill=tk.X)
        ttk.Label(btn_frame, text="鎻愮ず: 缁撳悎椤堕儴鍏抽敭璇嶆洿绮惧噯", font=("", 8), foreground="gray").pack(pady=(5,0))

        # === 鍙充晶锛氭悳绱笌缁撴灉 ===
        right_frame = ttk.Frame(paned, padding="10")
        paned.add(right_frame, minsize=600)
        
        self.search_frame = right_frame

        # 椤堕儴鎼滅储鏍?
        top_frame = ttk.Frame(right_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(top_frame, text="闄勫姞鍏抽敭璇?").pack(side=tk.LEFT, padx=(0, 5))
        self.search_query_var = tk.StringVar()
        self.search_entry = ttk.Entry(top_frame, textvariable=self.search_query_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.search_entry.bind('<Return>', lambda e: self.on_search_click())
        
        self.search_source_var = tk.StringVar(value="Anna's Archive")
        source_combo = ttk.Combobox(
            top_frame, 
            textvariable=self.search_source_var,
            values=["Anna's Archive", "Z-Library"],
            state="readonly",
            width=15
        )
        source_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(top_frame, text="鏅€氭悳绱?, command=self.on_search_click).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="馃 AI 瀵讳功", command=self.on_ai_search_click).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="閰嶇疆璐﹀彿", command=self.open_online_config).pack(side=tk.LEFT, padx=5)
        
        # 涓棿缁撴灉鍒楄〃
        list_frame = ttk.Frame(self.search_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 浣跨敤 Treeview 灞曠ず缁撴灉
        columns = ("title", "author", "language", "ext", "size", "source", "category")
        self.search_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        self.search_tree.heading("title", text="鏍囬")
        self.search_tree.heading("author", text="浣滆€?)
        self.search_tree.heading("language", text="璇█")
        self.search_tree.heading("ext", text="鏍煎紡")
        self.search_tree.heading("size", text="澶у皬")
        self.search_tree.heading("source", text="鏉ユ簮")
        self.search_tree.heading("category", text="AI鍒嗙被")
        
        self.search_tree.column("title", width=300)
        self.search_tree.column("author", width=120)
        self.search_tree.column("language", width=50, anchor="center")
        self.search_tree.column("ext", width=50, anchor="center")
        self.search_tree.column("size", width=70, anchor="e")
        self.search_tree.column("source", width=90, anchor="center")
        self.search_tree.column("category", width=100, anchor="center")
        
        self.search_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.search_tree.bind('<<TreeviewSelect>>', self.on_search_result_select)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.search_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.search_tree.config(yscrollcommand=scrollbar.set)
        
        # 鍒嗛〉鎺т欢
        pagination_frame = ttk.Frame(right_frame)
        pagination_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.prev_btn = ttk.Button(pagination_frame, text="< 涓婁竴椤?, command=self.on_prev_page, state='disabled')
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.page_label_var = tk.StringVar(value="绗?1 椤?)
        ttk.Label(pagination_frame, textvariable=self.page_label_var, width=8).pack(side=tk.LEFT, padx=5)
        
        # 婊戝潡蹇€熻烦杞?
        self.page_slider = tk.Scale(pagination_frame, from_=1, to=50, orient=tk.HORIZONTAL, length=200, showvalue=0)
        self.page_slider.set(1)
        self.page_slider.pack(side=tk.LEFT, padx=5)
        self.page_slider.bind("<ButtonRelease-1>", self.on_page_slider_release)
        # 鎷栧姩鏃跺疄鏃舵洿鏂版爣绛?
        self.page_slider.bind("<Motion>", lambda e: self.page_label_var.set(f"绗?{self.page_slider.get()} 椤?))
        
        self.next_btn = ttk.Button(pagination_frame, text="涓嬩竴椤?>", command=self.on_next_page, state='disabled')
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        # 搴曢儴璇︽儏涓庝笅杞?
        bottom_frame = ttk.LabelFrame(self.search_frame, text="缁撴灉璇︽儏", padding="10")
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.search_detail_var = tk.StringVar(value="璇蜂粠宸︿晶閫夋嫨绛涢€夋潯浠舵垨鐩存帴鎼滅储")
        ttk.Label(bottom_frame, textvariable=self.search_detail_var, wraplength=800, justify=tk.LEFT).pack(fill=tk.X, pady=(0, 10))
        
        btn_frame = ttk.Frame(bottom_frame)
        btn_frame.pack(side=tk.RIGHT)

        ttk.Button(btn_frame, text="馃彿锔?鑾峰彇缃戠珯鍒嗙被", command=self.on_auto_categorize_click).pack(side=tk.LEFT, padx=5)
        self.download_btn = ttk.Button(btn_frame, text="涓嬭浇骞跺鍏ョ炕璇?, command=self.on_download_click, state="disabled")
        self.download_btn.pack(side=tk.LEFT, padx=5)
        
        self.search_status_var = tk.StringVar(value="灏辩华")
        ttk.Label(self.search_frame, textvariable=self.search_status_var, foreground="gray").pack(side=tk.LEFT, pady=(5, 0))

        # 鎼滅储缁撴灉缂撳瓨
        self.current_search_results = []
        self.selected_result = None
        self.current_page = 1

    def on_prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.perform_paged_search()

    def on_next_page(self):
        self.current_page += 1
        self.perform_paged_search()

    def on_page_slider_release(self, event):
        """婊戝潡閲婃斁鏃惰烦杞?""
        new_page = self.page_slider.get()
        if new_page != self.current_page:
            self.current_page = new_page
            self.perform_paged_search()

    def perform_paged_search(self):
        """鎵ц鍒嗛〉鎼滅储"""
        query = self.search_query_var.get().strip()
        source = self.search_source_var.get()
        if not query: return
        
        # 鍚屾鎺т欢鐘舵€?
        self.page_label_var.set(f"绗?{self.current_page} 椤?)
        self.page_slider.set(self.current_page)
        
        self.search_status_var.set(f"姝ｅ湪鎼滅储绗?{self.current_page} 椤? {query}...")
        
        # 鏇存柊鎸夐挳鐘舵€?
        self.prev_btn.config(state='normal' if self.current_page > 1 else 'disabled')
        
        # 寮€鍚嚎绋嬫悳绱?
        threading.Thread(target=self.perform_search, args=(query, source, self.current_page), daemon=True).start()

    def on_sidebar_search_click(self):
        """澶勭悊渚ц竟鏍忕粍鍚堟悳绱?""
        # 1. 鏀堕泦閫変腑鐨勫垎绫?
        selected_cats = []
        for item_id in self.cat_tree.selection():
            item_text = self.cat_tree.item(item_id, "text")
            # 鎻愬彇鑻辨枃閮ㄥ垎浣滀负鍏抽敭璇?(濡傛灉鏈?
            if "(" in item_text:
                keyword = item_text.split("(")[1].strip(")")
                selected_cats.append(keyword)
            else:
                selected_cats.append(item_text)
        
        # 2. 鏀堕泦閫変腑鐨勮瑷€
        selected_langs = [lang for lang, var in self.lang_vars.items() if var.get()]
        
        # 3. 鏀堕泦杈撳叆妗嗙殑棰濆鍏抽敭璇?
        extra_keywords = self.search_query_var.get().strip()
        
        # 4. 缁勫悎鏌ヨ璇彞
        query_parts = []
        if selected_cats:
            query_parts.extend(selected_cats)
        if selected_langs:
            query_parts.extend(selected_langs)
        if extra_keywords:
            query_parts.append(extra_keywords)
            
        final_query = " ".join(query_parts)
        
        if not final_query:
            messagebox.showwarning("鎻愮ず", "璇疯嚦灏戦€夋嫨涓€涓垎绫汇€佽瑷€鎴栬緭鍏ュ叧閿瘝")
            return
            
        # 璁剧疆鍒拌緭鍏ユ骞惰Е鍙戞悳绱?
        self.search_query_var.set(final_query)
        self.on_search_click()

    def on_category_select(self, event):
        """(淇濈暀鍗曟満琛屼负锛屼絾澶氶€夋ā寮忎笅涓昏鐢辨寜閽Е鍙?"""
        pass # 澶氶€夋ā寮忎笅锛岀偣鍑讳笉鐩存帴瑙﹀彂锛岀敱鎸夐挳瑙﹀彂

    def on_random_browse_click(self):
        """闅忔満娴忚"""
        import random
        # 甯歌鍒嗙被鍜岀儹闂ㄥ叧閿瘝
        keywords = [
            "Best sci-fi books 2024", "Classic literature", "Python programming", 
            "History of China", "Modern philosophy", "Psychology bestsellers",
            "Artificial Intelligence", "Machine Learning", "Space exploration",
            "Fantasy novels", "Mystery thrillers", "Biographies",
            "Cooking and Food", "Self-help", "Finance and Investment"
        ]
        random_keyword = random.choice(keywords)
        self.search_query_var.set(random_keyword)
        self.on_search_click()

    def on_auto_categorize_click(self):
        """鑾峰彇缃戠珯鍘熸湰鐨勫垎绫讳俊鎭紙鏀寔鍗曢€夈€佹枃浠跺す鎵归噺銆佸叏閲忔壒閲忥級"""
        selection = self.search_tree.selection()
        items_to_process = []
        
        # 1. 濡傛灉娌℃湁閫変腑浠讳綍椤?-> 璇㈤棶鏄惁澶勭悊鍏ㄩ儴
        if not selection:
            if not self.current_search_results:
                messagebox.showwarning("鎻愮ず", "鍒楄〃涓虹┖锛岃鍏堟悳绱?)
                return
            
            if messagebox.askyesno("鎵归噺鑾峰彇", f"鎮ㄦ湭閫変腑浠讳綍涔︾睄銆俓n鏄惁瑕佸褰撳墠鍒楄〃涓殑 {len(self.current_search_results)} 鏈功鍏ㄩ儴鑾峰彇璇︾粏鍒嗙被锛焅n(杩欏彲鑳介渶瑕佷竴浜涙椂闂?"):
                items_to_process = self.current_search_results
            else:
                return

        # 2. 濡傛灉閫変腑浜嗘煇椤?
        else:
            item_id = selection[0]
            
            # 鎯呭喌 A: 閫変腑浜嗗垎绫绘枃浠跺す -> 澶勭悊璇ュ垎绫讳笅鐨勬墍鏈変功绫?
            if "_cat_" in item_id:
                cat_name = self.search_tree.item(item_id, "values")[0].replace("馃搨 ", "")
                # 鎵惧埌鎵€鏈夊睘浜庤鍒嗙被鐨勪功绫?
                items_to_process = [res for res in self.current_search_results if res.get('category') == cat_name]
                
                if not items_to_process: # Fallback just in case
                    return
                    
                if not messagebox.askyesno("鎵归噺鑾峰彇", f"鏄惁鑾峰彇 '{cat_name}' 鍒嗙被涓?{len(items_to_process)} 鏈功鐨勮缁嗗垎绫伙紵"):
                    return
            
            # 鎯呭喌 B: 閫変腑浜嗗叿浣撶殑涔︾睄 -> 澶勭悊鍗曟湰涔?
            else:
                item_values = self.search_tree.item(item_id, "values")
                title = item_values[0]
                for res in self.current_search_results:
                    if res.get('title') == title:
                        items_to_process = [res]
                        break
        
        if not items_to_process:
            return

        self.search_status_var.set(f"鍑嗗鑾峰彇 {len(items_to_process)} 鏈功鐨勫垎绫讳俊鎭?..")
        self.download_btn.config(state="disabled") # 鏆傛椂绂佺敤涓嬭浇闃叉鍐茬獊
        
        def run_batch_fetch():
            count = 0
            total = len(items_to_process)
            
            for i, book_info in enumerate(items_to_process):
                title = book_info.get('title', 'Unknown')
                url = book_info.get('url', '')
                source = book_info.get('source', '')
                
                if not url: continue
                
                self.root.after(0, lambda t=title, c=count+1, tot=total: self.search_status_var.set(f"[{c}/{tot}] 鑾峰彇鍒嗙被: {t[:20]}..."))
                
                try:
                    # 鑾峰彇璇︾粏鍒嗙被
                    new_category = self.online_search_manager.get_book_category(url, source)
                    
                    if new_category and new_category != "Unknown":
                        book_info['category'] = new_category # 鏇存柊鏁版嵁
                    
                    # 绋嶅井寤舵椂閬垮厤璇锋眰杩囧揩
                    if total > 1:
                        time.sleep(0.5)
                        
                except Exception as e:
                    print(f"Error fetching cat for {title}: {e}")
                
                count += 1
            
            # 鍏ㄩ儴瀹屾垚鍚庡埛鏂扮晫闈?
            self.root.after(0, lambda: self._refresh_search_tree_grouped())
            self.root.after(0, lambda: self.search_status_var.set(f"鎵归噺鑾峰彇瀹屾垚锛屽凡鏇存柊 {count} 鏈功鐨勫垎绫?))
            self.root.after(0, lambda: self.download_btn.config(state="normal"))

        threading.Thread(target=run_batch_fetch, daemon=True).start()

    def _refresh_search_tree_grouped(self):
        """閲嶆柊鏍规嵁褰撳墠鏁版嵁鍒锋柊鏍戠姸鍒楄〃"""
        # 娓呯┖褰撳墠鏍?
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)
            
        # 閲嶆柊鍒嗙粍
        categories = {}
        for res in self.current_search_results:
            cat = res.get('category', 'Uncategorized')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(res)
        
        # 閲嶆柊鎻掑叆
        for i, (cat, cat_books) in enumerate(categories.items()):
            cat_id = f"group_{i}"
            # 鏂囦欢澶硅妭鐐?
            self.search_tree.insert("", tk.END, iid=cat_id, values=("馃搨 " + cat, "", "", "", "", res.get('source', ''), "鍒嗙被"), open=True)
            
            for j, res in enumerate(cat_books):
                # 涔︾睄鑺傜偣
                self.search_tree.insert(cat_id, tk.END, iid=f"book_{i}_{j}", values=(
                    res.get('title', '鏈煡'),
                    res.get('author', '鏈煡'),
                    res.get('language', ''),
                    res.get('extension', ''),
                    res.get('size', ''),
                    res.get('source', res.get('source', '')),
                    cat
                ))


    def on_ai_search_click(self):
        """AI 鏅鸿兘瀵讳功鐐瑰嚮澶勭悊"""
        query = self.search_query_var.get().strip()
        if not query:
            messagebox.showwarning("璀﹀憡", "璇疯緭鍏ユ偍鐨勫涔﹂渶姹傦紙渚嬪锛?鎵句竴鏈叧浜嶱ython鏁版嵁鍒嗘瀽鐨勭晠閿€涔?锛?)
            return
            
        source = self.search_source_var.get()
        self.search_status_var.set(f"AI 姝ｅ湪鍒嗘瀽闇€姹? {query}...")
        self.download_btn.config(state="disabled")
        
        # 娓呯┖褰撳墠鍒楄〃
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)
            
        # 寮€鍚嚎绋嬫悳绱?
        threading.Thread(target=self.perform_ai_search, args=(query, source), daemon=True).start()

    def perform_ai_search(self, query, source):
        """鎵ц AI 瀵讳功閫昏緫"""
        try:
            def callback(msg):
                self.root.after(0, lambda: self.search_status_var.set(msg))
            
            # 1. 璋冪敤 BookHunter
            results = self.book_hunter.hunt(query, source, callback=callback)
            
            # 2. (鍙€? AI 鍐嶆绛涢€?
            # callback("馃 AI 姝ｅ湪绛涢€夋渶浣冲尮閰?..")
            # filtered_results = self.book_hunter.ai_filter_results(query, results)
            # results = filtered_results if filtered_results else results
            
            self.current_search_results = results
            
            def update_ui():
                # 娓呯┖鏃х粨鏋?
                for item in self.search_tree.get_children():
                    self.search_tree.delete(item)

                if not results:
                    self.search_status_var.set("AI 鏈壘鍒扮浉鍏充功绫?)
                    messagebox.showinfo("鎻愮ず", "AI 鍒嗘瀽浜嗘偍鐨勯渶姹傦紝浣嗘湭鎵惧埌鍖归厤鐨勪功绫嶃€?)
                    return
                
                # 鎸夊垎绫诲垎缁?
                categories = {}
                for res in results:
                    cat = res.get('category', 'Uncategorized')
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append(res)
                
                # 娓呯┖骞朵互鏍戠姸灞曠ず
                for i, (cat, cat_books) in enumerate(categories.items()):
                    # 鎻掑叆鍒嗙被鐖惰妭鐐?
                    cat_id = f"ai_cat_{i}"
                    self.search_tree.insert("", tk.END, iid=cat_id, values=("馃搨 " + cat, "", "", "", "", source, "鍒嗙被"), open=True)
                    
                    for j, res in enumerate(cat_books):
                        self.search_tree.insert(cat_id, tk.END, iid=f"ai_book_{i}_{j}", values=(
                            res.get('title', '鏈煡'),
                            res.get('author', '鏈煡'),
                            res.get('language', ''),
                            res.get('extension', ''),
                            res.get('size', ''),
                            res.get('source', source),
                            cat
                        ))
                
                self.search_status_var.set(f"AI 瀵讳功瀹屾垚锛屾壘鍒?{len(results)} 鏈帹鑽愪功绫?)
                
            self.root.after(0, update_ui)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("AI 瀵讳功閿欒", str(e)))
            self.root.after(0, lambda: self.search_status_var.set("瀵讳功鍑洪敊"))

    def on_search_click(self):
        """鐐瑰嚮鎼滅储鎸夐挳"""
        query = self.search_query_var.get().strip()
        if not query:
            messagebox.showwarning("璀﹀憡", "璇疯緭鍏ユ悳绱㈠叧閿瘝")
            return
            
        source = self.search_source_var.get()
        self.search_status_var.set(f"姝ｅ湪浠?{source} 鎼滅储: {query}...")
        self.download_btn.config(state="disabled")
        
        # 閲嶇疆鍒嗛〉
        self.current_page = 1
        self.perform_paged_search()

    def perform_search(self, query, source, page=1):
        """鎵ц鎼滅储閫昏緫锛堝悗鍙扮嚎绋嬶級"""
        try:
            if source == "Z-Library":
                results = self.online_search_manager.search_zlibrary(query, page)
            else:
                results = self.online_search_manager.search_annas_archive(query, page)
                
            self.current_search_results = results
            
            def update_ui():
                # 娓呯┖鏃х粨鏋?
                for item in self.search_tree.get_children():
                    self.search_tree.delete(item)

                # 鏇存柊鍒嗛〉鎸夐挳鐘舵€?
                if results:
                    self.next_btn.config(state='normal')
                    self.prev_btn.config(state='normal' if page > 1 else 'disabled')
                else:
                    self.next_btn.config(state='disabled')
                    # Keep prev enabled if we are deep in pages? No, usually if no results, stop.
                    
                if not results:
                    self.search_status_var.set("鏈壘鍒扮粨鏋?)
                    messagebox.showinfo("鎻愮ず", f"鍦?{source} 涓湭鎵惧埌鍏抽敭璇?'{query}' 鐨勭粨鏋?)
                    return
                    
                # 鎸夊垎绫诲垎缁?
                categories = {}
                for res in results:
                    cat = res.get('category', 'Uncategorized')
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append(res)
                
                for i, (cat, cat_books) in enumerate(categories.items()):
                    # 鎻掑叆鍒嗙被鐖惰妭鐐?
                    cat_id = f"search_cat_{i}"
                    self.search_tree.insert("", tk.END, iid=cat_id, values=("馃搨 " + cat, "", "", "", "", source, "鍒嗙被"), open=True)
                    
                    for j, res in enumerate(cat_books):
                        self.search_tree.insert(cat_id, tk.END, iid=f"search_book_{i}_{j}", values=(
                            res.get('title', '鏈煡'),
                            res.get('author', '鏈煡'),
                            res.get('language', ''),
                            res.get('extension', ''),
                            res.get('size', ''),
                            res.get('source', source),
                            cat
                        ))
                
                self.search_status_var.set(f"鎼滅储瀹屾垚锛屾壘鍒?{len(results)} 涓粨鏋?(绗?{page} 椤?")
                
            self.root.after(0, update_ui)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("鎼滅储閿欒", str(e)))
            self.root.after(0, lambda: self.search_status_var.set("鎼滅储鍑洪敊"))

    def on_search_result_select(self, event):
        """閫夋嫨鎼滅储缁撴灉"""
        selection = self.search_tree.selection()
        if not selection:
            return
            
        # 濡傛灉閫変腑鐨勬槸鍒嗙被鏂囦欢澶癸紝涓嶆墽琛屽悗缁€昏緫
        item_id = selection[0]
        if "_cat_" in item_id:
            self.selected_result = None
            self.search_detail_var.set("璇烽€夋嫨鍏蜂綋鐨勪功绫?)
            self.download_btn.config(state="disabled")
            return

        # 闇€瑕佹牴鎹?Treeview 鐨勭粍缁囨柟寮忔壘鍒板搴旂殑缁撴灉瀵硅薄
        # 绠€鍗曟柟妗堬細鍦ㄧ粨鏋滄彃鍏ユ椂灏?index 瀛樺湪 values 閲岋紝鎴栬€呮牴鎹爣棰樺尮閰?
        # 杩欓噷鎴戜滑閬嶅巻缂撳瓨瀵绘壘鍖归厤鐨勬爣棰橈紙鏈€绠€鍗曪級
        item_values = self.search_tree.item(item_id, "values")
        title = item_values[0]
        
        self.selected_result = None
        for res in self.current_search_results:
            if res.get('title') == title:
                self.selected_result = res
                break
        
        if self.selected_result:
            res = self.selected_result
            detail = (
                f"鏍囬: {res.get('title')}\n"
                f"浣滆€? {res.get('author')}\n"
                f"鍒嗙被: {res.get('category', 'Uncategorized')}\n"
                f"鏍煎紡: {res.get('extension')} | 澶у皬: {res.get('size')} | 璇█: {res.get('language')}\n"
                f"鏉ユ簮: {res.get('source')}\n"
                f"璇︽儏: {res.get('metadata', '')}"
            )
            self.search_detail_var.set(detail)
            self.download_btn.config(state="normal")

    def on_download_click(self):
        """鐐瑰嚮涓嬭浇鎸夐挳"""
        if not self.selected_result:
            return
            
        res = self.selected_result
        self.search_status_var.set(f"姝ｅ湪涓嬭浇: {res.get('title')}...")
        self.download_btn.config(state="disabled")
        
        # 寮€鍚嚎绋嬩笅杞?
        threading.Thread(target=self.perform_download, args=(res,), daemon=True).start()

    def perform_download(self, result_item):
        """鎵ц涓嬭浇閫昏緫锛堝悗鍙扮嚎绋嬶級"""
        # 瀵煎叆鑷畾涔夊紓甯?
        from online_search import CloudflareError
        import webbrowser

        try:
            def progress_cb(current, total):
                if total > 0:
                    percent = (current / total) * 100
                    self.root.after(0, lambda: self.search_status_var.set(f"涓嬭浇涓? {percent:.1f}%"))
                else:
                    self.root.after(0, lambda: self.search_status_var.set(f"涓嬭浇涓? {current/1024/1024:.1f} MB"))
            
            file_path = self.online_search_manager.download_book(result_item, progress_callback=progress_cb)
            
            if file_path and os.path.exists(file_path):
                self.root.after(0, lambda: self.search_status_var.set("涓嬭浇鎴愬姛锛屾鍦ㄥ鍏?.."))
                
                def load_downloaded():
                    self.file_path_var.set(file_path)
                    self.load_file_content(file_path)
                    # 鍒囨崲鍒板師鏂囨爣绛鹃〉
                    for i in range(self.notebook.index("end")):
                        if self.notebook.tab(i, "text") == "鍘熸枃":
                            self.notebook.select(i)
                            break
                    messagebox.showinfo("鎴愬姛", f"涔︾睄宸蹭笅杞藉苟鎴愬姛瀵煎叆锛歕n{os.path.basename(file_path)}")
                
                self.root.after(0, load_downloaded)
            else:
                self.root.after(0, lambda: messagebox.showerror("涓嬭浇澶辫触", "鏃犳硶瀹屾垚涓嬭浇锛屾枃浠舵湭淇濆瓨銆?))
                self.root.after(0, lambda: self.search_status_var.set("涓嬭浇澶辫触"))

        except CloudflareError as ce:
            # 鎹曡幏 Cloudflare 閿欒锛屾彁绀虹敤鎴蜂娇鐢ㄦ祻瑙堝櫒鎵撳紑
            msg = "鑷姩涓嬭浇琚?Cloudflare 鎷︽埅 (403 Forbidden)銆俓n杩欓€氬父鏄洜涓虹綉绔欏惎鐢ㄤ簡鍙嶇埇铏繚鎶ゃ€俓n\n鏄惁鍦ㄦ祻瑙堝櫒涓墦寮€涓嬭浇椤甸潰锛?
            self.root.after(0, lambda: self._prompt_browser_open(msg, str(ce)))
            self.root.after(0, lambda: self.search_status_var.set("闇€瑕佹祻瑙堝櫒涓嬭浇"))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("涓嬭浇閿欒", str(e)))
            self.root.after(0, lambda: self.search_status_var.set("涓嬭浇鍑洪敊"))
        finally:
            self.root.after(0, lambda: self.download_btn.config(state="normal"))

    def _prompt_browser_open(self, msg, url):
        """鎻愮ず骞跺湪娴忚鍣ㄦ墦寮€閾炬帴"""
        import webbrowser
        if messagebox.askyesno("涓嬭浇鍙楅樆", msg):
            webbrowser.open(url)

    def open_online_config(self):
        """鎵撳紑鍦ㄧ嚎鎼滅储閰嶇疆瀵硅瘽妗?""
        config_window = tk.Toplevel(self.root)
        config_window.title("鍦ㄧ嚎鎼滅储閰嶇疆")
        config_window.geometry("550x450")
        config_window.transient(self.root)
        config_window.grab_set()

        frame = ttk.Frame(config_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Z-Library 閰嶇疆
        zlib_frame = ttk.LabelFrame(frame, text="Z-Library 閰嶇疆", padding="10")
        zlib_frame.pack(fill=tk.X, pady=(0, 10))
        
        zlib_config = self.config_manager.get('online_search.zlibrary', {})
        
        ttk.Label(zlib_frame, text="閭:").grid(row=0, column=0, sticky=tk.W, pady=2)
        email_var = tk.StringVar(value=zlib_config.get('email', ''))
        ttk.Entry(zlib_frame, textvariable=email_var, width=30).grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
        
        ttk.Label(zlib_frame, text="瀵嗙爜:").grid(row=1, column=0, sticky=tk.W, pady=2)
        pass_var = tk.StringVar(value=zlib_config.get('password', ''))
        ttk.Entry(zlib_frame, textvariable=pass_var, show="*", width=30).grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)
        
        ttk.Label(zlib_frame, text="鍩熷悕:").grid(row=2, column=0, sticky=tk.W, pady=2)
        domain_var = tk.StringVar(value=zlib_config.get('domain', 'https://singlelogin.re'))
        domain_entry = ttk.Entry(zlib_frame, textvariable=domain_var, width=30)
        domain_entry.grid(row=2, column=1, sticky=tk.W, pady=2, padx=5)

        def test_zlib_connection():
            """娴嬭瘯 Z-Library 杩炴帴"""
            email = email_var.get().strip()
            password = pass_var.get().strip()
            domain = domain_var.get().strip()
            
            if not email or not password:
                messagebox.showwarning("鎻愮ず", "璇疯緭鍏ラ偖绠卞拰瀵嗙爜浠ユ祴璇曠櫥褰?)
                return

            self.config_manager.set('online_search.zlibrary.email', email, save=False)
            self.config_manager.set('online_search.zlibrary.password', password, save=False)
            self.config_manager.set('online_search.zlibrary.domain', domain, save=False)
            
            def run_test():
                try:
                    success = self.online_search_manager.login_zlibrary()
                    if success:
                        self.root.after(0, lambda: messagebox.showinfo("鎴愬姛", "Z-Library 鐧诲綍鎴愬姛锛?))
                    else:
                        self.root.after(0, lambda: messagebox.showerror("澶辫触", "Z-Library 鐧诲綍澶辫触锛岃妫€鏌ヨ处鍙峰瘑鐮佹垨鍩熷悕"))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("閿欒", f"杩炴帴鍑洪敊: {str(e)}"))
            
            threading.Thread(target=run_test, daemon=True).start()

        ttk.Button(zlib_frame, text="娴嬭瘯鐧诲綍", command=test_zlib_connection).grid(row=3, column=1, sticky=tk.E, pady=5, padx=5)
        
        # Anna's Archive 閰嶇疆
        annas_frame = ttk.LabelFrame(frame, text="Anna's Archive 閰嶇疆", padding="10")
        annas_frame.pack(fill=tk.X, pady=(0, 10))
        
        annas_config = self.config_manager.get('online_search.annas_archive', {})
        ttk.Label(annas_frame, text="鍩熷悕:").grid(row=0, column=0, sticky=tk.W, pady=2)
        annas_domain_var = tk.StringVar(value=annas_config.get('domain', 'https://annas-archive.li'))
        annas_domain_entry = ttk.Entry(annas_frame, textvariable=annas_domain_var, width=30)
        annas_domain_entry.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)

        def test_annas_connection():
            """娴嬭瘯 Anna's Archive 杩炴帴"""
            domain = annas_domain_var.get().strip()
            
            def run_test():
                try:
                    import requests
                    resp = requests.get(domain, timeout=10)
                    if resp.status_code == 200:
                        self.root.after(0, lambda: messagebox.showinfo("鎴愬姛", f"鎴愬姛杩炴帴鍒?Anna's Archive锛乗n鐘舵€佺爜: {resp.status_code}"))
                    else:
                        self.root.after(0, lambda: messagebox.showwarning("璀﹀憡", f"鏈嶅姟鍣ㄨ繑鍥炵姸鎬佺爜: {resp.status_code}"))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("閿欒", f"杩炴帴澶辫触: {str(e)}"))

            threading.Thread(target=run_test, daemon=True).start()

        ttk.Button(annas_frame, text="娴嬭瘯杩炴帴", command=test_annas_connection).grid(row=1, column=1, sticky=tk.E, pady=5, padx=5)

        # 鑷姩妫€娴嬮暅鍍忓姛鑳?
        def auto_detect_mirrors():
            """鑷姩妫€娴嬫渶蹇暅鍍?""
            btn = detect_btn
            btn.config(state='disabled', text="妫€娴嬩腑...")
            
            def run_detection():
                try:
                    results = self.online_search_manager.check_mirrors()
                    
                    # 鏌ユ壘鏈€浣抽暅鍍?
                    best_annas = None
                    for m in results['annas_archive']:
                        if m['status'] == 'OK':
                            best_annas = m
                            break
                            
                    best_zlib = None
                    for m in results['zlibrary']:
                        if m['status'] == 'OK':
                            best_zlib = m
                            break
                    
                    msg = "妫€娴嬬粨鏋?\n\n"
                    
                    if best_annas:
                        msg += f"Anna's Archive (鏈€蹇?: {best_annas['url']} ({best_annas['latency']}ms)\n"
                        self.root.after(0, lambda: annas_domain_var.set(best_annas['url']))
                    else:
                        msg += "Anna's Archive: 鏈壘鍒板彲鐢ㄩ暅鍍廫n"
                        
                    if best_zlib:
                        msg += f"Z-Library (鏈€蹇?: {best_zlib['url']} ({best_zlib['latency']}ms)\n"
                        self.root.after(0, lambda: domain_var.set(best_zlib['url']))
                    else:
                        msg += "Z-Library: 鏈壘鍒板彲鐢ㄩ暅鍍廫n"
                        
                    self.root.after(0, lambda: messagebox.showinfo("闀滃儚妫€娴嬪畬鎴?, msg))
                    
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("閿欒", f"妫€娴嬪け璐? {e}"))
                finally:
                    self.root.after(0, lambda: btn.config(state='normal', text="鑷姩妫€娴嬮暅鍍?))

            threading.Thread(target=run_detection, daemon=True).start()

        detect_btn = ttk.Button(frame, text="鑷姩妫€娴嬪苟閫夋嫨鏈€蹇暅鍍?, command=auto_detect_mirrors)
        detect_btn.pack(side=tk.LEFT, padx=10, pady=10)

        def save_online_config():
            self.config_manager.set('online_search.zlibrary.email', email_var.get().strip())
            self.config_manager.set('online_search.zlibrary.password', pass_var.get().strip())
            self.config_manager.set('online_search.zlibrary.domain', domain_var.get().strip())
            self.config_manager.set('online_search.annas_archive.domain', annas_domain_var.get().strip())
            messagebox.showinfo("鎴愬姛", "鍦ㄧ嚎鎼滅储閰嶇疆宸蹭繚瀛?)
            config_window.destroy()

        ttk.Button(frame, text="淇濆瓨閰嶇疆", command=save_online_config).pack(side=tk.RIGHT, pady=10)

    def create_menu_bar(self):
        """鍒涘缓椤堕儴鑿滃崟鏍?""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="鏂囦欢 (File)", menu=file_menu)
        file_menu.add_command(label="鎵撳紑鏂囦欢...", command=self.browse_file)
        file_menu.add_command(label="浠?URL 瀵煎叆缃戦〉...", command=self.import_from_url)
        file_menu.add_command(label="浠庡壀璐存澘瀵煎叆鏂囨湰", command=self.import_from_clipboard)
        file_menu.add_separator()
        file_menu.add_command(label="閫€鍑?, command=self.on_closing)

        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="宸ュ叿 (Tools)", menu=tools_menu)
        tools_menu.add_command(label="鏅鸿兘鎻愬彇鏈 (Auto Glossary)", command=self.generate_glossary_action)
        tools_menu.add_command(label="缈昏瘧璁板繂搴撶紪杈戝櫒 (TM Editor)", command=self.open_tm_editor)
        tools_menu.add_command(label="鏍煎紡杞崲宸ュ叿绠?(Format Converter)", command=self.open_format_converter)
        tools_menu.add_command(label="浜戠鍒嗕韩 (Upload & Share)", command=self.open_cloud_share)
        tools_menu.add_separator()
        tools_menu.add_command(label="瀵煎嚭鍙岃瀵圭収 Word (.docx)", command=self.export_bilingual_docx_action)
        tools_menu.add_command(label="鐢熸垚鏈夊０涔?(Audiobook)", command=self.export_audiobook)
        
        # View Menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="瑙嗗浘 (View)", menu=view_menu)
        view_menu.add_command(label="鍒囨崲涓婚 (鏄庝寒/鏆楅粦)", command=self.toggle_theme)

    def import_from_url(self):
        """浠?URL 瀵煎叆缃戦〉鍐呭"""
        url = simpledialog.askstring("瀵煎叆缃戦〉", "璇疯緭鍏ョ綉椤?URL:")
        if not url: return
        
        try:
            self.progress_text_var.set("姝ｅ湪鎶撳彇缃戦〉...")
            # Run in thread to avoid freezing
            def fetch_thread():
                try:
                    title, content = self.web_importer.fetch_content(url)
                    self.root.after(0, lambda: self._load_imported_content(f"URL: {title}", content))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("瀵煎叆澶辫触", str(e)))
                    self.root.after(0, lambda: self.progress_text_var.set("瀵煎叆澶辫触"))
            
            threading.Thread(target=fetch_thread, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("瀵煎叆澶辫触", str(e))

    def import_from_clipboard(self):
        """浠庡壀璐存澘瀵煎叆鏂囨湰"""
        try:
            content = self.root.clipboard_get()
            if not content.strip():
                messagebox.showwarning("鎻愮ず", "鍓创鏉夸负绌?)
                return
            self._load_imported_content("Clipboard Content", content)
            
        except Exception as e:
            messagebox.showerror("閿欒", f"鏃犳硶璇诲彇鍓创鏉? {e}")

    def _load_imported_content(self, title, content):
        """Helper to load content into the editor"""
        self.file_path_var.set(title)
        self.current_text = content
        self.generate_toc(content)
        self.text_signature = self.compute_text_signature(content)
        self.source_segments = []
        self.translated_segments = []
        self.failed_segments = []
        self.resume_from_index = 0
        
        self.original_text.delete('1.0', tk.END)
        self.update_text_display()
        self.file_info_var.set(f"宸插姞杞? {title[:20]}... ({len(content)} 瀛楃)")
        self.progress_text_var.set("瀵煎叆鎴愬姛")
        self.clear_progress_cache()

    def generate_glossary_action(self):
        """鏅鸿兘鎻愬彇鏈"""
        if not self.current_text:
            messagebox.showwarning("璀﹀憡", "璇峰厛鍔犺浇鏂囨湰")
            return
            
        if not messagebox.askyesno("纭", "杩欏皢浣跨敤 LLM 鍒嗘瀽鏂囨湰鍓?4000 瀛楀苟鎻愬彇鏈锛屽彲鑳芥秷鑰楀皯閲?Token銆俓n鏄惁缁х画锛?):
            return
            
        def run_extraction():
            try:
                self.root.after(0, lambda: self.progress_text_var.set("姝ｅ湪鍒嗘瀽鏂囨湰鎻愬彇鏈..."))
                terms = self.smart_glossary.extract_terms(self.current_text)
                
                if not terms:
                    self.root.after(0, lambda: messagebox.showinfo("缁撴灉", "鏈彁鍙栧埌閲嶈鏈"))
                    return
                    
                self.root.after(0, lambda: self._show_glossary_import_dialog(terms))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("閿欒", str(e)))
            finally:
                self.root.after(0, lambda: self.progress_text_var.set("灏辩华"))
                
        threading.Thread(target=run_extraction, daemon=True).start()

    def _show_glossary_import_dialog(self, terms):
        """鏄剧ず鏈瀵煎叆纭瀵硅瘽妗?""
        win = tk.Toplevel(self.root)
        win.title("鎻愬彇鍒扮殑鏈")
        win.geometry("600x400")
        
        ttk.Label(win, text="鍕鹃€夎娣诲姞鍒板綋鍓嶆湳璇〃鐨勮瘝鏉?").pack(pady=5)
        
        frame = ttk.Frame(win)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        check_vars = []
        for i, (term, trans, type_) in enumerate(terms):
            var = tk.BooleanVar(value=True)
            check_vars.append((var, term, trans, type_))
            cb = ttk.Checkbutton(scrollable_frame, text=f"[{type_}] {term} -> {trans}", variable=var)
            cb.pack(anchor="w", padx=5, pady=2)
            
        def do_import():
            count = 0
            target_glossary = "Auto_Extracted"
            if not self.glossary_manager.load_glossary(target_glossary):
                self.glossary_manager.create_glossary(target_glossary, "AI 鑷姩鎻愬彇鐨勬湳璇?)
            
            for var, term, trans, type_ in check_vars:
                if var.get():
                    self.glossary_manager.add_term(target_glossary, term, trans, notes=f"Type: {type_}")
                    count += 1
            
            messagebox.showinfo("鎴愬姛", f"宸插鍏?{count} 涓湳璇埌 '{target_glossary}' 琛?)
            win.destroy()
            
        ttk.Button(win, text="瀵煎叆閫変腑椤?, command=do_import).pack(pady=10)

    def export_bilingual_docx_action(self):
        """瀵煎嚭鍙岃瀵圭収 Word 鏂囨。"""
        if not self.translated_segments:
            messagebox.showwarning("璀﹀憡", "娌℃湁鍙鍑虹殑璇戞枃")
            return
            
        try:
            # Check for docx library
            try:
                import docx
            except ImportError:
                messagebox.showerror("閿欒", "鏈畨瑁?python-docx 搴?)
                return

            filename = filedialog.asksaveasfilename(
                title="瀵煎嚭鍙岃瀵圭収 Word",
                defaultextension=".docx",
                filetypes=[("Word 鏂囨。", "*.docx")]
            )
            if not filename: return
            
            # Use DocxHandler to create it (we instantiate a dummy one or use static method if we had one, 
            # but since we added it as instance method, we can create a temporary handler or just use the logic directly here)
            # Actually, reusing the logic I put in DocxHandler is best, but I need an instance.
            # I will just re-implement the simple logic here to avoid dependency on an existing file for DocxHandler init.
            
            from docx import Document
            from docx.shared import Pt
            
            doc = Document()
            doc.add_heading('鍙岃瀵圭収缈昏瘧 / Bilingual Translation', 0)
            
            table = doc.add_table(rows=1, cols=2)
            table.style = 'Table Grid'
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = '鍘熸枃 (Original)'
            hdr_cells[1].text = '璇戞枃 (Translation)'
            
            limit = max(len(self.source_segments), len(self.translated_segments))
            for i in range(limit):
                row_cells = table.add_row().cells
                
                # Source
                if i < len(self.source_segments):
                    row_cells[0].text = self.source_segments[i]
                
                # Target
                if i < len(self.translated_segments):
                    row_cells[1].text = self.translated_segments[i]
                    
            doc.save(filename)
            messagebox.showinfo("鎴愬姛", f"鍙岃鏂囨。宸插鍑? {filename}")
            
        except Exception as e:
            messagebox.showerror("瀵煎嚭澶辫触", str(e))

    def toggle_theme(self):
        """鍒囨崲鏄庝寒/鏆楅粦涓婚"""
        style = ttk.Style()
        
        if self.current_theme == "light":
            self.current_theme = "dark"
            style.theme_use('clam')
            
            bg_color = "#2b2b2b"
            fg_color = "#ffffff"
            field_bg = "#3c3f41"
            select_bg = "#005fb8"
            
            style.configure(".", background=bg_color, foreground=fg_color)
            style.configure("TLabel", background=bg_color, foreground=fg_color)
            style.configure("TButton", background=field_bg, foreground=fg_color, borderwidth=1)
            style.map("TButton", background=[("active", "#4c5052")])
            style.configure("TEntry", fieldbackground=field_bg, foreground=fg_color)
            style.configure("TCombobox", fieldbackground=field_bg, foreground=fg_color, background=bg_color)
            style.configure("Treeview", background=field_bg, foreground=fg_color, fieldbackground=field_bg)
            style.map("Treeview", background=[("selected", select_bg)])
            style.configure("TLabelframe", background=bg_color, foreground=fg_color)
            style.configure("TLabelframe.Label", background=bg_color, foreground=fg_color)
            
            # Text widgets
            for widget in [self.original_text, self.translated_text_widget, self.failed_source_text, 
                          self.manual_translation_text, self.analysis_text, self.comp_source_text, self.comp_target_text]:
                try:
                    widget.config(bg=field_bg, fg=fg_color, insertbackground=fg_color)
                except: pass
                
            # Listboxes
            for lb in [self.failed_listbox, self.analysis_listbox]:
                try:
                    lb.config(bg=field_bg, fg=fg_color)
                except: pass
            
        else:
            self.current_theme = "light"
            style.theme_use('default')
            
            # Reset Text widgets
            for widget in [self.original_text, self.translated_text_widget, self.failed_source_text, 
                          self.manual_translation_text, self.analysis_text, self.comp_source_text, self.comp_target_text]:
                try:
                    widget.config(bg="white", fg="black", insertbackground="black")
                except: pass
                
            # Reset Listboxes
            for lb in [self.failed_listbox, self.analysis_listbox]:
                try:
                    lb.config(bg="white", fg="black")
                except: pass

    def open_tm_editor(self):
        """鎵撳紑缈昏瘧璁板繂搴撶紪杈戝櫒"""
        TMEditorDialog(self.root, self.translation_memory)

    def open_format_converter(self):
        """鎵撳紑鏍煎紡杞崲宸ュ叿绠?""
        def load_callback(path):
            if path and os.path.exists(path):
                self.root.after(0, lambda: self.file_path_var.set(path))
                self.root.after(0, lambda: self.load_file_content(path))
                
        FormatConverterDialog(self.root, load_callback)

def main():
    """涓荤▼搴忓叆鍙?""
    # 璁剧疆鏃ュ織璁板綍
    class Logger(object):
        def __init__(self, filename="translator.log"):
            self.terminal = sys.stdout
            self.log = open(filename, "a", encoding="utf-8")

        def write(self, message):
            # 閬垮厤鍐欏叆绌鸿鎴栧彧鏈夋崲琛岀鐨勮锛堝彲閫夛級
            self.terminal.write(message)
            self.log.write(message)
            self.log.flush()

        def flush(self):
            self.terminal.flush()
            self.log.flush()

    # 閲嶅畾鍚戣緭鍑哄埌鏃ュ織鏂囦欢
    sys.stdout = Logger()
    sys.stderr = Logger("translator_error.log")
    
    print(f"\n{'='*50}")
    print(f"鍚姩鏃堕棿: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"鐗堟湰: {CONFIG_VERSION}")
    print(f"{'='*50}\n")

    # 妫€鏌ヤ緷璧?
    missing_libs = []
    if not PDF_SUPPORT:
        missing_libs.append("PyPDF2 (鐢ㄤ簬PDF鏀寔)")
    if not EPUB_SUPPORT:
        missing_libs.append("ebooklib, beautifulsoup4 (鐢ㄤ簬EPUB鏀寔)")
    if not GEMINI_SUPPORT:
        missing_libs.append("google-generativeai (鐢ㄤ簬Gemini API)")
    if not OPENAI_SUPPORT:
        missing_libs.append("openai (鐢ㄤ簬OpenAI API)")
    if not REQUESTS_SUPPORT:
        missing_libs.append("requests (鐢ㄤ簬鑷畾涔堿PI)")

    if missing_libs:
        print("=" * 60)
        print("璀﹀憡: 浠ヤ笅搴撴湭瀹夎锛岄儴鍒嗗姛鑳藉皢涓嶅彲鐢?")
        for lib in missing_libs:
            print(f"  - {lib}")
        print("\n瀹夎鍛戒护:")
        print("py -m pip install PyPDF2 ebooklib beautifulsoup4 google-generativeai openai requests")
        print("=" * 60)
        print()

    root = tk.Tk()
    app = BookTranslatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

