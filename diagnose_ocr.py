import sys
import os
import subprocess

print("=== OCR Environment Diagnostic Tool ===")
print(f"Python: {sys.version}")

# 1. Check Libraries
print("\n[1] Checking Python Libraries...")
try:
    import PIL
    import PIL.Image
    print(f"  - Pillow: INSTALLED (v{PIL.__version__})")
except ImportError:
    print("  - Pillow: NOT INSTALLED")

try:
    import pytesseract
    print(f"  - pytesseract: INSTALLED (v{pytesseract.get_tesseract_version()})")
except ImportError:
    print("  - pytesseract: NOT INSTALLED")
except Exception as e:
    print(f"  - pytesseract: INSTALLED but error getting version: {e}")

# 2. Check Tesseract Executable
print("\n[2] Checking Tesseract Executable...")

def find_tesseract():
    # 1. Try PATH
    import shutil
    if shutil.which('tesseract'):
        return 'tesseract'
    
    # 2. Try common Windows paths
    if os.name == 'nt':
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\Tesseract-OCR\tesseract.exe")
        ]
        for path in common_paths:
            if os.path.exists(path):
                print(f"  - Auto-detected Tesseract at: {path}")
                return path
    return None

try:
    import pytesseract
    from PIL import Image
    
    # Check/Configure Tesseract
    tess_path = find_tesseract()
    if tess_path and tess_path != 'tesseract':
        pytesseract.pytesseract.tesseract_cmd = tess_path
    
    # Create a simple image for testing
    img = Image.new('RGB', (100, 30), color = (255, 255, 255))
    
    try:
        # Try simple English OCR
        print("  - Attempting simple OCR (lang='eng')...")
        pytesseract.image_to_string(img, lang='eng')
        print("  - SUCCESS: Tesseract executable found and working.")
    except pytesseract.TesseractNotFoundError:
        print("  - ERROR: Tesseract executable NOT found via pytesseract.")
        print("    This usually means it's not in PATH or pytesseract can't find it.")
        print(f"    Current PATH: {os.environ.get('PATH')}")
    except Exception as e:
        print(f"  - ERROR during execution: {e}")

    # Try Japanese OCR
    try:
        print("  - Attempting Japanese OCR (lang='jpn')...")
        pytesseract.image_to_string(img, lang='jpn')
        print("  - SUCCESS: Japanese language data found.")
    except Exception as e:
        print(f"  - WARNING: Japanese OCR failed. Missing 'jpn' language data? Error: {e}")

except Exception as e:
    print(f"  - Critical error: {e}")

# 3. Verifying Tesseract command line
print("\n[3] Verifying 'tesseract --version' command line...")
try:
    result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True, check=True)
    print(f"  - Command 'tesseract --version' output:\n{result.stdout}")
except FileNotFoundError:
    print("  - Command 'tesseract' not found in system PATH (via direct subprocess call).")
    print("    This confirms tesseract.exe is NOT directly executable from command line.")
except Exception as e:
    print(f"  - Error running 'tesseract --version': {e}")
    print("    This usually indicates an issue with the tesseract executable or its environment.")


print("\n=== Diagnostic Complete ===")
input("Press Enter to exit...")