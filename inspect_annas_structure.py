import requests
from bs4 import BeautifulSoup

def inspect():
    # 1. We know this book exists from previous run
    # https://annas-archive.li/md5/ed199f03906ed5fbc278f512c63c19b9
    
    # Let's try to fetch a specific slow download link we saw:
    # /slow_download/ed199f03906ed5fbc278f512c63c19b9/0/0
    
    base_url = "https://annas-archive.li"
    slow_path = "/slow_download/ed199f03906ed5fbc278f512c63c19b9/0/0"
    full_url = base_url + slow_path
    
    print(f"Testing Slow Download: {full_url}")
    
    try:
        # Use stream=True to avoid downloading the whole file if it's large
        r = requests.get(full_url, stream=True, timeout=15)
        
        print(f"Status Code: {r.status_code}")
        print(f"Headers: {r.headers}")
        
        content_type = r.headers.get('Content-Type', '')
        print(f"Content-Type: {content_type}")
        
        if 'text/html' in content_type:
            print("\nIt's an HTML page. Inspecting content...")
            # Read a bit of content
            chunk = next(r.iter_content(chunk_size=4096))
            soup = BeautifulSoup(chunk, 'html.parser')
            print(soup.prettify()[:500])
            
            # Check for "click here to download" links
            print("\nChecking for nested download links:")
            for a in soup.find_all('a', href=True):
                print(f"Link: {a['href']} | Text: {a.get_text(strip=True)}")
        else:
            print("\nIt appears to be a direct file stream!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect()
