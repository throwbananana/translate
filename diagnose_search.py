import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote

def test_url(name, base_url, search_path, query="python"):
    print(f"\n--- Testing {name} ---")
    print(f"Base URL: {base_url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        # Short timeout for mirror checking
        response = requests.get(base_url, headers=headers, timeout=5)
        print(f"Connectivity: OK (Status: {response.status_code})")
        
        if response.status_code == 200:
            # Try a search if connectivity is good
            if "{query}" in search_path:
                full_url = f"{base_url.rstrip('/')}{search_path.format(query=quote(query))}"
                print(f"Search Test: {full_url}")
                search_resp = requests.get(full_url, headers=headers, timeout=10)
                print(f"Search Status: {search_resp.status_code}")
                if search_resp.status_code == 200:
                    print(">>> SUCCESS: This mirror seems to work! <<<")
                    return True
            else:
                # Just a domain check
                print(">>> SUCCESS: Domain is reachable! <<<")
                return True
                
    except Exception as e:
        print(f"Connectivity: FAILED ({str(e)[:50]}...)")
    
    return False

if __name__ == "__main__":
    mirrors = [
        # Anna's Archive
        ("Anna's (.li)", "https://annas-archive.li", "/search?q={query}"),
        ("Anna's (.se)", "https://annas-archive.se", "/search?q={query}"),
        ("Anna's (.gs)", "https://annas-archive.gs", "/search?q={query}"),
        
        # Z-Library (Login/Search gateways)
        ("Z-Lib (singlelogin.re)", "https://singlelogin.re", ""), # Login portal
        ("Z-Lib (z-library.rs)", "https://z-library.rs", ""),     # Info/search
        ("Z-Lib (z-lib.do)", "https://z-lib.do", "/s/{query}"),
    ]

    working_mirrors = []
    for name, url, path in mirrors:
        if test_url(name, url, path):
            working_mirrors.append((name, url))

    print("\n\n=== SUMMARY ===")
    if working_mirrors:
        print("Found working mirrors:")
        for name, url in working_mirrors:
            print(f"- {name}: {url}")
    else:
        print("No alternative mirrors found. Proxy might be required.")