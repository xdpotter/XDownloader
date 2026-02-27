from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import uuid
from keep_alive import start_keep_alive

app = Flask(__name__)
CORS(app)

# Render safe temp folder
TEMP_DIR = "/tmp"
os.makedirs(TEMP_DIR, exist_ok=True)


# ===============================
# DOWNLOAD API
# ===============================
@app.route("/api/download", methods=["POST"])
def download_media():
    data = request.json
    url = data.get("url")
    download_option = data.get("format", "mp4_hd")

    if not url:
        return jsonify({"status": "error", "message": "Missing URL"}), 400

    # unique filename (no searching needed)
    file_id = str(uuid.uuid4())
    output_path = os.path.join(TEMP_DIR, f"{file_id}.%(ext)s")

    ydl_opts = {
        "outtmpl": output_path,
        "format": "best",
        "noplaylist": True,
        "quiet": True,
        "nocheckcertificate": True,
        "merge_output_format": "mp4"
    }

    # MP3 option
    if download_option == "mp3":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # get exact downloaded file
            file_path = ydl.prepare_filename(info)

        # if mp3 postprocess changed extension
        if download_option == "mp3":
            file_path = file_path.replace(".webm", ".mp3").replace(".m4a", ".mp3")

        if not os.path.exists(file_path):
            return jsonify({"status": "error", "message": "File not created"}), 500

        response = send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path)
        )

        # delete AFTER sending
        @response.call_on_close
        def cleanup():
            try:
                os.remove(file_path)
            except:
                pass

        return response

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ===============================
# HEALTH CHECK
# ===============================
@app.route("/health")
def health():
    return {"status": "ok", "msg": "Running ❤️"}, 200


# ===============================
# START SERVER
# ===============================
if __name__ == "__main__":
    start_keep_alive()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
