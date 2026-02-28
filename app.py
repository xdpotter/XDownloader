from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import uuid
from keep_alive import start_keep_alive

app = Flask(__name__)
CORS(app)

# Render allows writing only to the /tmp folder
TEMP_DIR = "/tmp"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.route("/api/download", methods=["POST"])
def download_media():
    data = request.json
    url = data.get("url")
    download_option = data.get("format", "mp4")

    if not url:
        return jsonify({"status": "error", "message": "Missing URL"}), 400

    # Create a unique filename to prevent overwriting other users' downloads
    file_id = str(uuid.uuid4())
    output_template = os.path.join(TEMP_DIR, f"{file_id}.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "cookiefile": "cookies.txt",  # Matches the file name in your directory
        "noplaylist": True,
        "quiet": True,
        "nocheckcertificate": True,
        # Common User-Agent to avoid being flagged as a bot
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    }

    if download_option == "mp3":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    else:
        # Attempts to get the best MP4 quality available
        ydl_opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        ydl_opts["merge_output_format"] = "mp4"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        # Fix extension if post-processing changed it to mp3
        if download_option == "mp3":
            file_path = os.path.splitext(file_path)[0] + ".mp3"

        if not os.path.exists(file_path):
            return jsonify({"status": "error", "message": "File creation failed"}), 500

        # Send the file to the user's browser
        response = send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path)
        )

        # Delete the file from the server after it is sent to keep the server clean
        @response.call_on_close
        def cleanup():
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Cleanup error: {e}")

        return response

    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/health")
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    start_keep_alive()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
