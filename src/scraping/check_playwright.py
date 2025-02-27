import subprocess
import shutil

def ensure_playwright_installed():
    """Memeriksa dan menginstal Playwright jika belum tersedia."""
    if shutil.which("playwright") is None:
        try:
            subprocess.run(["python", "-m", "pip", "install", "--upgrade", "playwright"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["python", "-m", "playwright", "install"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True  
        except subprocess.CalledProcessError:
            return False  
    return None
