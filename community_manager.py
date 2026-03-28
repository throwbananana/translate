#! python
# -*- coding: utf-8 -*-
import json
import os
import time
import hashlib
import requests
from pathlib import Path
from cloud_upload import CloudUploader

class CommunityManager:
    """
    Manages the Community Library with enhanced security and deduping.
    """
    
    def __init__(self, data_dir="server_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.library_file = self.data_dir / "library.json" # Local cache of public books
        self._init_db()

    def _init_db(self):
        if not self.library_file.exists():
            # Initial sample data
            sample_data = [
                {
                    "id": "1",
                    "title": "使用指南 (User Guide)",
                    "author": "Developer",
                    "description": "Book Translator 官方使用指南",
                    "url": "https://files.catbox.moe/sample.pdf", 
                    "uploader": "Admin",
                    "date": "2025-01-01",
                    "size": "1.2MB",
                    "md5": "00000000000000000000000000000000",
                    "downloads": 1024,
                    "status": "approved"
                }
            ]
            self._save_json(self.library_file, sample_data)

    def _load_json(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def _save_json(self, path, data):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def calculate_md5(self, file_path):
        """Calculate MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def sync_from_remote(self):
        """
        [PLACEHOLDER] Sync library list from a remote server/gist.
        Currently just returns local data, but structure is ready for API integration.
        """
        # Example implementation for real server:
        # try:
        #     resp = requests.get("https://api.myserver.com/library.json")
        #     if resp.status_code == 200:
        #         remote_data = resp.json()
        #         self._save_json(self.library_file, remote_data)
        # except Exception as e:
        #     print(f"Sync failed: {e}")
        pass

    def get_public_books(self):
        """Get list of public books (Auto-syncs first)"""
        self.sync_from_remote()
        return self._load_json(self.library_file)

    def submit_book(self, file_path, title, author, description, uploader_name):
        """
        1. Check MD5 to avoid re-uploading duplicate files
        2. Upload file to Cloud (Catbox) if new
        3. Save record (Auto-approved)
        """
        # 0. Calculate MD5
        file_md5 = self.calculate_md5(file_path)
        file_size = os.path.getsize(file_path)
        size_str = f"{file_size / 1024 / 1024:.2f} MB"
        
        library = self.get_public_books()
        
        # 1. Check for duplicates
        existing_url = None
        for book in library:
            if book.get('md5') == file_md5:
                existing_url = book['url']
                print(f"File exists! Reusing URL: {existing_url}")
                break
        
        # 2. Upload if needed
        if existing_url:
            file_url = existing_url
        else:
            try:
                file_url = CloudUploader.upload_to_catbox(file_path)
            except Exception as e:
                raise Exception(f"Cloud upload failed: {str(e)}")

        # 3. Create Record
        # Check if exactly same record exists (Same title + MD5) to prevent spam
        for book in library:
            if book.get('md5') == file_md5 and book.get('title') == title:
                raise Exception("This book is already in the library!")

        record = {
            "id": str(int(time.time() * 1000)),
            "title": title,
            "author": author,
            "description": description,
            "url": file_url,
            "uploader": uploader_name,
            "date": time.strftime("%Y-%m-%d"),
            "size": size_str,
            "md5": file_md5,
            "downloads": 0,
            "status": "approved"
        }

        # 4. Add to Library
        library.insert(0, record)
        self._save_json(self.library_file, library)
        
        # 5. Push update to remote (Placeholder)
        # requests.post("https://api.myserver.com/library/update", json=record)
        
        return True

    def delete_book(self, book_id):
        """Delete book from library"""
        library = self.get_public_books()
        new_library = [b for b in library if str(b['id']) != str(book_id)]
        
        if len(new_library) != len(library):
            self._save_json(self.library_file, new_library)
            return True
        return False

    def check_link_health(self, url):
        """Check if a link is still valid (HEAD request)"""
        try:
            resp = requests.head(url, timeout=5)
            return resp.status_code == 200
        except:
            return False
