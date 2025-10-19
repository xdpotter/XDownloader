# app.py

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import time
import re

app = Flask(__name__)
CORS(app) # Enable CORS for frontend communication

# Define a temporary directory for processed files
TEMP_DIR = os.path.join(tempfile.gettempdir(), 'xdownloader_files')
os.makedirs(TEMP_DIR, exist_ok=True)

@app.route('/api/download', methods=['POST'])
def download_media():
    data = request.get_json()
    url = data.get('url')
    download_option = data.get('format', 'mp4_hd') # Default to high quality video
    
    if not url:
        return jsonify({"status": "error", "message": "Missing URL parameter."}), 400

    # Sanitize URL to prevent directory traversal issues
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Define temporary output path for the file
    timestamp = int(time.time())
    output_filename_template = os.path.join(TEMP_DIR, f'media_file_{timestamp}.%(ext)s')
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]', # Default format (best quality mp4)
        'outtmpl': output_filename_template,
        'noplaylist': True,
        'verbose': False,
        'quiet': True,
        'noprogress': True,
        'max_filesize': 1024 * 1024 * 500, # Max file size 500MB
    }

    # --- Logic to select format based on download_option ---
    if download_option == 'mp3':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
        ydl_opts['outtmpl'] = os.path.join(TEMP_DIR, f'audio_file_{timestamp}.%(ext)s')

    elif download_option in ['slides', 'photo_best']:
        # For platforms like Instagram/Pinterest (best image) or TikTok Slideshows
        ydl_opts['format'] = 'best' # yt-dlp automatically handles static images/slideshows with 'best'
        ydl_opts['outtmpl'] = os.path.join(TEMP_DIR, f'image_file_{timestamp}.%(title)s.%(ext)s')

    elif download_option in ['video_best', 'hd', 'best_mp4']:
        # High quality video (default setting)
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]'

    # --- Download Process ---
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            
            # Get the path to the downloaded file(s)
            downloaded_files = ydl.download_retcode.get('files', [])
            
            if not downloaded_files:
                # Fallback path finding for single file download
                filename_pattern = re.escape(os.path.join(TEMP_DIR, f'media_file_{timestamp}'))
                matching_files = [f for f in os.listdir(TEMP_DIR) if re.match(r'{}\..*'.format(filename_pattern), os.path.join(TEMP_DIR, f))]
                if not matching_files:
                    raise Exception("Download failed: No file produced by yt-dlp.")
                file_path = os.path.join(TEMP_DIR, matching_files[0])
                
            else:
                # Handle cases where multiple files (like slideshows) are downloaded
                # For simplicity, we assume single file download for now unless specific logic is added
                file_path = downloaded_files[0]
                
            # Get original file name for user download
            base_name = info_dict.get('title', 'download_media')
            if download_option == 'mp3':
                base_name = f"{base_name}.mp3"
            else:
                base_name = f"{base_name}.mp4"

            # --- Serve File and Cleanup ---
            return send_file(
                file_path, 
                as_attachment=True, 
                download_name=base_name,
                mimetype='application/octet-stream'
            )

    except Exception as e:
        print(f"Download Error: {e}")
        return jsonify({"status": "error", "message": f"Could not process or download media. Error: {str(e)}"}), 500
    finally:
        # Crucial: Clean up the temporary file(s) after serving
        if 'file_path' in locals() and os.path.exists(file_path):
             os.remove(file_path)
             print(f"Cleaned up file: {file_path}")
        # Add cleanup logic for multi-file downloads (e.g., slideshows) if implemented

# Initial route for health check
@app.route('/health')
def health_check():
    return jsonify({"status": "ok", "message": "XDownloader Backend is running with love 💖"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)