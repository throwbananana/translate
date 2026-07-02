#! python
# -*- coding: utf-8 -*-
"""Patch `book_translator_gui.pyw` toward guarded translation sessions.

The GitHub contents API replaces whole files, while `book_translator_gui.pyw` is a
large legacy GUI module.  This tool keeps GUI wiring steps reproducible and
reviewable by applying small, idempotent text transformations locally.

Current scope covers the guarded GUI translation migration path:

1. import the controller session/workflow helpers;
2. initialize `TranslationRunGuard` and `current_translation_session` in the GUI;
3. move `start_translation()` resume/reset planning into `start_gui_translation_session(...)`;
4. pass the created session to the translation worker thread;
5. make `stop_translation()` cancel the active guarded session;
6. rewrite `translate_text(...)` into a thin guarded lifecycle adapter;
7. let `translate_segment(...)` consume the immutable config snapshot so the
   worker path no longer reads Tk variables for target language/style settings.

The tool still does not directly execute the patch in CI; it keeps the large GUI
file update reviewable and repeatable before the generated diff is committed.
"""

from __future__ import annotations

import argparse
from pathlib import Path

TARGET = Path("book_translator_gui.pyw")

IMPORT_ANCHOR = "from ui.workstation import ActionBar, ApiPanel, FilePanel, ProgressPanel\n"
CONTROLLER_IMPORT = """from controllers import (
    GuiTranslationWorkerCallbacks,
    TranslationRunGuard,
    cancel_gui_translation_session,
    run_guarded_gui_translation_lifecycle,
    schedule_gui_translation_final_state,
    start_gui_translation_session,
)
"""

INIT_ANCHOR = "        self.translation_thread = None\n"
INIT_GUARD_STATE = """        self.translation_run_guard = TranslationRunGuard()
        self.current_translation_session = None
"""

START_LEGACY_SESSION_PLAN = """        # 计算签名用于断点恢复判断
        current_signature = self.compute_text_signature(self.current_text)
        resume_possible = (
            self.text_signature == current_signature
            and self.source_segments
            and 0 < len(self.translated_segments) < len(self.source_segments)
        )

        # 是否从断点继续
        self.resume_from_index = 0
        if resume_possible:
            resume = messagebox.askyesno(
                "继续翻译",
                f"检测到上次未完成的翻译，是否从第 {len(self.translated_segments) + 1} 段继续？"
            )
            if resume:
                self.resume_from_index = len(self.translated_segments)
                # 确保译文长度与起始段对齐
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
"""

START_SESSION_PLAN = """        # 计算签名用于断点恢复判断，并通过 controller 生成本次会话快照
        current_signature = self.compute_text_signature(self.current_text)
        resume_possible = (
            self.text_signature == current_signature
            and self.source_segments
            and 0 < len(self.translated_segments) < len(self.source_segments)
        )
        resume_requested = False
        if resume_possible:
            resume_requested = messagebox.askyesno(
                "继续翻译",
                f"检测到上次未完成的翻译，是否从第 {len(self.translated_segments) + 1} 段继续？"
            )

        session = start_gui_translation_session(
            self.translation_run_guard,
            api_type=api_type,
            target_language=self.target_language_var,
            style=self.style_var,
            concurrency=self.concurrency_var,
            current_signature=current_signature,
            cached_signature=self.text_signature,
            source_segments=self.source_segments,
            translated_segments=self.translated_segments,
            failed_segments=self.failed_segments,
            resume_requested=resume_requested,
        )
        self.current_translation_session = session
        start_state = session.start_state
        self.resume_from_index = start_state.resume_from_index
        self.source_segments = list(start_state.source_segments)
        self.translated_segments = list(start_state.translated_segments)
        self.failed_segments = list(start_state.failed_segments)
"""

START_LEGACY_PROGRESS = """        self.progress_var.set(
            (self.resume_from_index / max(len(self.source_segments), 1)) * 100
            if self.resume_from_index and self.source_segments else 0
        )
        if not self.resume_from_index:
            self.translated_text = ""
            self.translated_text_widget.delete('1.0', tk.END)
        self.failed_segments = []
"""

START_SESSION_PROGRESS = """        self.progress_var.set(start_state.initial_progress)
        if start_state.should_clear_translated_text:
            self.translated_text = ""
            self.translated_text_widget.delete('1.0', tk.END)
"""

THREAD_OLD = """        # 在新线程中执行翻译
        self.translation_thread = threading.Thread(target=self.translate_text, daemon=True)
        self.translation_thread.start()
"""

