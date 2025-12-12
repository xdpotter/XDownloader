from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import time
from keep_alive import start_keep_alive

app = Flask(__name__)
CORS(app)

# Temporary directory for downloads
TEMP_DIR = os.path.join(tempfile.gettempdir(), "xdownloader_files")
os.makedirs(TEMP_DIR, exist_ok=True)


@app.route("/api/download", methods=["POST"])
def download_media():
    data = request.get_json()
    url = data.get("url")
    download_option = data.get("format", "mp4_hd")

    if not url:
        return jsonify({"status": "error", "message": "Missing URL parameter"}), 400

    timestamp = int(time.time())
    output_template = os.path.join(TEMP_DIR, f"media_{timestamp}.%(ext)s")

    # ------------------ yt-dlp options ------------------
    ydl_opts = {
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "nocheckcertificate": True,
        "postprocessors": []
    }

    # ---------------- FORMAT SELECTION ------------------
    if download_option == "mp3":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]

    elif download_option in ["video_hd", "mp4_hd", "best", "video_best"]:
        ydl_opts["format"] = "bestvideo+bestaudio/best"

    elif download_option in ["slides", "photo_best"]:
        ydl_opts["format"] = "best"

    else:
        ydl_opts["format"] = "best"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Download and get info
            info = ydl.extract_info(url, download=True)

            # Get correct filename
            final_path = ydl.prepare_filename(info)

            # If mp3, fix extension
            if download_option == "mp3":
                final_path = final_path.rsplit(".", 1)[0] + ".mp3"

            if not os.path.exists(final_path):
                raise Exception("Download failed: file not found.")

            # Clean download name for user
            download_name = os.path.basename(final_path)

            return send_file(
                final_path,
                as_attachment=True,
                download_name=download_name,
            )

    except Exception as e:
        print("Download Error:", e)
        return jsonify({
            "status": "error",
            "message": f"Could not download media: {str(e)}"
        }), 500

    finally:
        # Cleanup downloaded files
        try:
            if "final_path" in locals() and os.path.exists(final_path):
                os.remove(final_path)
        except:
            pass


@app.route("/health")
def health():
    return {"status": "ok", "msg": "Backend running ❤️"}, 200


if __name__ == "__main__":
    start_keep_alive()
    app.run(host="0.0.0.0", port=5000)
