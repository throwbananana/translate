import requests
from bs4 import BeautifulSoup

def inspect():
    url = "https://annas-archive.li/search?q=python"
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        items = soup.select('a[href*="/md5/"]')
        if items:
            first = items[0]
            parent = first.parent
            print("Parent classes:", parent.get('class'))
            
            h3 = parent.find('h3')
            if h3:
                print("Found h3 in parent:", h3.get_text(strip=True))
            else:
                print("No h3 in parent.")
                # Print all text in parent
                print("Parent text:", parent.get_text(strip=True)[:100])
            
    except Exception as e:
        print(e)

if __name__ == "__main__":
    inspect()