THREAD_NEW = """        # 在新线程中执行翻译
        self.translation_thread = threading.Thread(
            target=self.translate_text,
            args=(session,),
            daemon=True,
        )
        self.translation_thread.start()
"""

STOP_OLD = """    def stop_translation(self):
        \"\"\"停止翻译\"\"\"
        self.is_translating = False
        self.translate_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.progress_text_var.set("翻译已停止")
"""

STOP_NEW = """    def stop_translation(self):
        \"\"\"停止翻译\"\"\"
        cancel_gui_translation_session(self.translation_run_guard)
        self.current_translation_session = None
        self.is_translating = False
        self.translate_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.progress_text_var.set("翻译已停止")
"""

TRANSLATE_TEXT_LEGACY = '''    def translate_text(self):
        """执行翻译（在后台线程中，支持并发）"""
        try:
            # 同步配置到引擎
            self.sync_engine_config()
            
            # 获取当前翻译API类型
            api_type = self.get_translation_api_type()
            self.consecutive_failures = 0

            # 准备
            self.root.after(0, self.progress_text_var.set, "正在进行文本分段...")

            # 使用 FileProcessor 进行分段
            self.source_segments = self.file_processor.split_text_into_segments(self.current_text, max_length=800)
            total_segments = len(self.source_segments)
            self.text_signature = self.compute_text_signature(self.current_text)
            start_index = min(self.resume_from_index or 0, total_segments)

            self.root.after(0, self.progress_text_var.set, f"文本已分为 {total_segments} 段，准备开始翻译...")
            if start_index:
                self.root.after(
                    0,
                    self.progress_var.set,
                    (start_index / total_segments) * 100 if total_segments else 0
                )
                self.root.after(
                    0,
                    self.progress_text_var.set,
                    f"继续翻译：从第 {start_index + 1} 段开始..."
                )

            # 预填充翻译列表，确保索引对齐
            if len(self.translated_segments) < total_segments:
                self.translated_segments.extend([""] * (total_segments - len(self.translated_segments)))

            # 获取并发设置
            max_workers = self.concurrency_var.get()
            remaining_segments = max(total_segments - start_index, 0)
            max_workers = max(1, min(max_workers, remaining_segments or 1))
            use_context = max_workers == 1  # 只有单线程模式才启用上下文
            
            # 定义单个任务函数
            def process_segment(idx):
                if not self.is_translating or self.paused_due_to_failures:
                    return None
                    
                segment = self.source_segments[idx]
                
                # 获取上下文（仅单线程有效）
                context = None
                if use_context and idx > 0:
                    prev_trans = self.translated_segments[idx-1]
                    # 确保前一段已翻译且不是错误信息
                    if prev_trans and not prev_trans.startswith("["):
                        context = prev_trans

                try:
                    result = self.translate_segment(api_type, segment, context)
                    return (idx, result, None)
                except Exception as e:
                    return (idx, None, str(e))

            # 执行翻译循环
            if max_workers > 1:
                # 并发模式
                self.root.after(0, self.progress_text_var.set, f"正在并发翻译 (线程数: {max_workers})...")
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # 创建剩余任务
                    futures = {
                        executor.submit(process_segment, i): i 
                        for i in range(start_index, total_segments)
                    }
                    
                    completed_count = start_index
                    for future in as_completed(futures):
                        if not self.is_translating or self.paused_due_to_failures:
                            executor.shutdown(wait=False, cancel_futures=True)
                            break
                            
                        try:
                            idx, result, error = future.result()
                        except Exception as e:
                            idx = futures[future]
                            result = None
                            error = str(e)
                        
                        if result:
                            self.translated_segments[idx] = result
                            self.consecutive_failures = 0
                        else:
                            self.consecutive_failures += 1
                            self.translated_segments[idx] = f"[翻译错误: {error}]\\n{self.source_segments[idx]}"
                            print(f"翻译段落 {idx + 1} 失败: {error}")
                            
                            if self.consecutive_failures >= self.max_consecutive_failures:
                                self.paused_due_to_failures = True
                                self.resume_from_index = idx  # 记录暂停位置（大概）
                        
                        completed_count += 1
                        progress = (completed_count / total_segments) * 100
                        self.root.after(0, self.progress_var.set, progress)
                        self.root.after(0, self.progress_text_var.set, f"正在翻译... {completed_count}/{total_segments} 段")
                        
                        # 定期保存和更新UI (不必每段都更新，减少开销)
                        if completed_count % 5 == 0:
                            self.save_progress_cache()
                            current_text = "\\n\\n".join(seg for seg in self.translated_segments if seg)
                            self.root.after(0, self.update_translated_text, current_text)
            else:
                # 单线程模式 (保持原逻辑以支持上下文)
                for idx in range(start_index, total_segments):
                    if not self.is_translating:
                        break
                    
                    # 重新调用 process_segment 逻辑
                    _, result, error = process_segment(idx)
                    
                    if result:
                        self.translated_segments[idx] = result
                        self.consecutive_failures = 0
                    else:
                        self.consecutive_failures += 1
                        self.translated_segments[idx] = f"[翻译错误: {error}]\\n{self.source_segments[idx]}"
                        
                        if self.consecutive_failures >= self.max_consecutive_failures:
                            self.paused_due_to_failures = True
                            self.resume_from_index = idx
                            break
                    
                    progress = ((idx + 1) / total_segments) * 100
                    self.root.after(0, self.progress_var.set, progress)
                    self.root.after(0, self.progress_text_var.set, f"正在翻译... {idx + 1}/{total_segments} 段")
                    
                    # 实时更新
                    self.translated_text = "\\n\\n".join(self.translated_segments[:idx+1])
                    self.root.after(0, self.update_translated_text, self.translated_text)
                    self.save_progress_cache()
                    
                    time.sleep(0.2) # 避免单线程下的API限流

            # 翻译完成后的处理
            if self.is_translating and not self.paused_due_to_failures:
                # 最终更新一次完整文本
                self.translated_text = "\\n\\n".join(self.translated_segments)
                self.root.after(0, self.update_translated_text, self.translated_text)
                
                self.root.after(0, self.progress_text_var.set, "正在检查译文...")
                # 暂时只在单线程模式下重试，并发模式下重试逻辑较复杂
                if max_workers == 1:
                    self.verify_and_retry_segments(api_type)

                self.root.after(0, self.refresh_failed_segments_view)
                self.root.after(0, self.progress_var.set, 100)
                
                failed_count = sum(1 for s in self.translated_segments if s.startswith("[翻译错误") or s.startswith("[未翻译"))
                status_msg = (
                    f"翻译完成，有 {failed_count} 段可能需要检查"
                    if failed_count else "翻译完成!"
                )
                self.root.after(0, self.progress_text_var.set, status_msg)
                self.root.after(0, self.on_translation_complete)
                if failed_count == 0:
                    self.clear_progress_cache()
            else:
                status_msg = "翻译已停止"
                if self.paused_due_to_failures:
                    status_msg = "已暂停，等待API恢复后可继续"
                self.root.after(0, self.progress_text_var.set, status_msg)

        except Exception as e:
            self.root.after(
                0,
                messagebox.showerror,
                "错误",
                f"翻译过程中出错:\\n{str(e)}"
            )
        finally:
            self.root.after(0, self.translate_btn.config, {'state': 'normal'})
            self.root.after(0, self.stop_btn.config, {'state': 'disabled'})
            self.is_translating = False
'''

