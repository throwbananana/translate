import requests
from bs4 import BeautifulSoup

def inspect():
    url = "https://annas-archive.li/search?q=python"
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        items = soup.select('a[href*="/md5/"]')
        print(f"Total items: {len(items)}")
        
        for i, item in enumerate(items[:10]):
            text = item.get_text(strip=True)
            href = item.get('href')
            print(f"[{i}] Text: '{text[:30]}...' | Href: {href}")
            
    except Exception as e:
        print(e)

if __name__ == "__main__":
    inspect()
