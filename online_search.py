#! python
# -*- coding: utf-8 -*-
"""
Online Search Module (experimental)

Default behavior is conservative:
- keep metadata lookup support
- disable Z-Library integration unless explicitly enabled
"""

import os
import requests
from bs4 import BeautifulSoup
import re
import json
from pathlib import Path
from urllib.parse import quote, urljoin
import time
import threading
from typing import List, Dict, Optional, Any

class CloudflareError(Exception):
    """Raised when Cloudflare blocks the request"""
    pass

class OnlineSearchManager:
    """Online search and download manager"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Referer': 'https://annas-archive.li/'
        }
        self.session.headers.update(self.headers)
        
    def _get_zlib_config(self):
        return self.config_manager.get('online_search.zlibrary', {})
        
    def _get_annas_config(self):
        return self.config_manager.get('online_search.annas_archive', {})

    def _zlibrary_enabled(self) -> bool:
        """Z-Library 集成默认关闭，只允许显式启用。"""
        env_value = os.getenv('TRANSLATE_ENABLE_ZLIBRARY')
        if env_value is not None:
            return env_value.strip().lower() in {'1', 'true', 'yes', 'on'}

        return bool(self.config_manager.get('online_search.enable_zlibrary', False))

    def check_mirrors(self) -> Dict[str, List[Dict]]:
        """
        Check availability and latency of known mirrors.
        Returns a dict with 'zlibrary' and 'annas_archive' lists.
        """
        annas_mirrors = [
            "https://annas-archive.li",
            "https://annas-archive.se",
            "https://annas-archive.gs"
        ]
        zlib_mirrors = [
            "https://singlelogin.re",
            "https://z-library.rs",
            "https://z-lib.do"
        ]
        
        results = {'annas_archive': [], 'zlibrary': []}
        
        def check_url(url, target_list):
            try:
                start = time.time()
                resp = requests.get(url, timeout=5, headers=self.headers)
                latency = (time.time() - start) * 1000
                if resp.status_code == 200:
                    target_list.append({'url': url, 'latency': int(latency), 'status': 'OK'})
                else:
                    target_list.append({'url': url, 'latency': 9999, 'status': f'Error {resp.status_code}'})
            except Exception as e:
                target_list.append({'url': url, 'latency': 9999, 'status': 'Failed'})

        threads = []
        for url in annas_mirrors:
            t = threading.Thread(target=check_url, args=(url, results['annas_archive']))
            threads.append(t)
            t.start()
            
        if self._zlibrary_enabled():
            for url in zlib_mirrors:
                t = threading.Thread(target=check_url, args=(url, results['zlibrary']))
                threads.append(t)
                t.start()
            
        for t in threads:
            t.join()
            
        # Sort by latency
        results['annas_archive'].sort(key=lambda x: x['latency'])
        results['zlibrary'].sort(key=lambda x: x['latency'])
        
        return results
        
    def login_zlibrary(self) -> bool:
        """Login to Z-Library"""
        if not self._zlibrary_enabled():
            return False

        config = self._get_zlib_config()
        email = config.get('email')
        password = config.get('password')
        domain = config.get('domain', 'https://singlelogin.re')
        
        if not email or not password:
            return False
            
        try:
            login_url = urljoin(domain, '/login.php')
            data = {
                'email': email,
                'password': password,
                'remmember': 1
            }
            response = self.session.post(login_url, data=data, timeout=20)
            
            if response.status_code == 200 and ('logout' in response.text.lower() or 'profile' in response.text.lower()):
                return True
            return False
        except Exception as e:
            print(f"Z-Library login failed: {e}")
            return False

    def search_annas_archive(self, query: str, page: int = 1) -> List[Dict]:
        """Search from Anna's Archive with improved parsing"""
        config = self._get_annas_config()
        domain = config.get('domain', 'https://annas-archive.li')
        search_url = f"{domain.rstrip('/')}/search?q={quote(query)}&page={page}"
        
        results = []
        try:
            response = self.session.get(search_url, timeout=30)
            if response.status_code == 403:
                raise CloudflareError("Cloudflare protection active")
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            # Anna's layout uses <a> tags with href containing /md5/
            # and usually a flexbox layout for details
            items = soup.select('a[href*="/md5/"]')
            
            for item in items:
                href = item.get('href')
                if not href: continue
                
                # Title is usually in h3 or plain text in the link
                title = ""
                title_tag = item.find('h3')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                else:
                    # Fallback: look for bold text or just the first non-gray div
                    # Anna's HTML is messy, often title is just text inside the anchor
                    # But often there is a div with class containing 'text-xl' or similar
                    divs = item.find_all('div')
                    for d in divs:
                        if 'italic' in d.get('class', []): # usually author
                            continue
                        if len(d.get_text(strip=True)) > 2:
                            title = d.get_text(strip=True)
                            break
                    if not title:
                        title = item.get_text(strip=True)

                if not title: continue

                # Extract Metadata (Author, Publisher, etc.)
                author = "Unknown"
                publisher = ""
                file_info = ""
                
                # Author is often in italic
                author_tag = item.find('div', class_='italic')
                if author_tag:
                    author = author_tag.get_text(strip=True)
                
                # File info (Language, Extension, Size) is usually in gray text
                meta_divs = item.find_all('div', class_=lambda x: x and 'text-gray' in x)
                raw_metadata = []
                for md in meta_divs:
                    txt = md.get_text(strip=True)
                    if txt: raw_metadata.append(txt)
                
                # Parse metadata string like "English [en], pdf, 10.2MB"
                # Or sometimes it's separate divs
                full_metadata = ", ".join(raw_metadata)
                
                # Try to parse specific fields
                lang = "Unknown"
                ext = "Unknown"
                size = "Unknown"
                category = "Uncategorized"
                
                # Heuristics for Anna's metadata
                for part in full_metadata.split(','):
                    part = part.strip()
                    if part in ['pdf', 'epub', 'mobi', 'azw3', 'txt']:
                        ext = part
                    elif 'MB' in part or 'KB' in part:
                        size = part
                    elif '[' in part and ']' in part: 
                        lang = part
                    elif '(' in part and ')' in part: # Often contains category like (Fiction)
                        category = part.strip('()')
                
                results.append({
                    'title': title,
                    'author': author,
                    'publisher': publisher,
                    'language': lang,
                    'extension': ext,
                    'size': size,
                    'url': urljoin(domain, href),
                    'source': "Anna's Archive",
                    'category': category,
                    'metadata': full_metadata[:100],
                    'id': href.split('/')[-1]
                })
            
            return results
        except CloudflareError:
            print("Anna's Archive returned 403 Forbidden (Cloudflare).")
            return []
        except Exception as e:
            print(f"Anna's Archive search failed: {e}")
            return []

    def search_zlibrary(self, query: str, page: int = 1, languages: List[str] = None) -> List[Dict]:
        """Search from Z-Library"""
        if not self._zlibrary_enabled():
            return []

        config = self._get_zlib_config()
        domain = config.get('domain', 'https://singlelogin.re')
        
        lang_param = ""
        if languages:
            # Map codes to full names for Z-Lib: languages[0]=chinese
            code_map = {'zh': 'chinese', 'en': 'english', 'ja': 'japanese', 'ko': 'korean', 'fr': 'french', 'de': 'german'}
            for i, l in enumerate(languages):
                full = code_map.get(l, l)
                lang_param += f"&languages[{i}]={full}"

        search_url = f"{domain.rstrip('/')}/s/{quote(query)}/?page={page}{lang_param}"
        
        results = []
        try:
            response = self.session.get(search_url, timeout=30)
            if response.status_code == 404 or 'login' in response.url:
                 # Try re-login
                if self.login_zlibrary():
                    response = self.session.get(search_url, timeout=30)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.select('tr.bookRow')
            
            for item in items:
                title_link = item.select_one('h3 a')
                if not title_link: continue
                
                title = title_link.get_text(strip=True)
                href = title_link.get('href')
                
                authors = ""
                authors_div = item.select_one('div.authors')
                if authors_div:
                    authors = authors_div.get_text(strip=True)
                
                # Property extraction
                ext = "Unknown"
                size = "Unknown"
                lang = "Unknown"
                category = "Uncategorized"
                
                prop_divs = item.select('div.bookProperty')
                for prop in prop_divs:
                    txt = prop.get_text(strip=True)
                    if 'MB' in txt or 'KB' in txt:
                        size = txt
                    elif 'property_categories' in prop.get('class', []):
                        category = txt.replace("Categories:", "").strip()
                    elif ',' in txt: 
                        parts = txt.split(',')
                        if len(parts) >= 1: ext = parts[0].strip()
                    else:
                        if txt.lower() in ['chinese', 'english', 'spanish']:
                            lang = txt
                
                results.append({
                    'title': title,
                    'author': authors,
                    'publisher': "",
                    'language': lang,
                    'extension': ext,
                    'size': size,
                    'url': urljoin(domain, href),
                    'source': "Z-Library",
                    'category': category,
                    'metadata': f"{ext}, {size}",
                    'id': href.split('/')[-1] if '/' in href else href
                })
                
            return results
        except Exception as e:
            print(f"Z-Library search failed: {e}")
            return []

    def download_book(self, result_item: Dict, progress_callback=None) -> Optional[str]:
        """
        Download book.
        Raises CloudflareError if 403 encountered, allowing GUI to fallback to browser.
        """
        url = result_item['url']
        source = result_item['source']
        
        try:
            # 1. Get the download page
            response = self.session.get(url, timeout=30)
            if response.status_code == 403:
                raise CloudflareError(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            download_url = None
            
            if source == "Z-Library":
                dl_btn = soup.select_one('a.btn.btn-primary.dlButton')
                if dl_btn:
                    download_url = urljoin(url, dl_btn.get('href'))
                    
            else: # Anna's Archive
                # Prioritize "Slow Partner Server"
                # Look for links containing 'slow_download'
                slow_links = soup.find_all('a', href=lambda x: x and '/slow_download/' in x)
                if slow_links:
                    download_url = urljoin(url, slow_links[0]['href'])
                else:
                    # Fallback to any get link
                    dl_links = soup.select('a[href*="/get/"]') or soup.select('a.download-button')
                    if dl_links:
                        download_url = urljoin(url, dl_links[0].get('href'))
            
            if not download_url:
                print("No download URL found on page.")
                return None
                
            # 2. Download the file
            print(f"Attempting download from: {download_url}")
            dl_response = self.session.get(download_url, stream=True, timeout=60)
            
            if dl_response.status_code == 403:
                raise CloudflareError(download_url)
                
            # Check content type - if html, it's likely an error page or interstitial
            content_type = dl_response.headers.get('content-type', '').lower()
            if 'text/html' in content_type:
                # If we expected a file but got HTML, it might be a "Wait" page
                # For now, treat as failure/need browser
                print("Got HTML instead of file. Likely interstitial.")
                raise CloudflareError(download_url) # Treat as browser-required for now

            dl_response.raise_for_status()
            
            # 3. Determine filename
            filename = ""
            if 'content-disposition' in dl_response.headers:
                cd = dl_response.headers['content-disposition']
                names = re.findall("filename=\"?([^\";]+)\"?", cd)
                if names:
                    filename = names[0].strip()
            
            if not filename:
                # Construct from title + ext
                safe_title = re.sub(r'[\\/*?:",<>|]', "", result_item['title'])
                ext = result_item.get('extension', 'pdf').replace('.', '')
                filename = f"{safe_title}.{ext}"
            
            # 4. Save file
            download_dir = Path(self.config_manager.get('online_search.download_path', 'downloads'))
            download_dir.mkdir(exist_ok=True)
            
            save_path = download_dir / filename
            total_size = int(dl_response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(save_path, 'wb') as f:
                for chunk in dl_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if progress_callback and total_size > 0:
                            progress_callback(downloaded_size, total_size)
                            
            return str(save_path.absolute())
            
        except CloudflareError as e:
            print(f"Cloudflare/Browser required for: {e}")
            raise e # Propagate to GUI
        except Exception as e:
            print(f"Download failed: {e}")
            return None

    def get_book_category(self, url: str, source: str) -> str:
        """
        Fetch the book's detail page and extract category/topic.
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            category = "Unknown"
            
            if source == "Z-Library":
                # Z-Library usually has <div class="bookProperty property_categories"> ... </div>
                cat_div = soup.find('div', class_='property_categories')
                if cat_div:
                    links = cat_div.find_all('a')
                    if links:
                        category = " > ".join([a.get_text(strip=True) for a in links])
                    else:
                        category = cat_div.get_text(strip=True).replace("Categories:", "").strip()
                
                if category == "Unknown":
                    # Method 2: Look for text "Categories:"
                    for tag in soup.find_all(string=re.compile("Categories:")):
                        if tag.parent:
                            txt = tag.parent.get_text(strip=True).replace("Categories:", "").strip()
                            if txt:
                                category = txt
                                break

            else: # Anna's Archive
                # Look for "Topic" or "Subject" or "Decimal Class"
                # Anna's detail pages are variable, often just big text dumps or tables
                for keyword in ["Topic", "Subject", "YCC", "DDC", "LCC"]:
                    tag = soup.find(string=re.compile(f"{keyword}:"))
                    if tag and tag.parent:
                        # Usually "Topic: Science"
                        full = tag.parent.get_text(strip=True)
                        candidate = full.split(":")[-1].strip()
                        if candidate:
                            category = candidate
                            break
                            
            return category if category else "Unknown"
            
        except Exception as e:
            print(f"Failed to get category from {url}: {e}")
            return "Unknown"

if __name__ == "__main__":
    pass
