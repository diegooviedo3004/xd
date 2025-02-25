from flask import Flask, request, jsonify, send_from_directory
import yt_dlp
import os
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)

# Directory to store downloaded MP3 files
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
os.makedirs(STATIC_DIR, exist_ok=True)

# yt-dlp configuration for downloading MP3 files
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': os.path.join(STATIC_DIR, '%(id)s.%(ext)s'),
    'quiet': True,
}

def get_video_id(url):
    """
    Extract the video ID from a YouTube URL.
    Supports both youtube.com and youtu.be formats.
    """
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path.lstrip('/')
    if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        query = parse_qs(parsed_url.query)
        return query.get('v', [None])[0]
    return None

@app.route('/download', methods=['POST'])
def download_audio():
    """
    Endpoint to download audio from a YouTube URL.
    Expects a JSON body with a 'url' field.
    Returns a JSON response with the download URL for the MP3 file.
    """
    try:
        # Parse request data
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'Missing URL in request body'}), 400

        youtube_url = data['url']
        video_id = get_video_id(youtube_url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL'}), 400

        # Check if the MP3 file already exists
        mp3_file = os.path.join(STATIC_DIR, f"{video_id}.mp3")
        if os.path.exists(mp3_file):
            download_url = f"{request.host_url}static/{video_id}.mp3"
            return jsonify({'videoUrl': download_url})

        # Download the audio using yt-dlp
        ydl_opts = YDL_OPTIONS.copy()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        # Verify download and serve the file
        if os.path.exists(mp3_file):
            download_url = f"{request.host_url}static/{video_id}.mp3"
            return jsonify({'videoUrl': download_url})
        else:
            return jsonify({'error': 'Failed to download audio'}), 500

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve MP3 files from the static directory."""
    try:
        return send_from_directory(STATIC_DIR, filename)
    except Exception:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    # For local testing only; Docker uses Gunicorn
    app.run(host='0.0.0.0', port=5000)
