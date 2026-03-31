#! python
# -*- coding: utf-8 -*-
"""兼容旧入口：转发到 scripts/manual_tests/manual_startup_check.py。"""

from pathlib import Path
import runpy


if __name__ == "__main__":
    script_path = Path(__file__).parent / "scripts" / "manual_tests" / "manual_startup_check.py"
    runpy.run_path(str(script_path), run_name="__main__")
