#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import os
import json

class CloudUploader:
    """Handles uploading files to cloud sharing services"""
    
    @staticmethod
    def upload_to_catbox(file_path):
        """
        Uploads a file to Catbox.moe
        Returns the URL if successful, raises Exception otherwise.
        """
        url = "https://catbox.moe/user/api.php"
        
        try:
            with open(file_path, 'rb') as f:
                files = {'fileToUpload': f}
                data = {'reqtype': 'fileupload'}
                # Catbox allows up to 200MB. Timeout increased for slower connections.
                response = requests.post(url, data=data, files=files, timeout=600)
                
            if response.status_code == 200:
                # Catbox returns the URL directly in the body
                return response.text.strip()
            else:
                raise Exception(f"Upload failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            raise Exception(f"Upload error: {str(e)}")

    @staticmethod
    def upload_to_fileio(file_path, expires="2w"):
        """
        Uploads to file.io (Ephemeral, good for quick one-time sharing)
        expires: 1d, 1w, 2w, 1m, 1y (Defaults to 2 weeks)
        """
        url = "https://file.io/"
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {'expires': expires}
                response = requests.post(url, files=files, data=data, timeout=600)
                
            if response.status_code == 200:
                return response.json().get('link')
            else:
                raise Exception(f"File.io upload failed: {response.text}")
        except Exception as e:
            raise Exception(f"Upload error: {str(e)}")

    @staticmethod
    def upload_to_litterbox(file_path, time='72h'):
        """
        Uploads to Litterbox (Temporary Catbox)
        time: 1h, 12h, 24h, 72h
        """
        url = "https://litterbox.catbox.moe/resources/internals/api.php"
        try:
            with open(file_path, 'rb') as f:
                files = {'fileToUpload': f}
                data = {'reqtype': 'fileupload', 'time': time}
                response = requests.post(url, data=data, files=files, timeout=600)
            
            if response.status_code == 200:
                return response.text.strip()
            else:
                raise Exception(f"Upload failed: {response.text}")
        except Exception as e:
            raise Exception(f"Upload error: {str(e)}")
