from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import time
import re
from keep_alive import start_keep_alive

app = Flask(__name__)
CORS(app)

TEMP_DIR = os.path.join(tempfile.gettempdir(), 'xdownloader_files')
os.makedirs(TEMP_DIR, exist_ok=True)

@app.route('/api/download', methods=['POST'])
def download_media():
    data = request.get_json()
    url = data.get('url')
    download_option = data.get('format', 'mp4_hd')

    if not url:
        return jsonify({"status": "error", "message": "Missing URL"}), 400

    timestamp = int(time.time())
    base_output = os.path.join(TEMP_DIR, f"output_{timestamp}.%(ext)s")

    ydl_opts = {
        'outtmpl': base_output,
        'noplaylist': True,
        'quiet': True,
        'nocheckcertificate': True,
        'postprocessors': [],
    }

    # FORMAT SELECTION
    if download_option == "mp3":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    elif download_option in ["video_hd", "mp4_hd", "best"]:
        ydl_opts['format'] = 'best'
    
    elif download_option == "slides":
        ydl_opts['format'] = 'best'
        ydl_opts['outtmpl'] = os.path.join(TEMP_DIR, f"slides_{timestamp}_%(title)s_%(id)s.%(ext)s")

    else:
        ydl_opts['format'] = 'best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "download")

            # Find output file
            files = os.listdir(TEMP_DIR)
            matches = [f for f in files if str(timestamp) in f]

            if not matches:
                raise Exception("No file downloaded")

            file_path = os.path.join(TEMP_DIR, matches[0])
            download_name = matches[0]

            return send_file(
                file_path,
                as_attachment=True,
                download_name=download_name
            )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        # Clean up
        if "file_path" in locals() and os.path.exists(file_path):
            os.remove(file_path)


@app.route("/health")
def health():
    return {"status": "ok", "msg": "Running ❤️"}, 200


if __name__ == "__main__":
    start_keep_alive()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