TRANSLATE_TEXT_GUARDED = '''    def translate_text(self, session=None):
        """执行翻译（在后台线程中，通过 guarded workflow 运行）"""
        if session is None:
            session = self.current_translation_session
        if session is None:
            self.root.after(0, self.progress_text_var.set, "翻译会话不存在，已停止")
            self.root.after(0, self.translate_btn.config, {'state': 'normal'})
            self.root.after(0, self.stop_btn.config, {'state': 'disabled'})
            self.is_translating = False
            return

        try:
            # 同步配置到引擎
            self.sync_engine_config()

            config = session.config
            self.consecutive_failures = 0
            self.text_signature = self.compute_text_signature(self.current_text)

            callbacks = GuiTranslationWorkerCallbacks(
                split_text=lambda text, max_length: self.file_processor.split_text_into_segments(
                    text,
                    max_length=max_length,
                ),
                translate_segment=lambda idx, segment, context: self.translate_segment(
                    config.api_type,
                    segment,
                    context,
                    config=config,
                ),
                is_active=lambda: self.is_translating,
                should_pause=lambda: self.paused_due_to_failures,
                set_status=self.progress_text_var.set,
                set_progress=self.progress_var.set,
                update_snapshot=self._update_guarded_translation_snapshot,
                on_error=lambda exc: messagebox.showerror(
                    "错误",
                    f"翻译过程中出错:\\n{str(exc)}",
                ),
            )

            finish_state = run_guarded_gui_translation_lifecycle(
                guard=self.translation_run_guard,
                run_id=session.run_id,
                scheduler=self.root.after,
                text=self.current_text,
                config=config,
                callbacks=callbacks,
                existing_translations=self.translated_segments,
                resume_from_index=self.resume_from_index,
                max_consecutive_failures=self.max_consecutive_failures,
                target_language=config.target_language,
            )
            schedule_gui_translation_final_state(
                self.translation_run_guard,
                session,
                self.root.after,
                self._apply_guarded_translation_finish_state,
                finish_state,
            )
        except Exception as e:
            self.root.after(
                0,
                messagebox.showerror,
                "错误",
                f"翻译过程中出错:\\n{str(e)}"
            )
        finally:
            self.is_translating = False

    def _update_guarded_translation_snapshot(self, translated_text):
        """Apply a guarded worker text snapshot on the GUI thread."""
        self.translated_text = translated_text
        self.update_translated_text(translated_text)

    def _apply_guarded_translation_finish_state(self, finish_state):
        """Apply finalized guarded worker state to legacy GUI fields/widgets."""
        self.source_segments = list(finish_state.source_segments)
        self.translated_segments = list(finish_state.translated_segments)
        self.failed_segments = list(finish_state.failed_segments)
        self.translated_text = finish_state.translated_text
        self.update_translated_text(finish_state.translated_text)
        self.refresh_failed_segments_view()
        self.progress_var.set(finish_state.progress)
        self.progress_text_var.set(finish_state.status_message)

        if finish_state.should_call_completion_hook:
            self.on_translation_complete()

        if finish_state.should_clear_progress_cache:
            self.clear_progress_cache()
        else:
            self.save_progress_cache()

        self.current_translation_session = None
        self.translate_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.is_translating = False
'''

TRANSLATE_SEGMENT_LEGACY = '''    def translate_segment(self, api_type, text, context=None):
        """按当前API类型翻译单段文本（使用统一翻译引擎）"""
        target_language = self.get_target_language()
        target_is_chinese = self.is_target_language_chinese(target_language)
        target_is_english = self.is_target_language_english(target_language)

        # 检测语言，如果已经是目标语言就跳过翻译
        lang = self.detect_language(text)
        if (target_is_chinese and lang == 'zh') or (target_is_english and lang == 'en'):
            return text
        
        # 构建风格提示
        style = self.style_var.get()
        style_prompt_map = {
            "直译 (Literal)": "请进行精准直译，严格保留原文的句子结构和语气，不要过度意译。",
            "通俗小说 (Novel)": "请采用通俗小说的笔法，用词生动、流畅，注重情节的连贯性和人物语气的自然，符合目标语言读者的阅读习惯。",
            "日式轻小说 (Light Novel)": "请采用日式轻小说译法，语气轻快自然，保留角色台词的个性、吐槽感、心理独白和章节节奏；专有名词、人名、称呼、拟声词与口癖应前后一致，避免过度文言化或学术化。",
            "学术专业 (Academic)": "请采用学术风格，用词严谨、专业，句式规范，确保术语准确，适合学术研究或专业人士阅读。",
            "武侠/古风 (Wuxia)": "请采用中国古典武侠或古风小说的笔触，用词典雅、古朴，半文半白，注重意境的渲染。",
            "新闻/媒体 (News)": "请采用新闻报道的风格，客观、简练、信息传达准确，符合新闻媒体的规范。"
        }
        style_guide = style_prompt_map.get(style, "")
        if style_guide:
            style_guide = f"风格要求：{style_guide}"
        
        # 调用翻译引擎
        # 注意：engine会自动处理翻译记忆、术语表、API调用、错误回退
        result = self.translation_engine.translate(
            text=text,
            target_lang=target_language,
            provider=self._engine_provider_name(api_type),
            use_memory=True,
            use_glossary=True,
            context=context,
            extra_prompt=style_guide
        )
        
        if result.success:
            return result.translated_text
        else:
            # 如果失败，抛出异常以便上层捕获处理（如记录失败段落）
            raise Exception(result.error or "未知翻译错误")
'''

TRANSLATE_SEGMENT_CONFIGURED = '''    def translate_segment(self, api_type, text, context=None, config=None):
        """按当前API类型翻译单段文本（使用统一翻译引擎）"""
        target_language = config.target_language if config is not None else self.get_target_language()
        target_is_chinese = self.is_target_language_chinese(target_language)
        target_is_english = self.is_target_language_english(target_language)

        # 检测语言，如果已经是目标语言就跳过翻译
        lang = self.detect_language(text)
        if (target_is_chinese and lang == 'zh') or (target_is_english and lang == 'en'):
            return text

        # 构建风格提示。Guarded worker runs pass an immutable config snapshot so
        # this method does not need to read Tk variables from the background thread.
        if config is not None:
            style_guide = config.style_prompt
            use_memory = config.use_memory
            use_glossary = config.use_glossary
        else:
            style = self.style_var.get()
            style_prompt_map = {
                "直译 (Literal)": "请进行精准直译，严格保留原文的句子结构和语气，不要过度意译。",
                "通俗小说 (Novel)": "请采用通俗小说的笔法，用词生动、流畅，注重情节的连贯性和人物语气的自然，符合目标语言读者的阅读习惯。",
                "日式轻小说 (Light Novel)": "请采用日式轻小说译法，语气轻快自然，保留角色台词的个性、吐槽感、心理独白和章节节奏；专有名词、人名、称呼、拟声词与口癖应前后一致，避免过度文言化或学术化。",
                "学术专业 (Academic)": "请采用学术风格，用词严谨、专业，句式规范，确保术语准确，适合学术研究或专业人士阅读。",
                "武侠/古风 (Wuxia)": "请采用中国古典武侠或古风小说的笔触，用词典雅、古朴，半文半白，注重意境的渲染。",
                "新闻/媒体 (News)": "请采用新闻报道的风格，客观、简练、信息传达准确，符合新闻媒体的规范。"
            }
            style_guide = style_prompt_map.get(style, "")
            if style_guide:
                style_guide = f"风格要求：{style_guide}"
            use_memory = True
            use_glossary = True

        # 调用翻译引擎
        # 注意：engine会自动处理翻译记忆、术语表、API调用、错误回退
        result = self.translation_engine.translate(
            text=text,
            target_lang=target_language,
            provider=self._engine_provider_name(api_type),
            use_memory=use_memory,
            use_glossary=use_glossary,
            context=context,
            extra_prompt=style_guide
        )

        if result.success:
            return result.translated_text
        else:
            # 如果失败，抛出异常以便上层捕获处理（如记录失败段落）
            raise Exception(result.error or "未知翻译错误")
'''


def _insert_after_once(text: str, anchor: str, insertion: str) -> str:
    if insertion in text:
        return text
    if anchor not in text:
        raise ValueError(f"Anchor not found: {anchor!r}")
    return text.replace(anchor, anchor + insertion, 1)


def _replace_once(text: str, old: str, new: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise ValueError("Expected source block was not found")
    return text.replace(old, new, 1)


def _replace_required_method_when_present(
    text: str,
    *,
    method_name: str,
    old: str,
    new: str,
) -> str:
    if new in text:
        return text
    if old in text:
        return text.replace(old, new, 1)
    if f"    def {method_name}" in text:
        raise ValueError(f"Expected source block for {method_name} was not found")
    return text


def _ensure_controller_import(text: str) -> str:
    if CONTROLLER_IMPORT in text:
        return text

    marker = "from controllers import ("
    if marker in text:
        start = text.index(marker)
        end = text.index(")\n", start) + len(")\n")
        existing = text[start:end]
        if "TranslationRunGuard" in existing or "start_gui_translation_session" in existing:
            return text[:start] + CONTROLLER_IMPORT + text[end:]

    return _insert_after_once(text, IMPORT_ANCHOR, CONTROLLER_IMPORT)


def apply_wiring_patch(text: str) -> str:
    """Return `book_translator_gui.pyw` with guarded session wiring applied."""
    text = _ensure_controller_import(text)
    text = _insert_after_once(text, INIT_ANCHOR, INIT_GUARD_STATE)
    text = _replace_once(text, START_LEGACY_SESSION_PLAN, START_SESSION_PLAN)
    text = _replace_once(text, START_LEGACY_PROGRESS, START_SESSION_PROGRESS)
    text = _replace_once(text, THREAD_OLD, THREAD_NEW)
    text = _replace_once(text, STOP_OLD, STOP_NEW)
    text = _replace_required_method_when_present(
        text,
        method_name="translate_text",
        old=TRANSLATE_TEXT_LEGACY,
        new=TRANSLATE_TEXT_GUARDED,
    )
    text = _replace_required_method_when_present(
        text,
        method_name="translate_segment",
        old=TRANSLATE_SEGMENT_LEGACY,
        new=TRANSLATE_SEGMENT_CONFIGURED,
    )
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        default=TARGET,
        type=Path,
        help="Path to book_translator_gui.pyw",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if the file would change instead of writing it.",
    )
    args = parser.parse_args()

    path = args.path
    original = path.read_text(encoding="utf-8")
    patched = apply_wiring_patch(original)

    if args.check:
        if patched != original:
            print(f"{path} needs guarded session wiring")
            return 1
        print(f"{path} is already wired for the guarded session pass")
        return 0

    if patched == original:
        print(f"{path} already up to date")
        return 0

    path.write_text(patched, encoding="utf-8")
    print(f"Applied guarded session wiring to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
