from flask import Flask, request, jsonify, send_from_directory
import yt_dlp
import os
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)

# Directory to store downloaded MP3 files and cookies
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
COOKIES_FILE = os.path.join('cookies.txt')
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
    'cookiefile': "cookies.txt"
}

def get_video_id(url):
    """Extract the video ID from a YouTube URL."""
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path.lstrip('/')
    if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        query = parse_qs(parsed_url.query)
        return query.get('v', [None])[0]
    return None

def download_audio(youtube_url):
    """Download audio and return the download URL or None if failed."""
    try:
        video_id = get_video_id(youtube_url)
        if not video_id:
            return None

        mp3_file = os.path.join(STATIC_DIR, f"{video_id}.mp3")
        if os.path.exists(mp3_file):
            return f"{request.host_url}static/{video_id}.mp3"

        ydl_opts = YDL_OPTIONS.copy()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        if os.path.exists(mp3_file):
            return f"{request.host_url}static/{video_id}.mp3"
        return None
    except Exception:
        return None

@app.route('/download', methods=['POST'])
def download_single_audio():
    """Download audio from a single YouTube URL provided in JSON."""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'Missing URL in request body'}), 400

        youtube_url = data['url']
        download_url = download_audio(youtube_url)
        if download_url:
            return jsonify({'videoUrl': download_url})
        return jsonify({'error': 'Failed to download audio'}), 500
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload a text file with YouTube URLs and return download links."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in request'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        urls = file.read().decode('utf-8').splitlines()
        results = []
        for url in urls:
            url = url.strip()
            if url:
                download_url = download_audio(url)
                if download_url:
                    results.append({'url': url, 'videoUrl': download_url})
                else:
                    results.append({'url': url, 'error': 'Failed to download'})
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/upload-cookies', methods=['POST'])
def upload_cookies():
    """Upload a cookies.txt file to the server."""
    try:
        if 'cookies' not in request.files:
            return jsonify({'error': 'No cookies file part in request'}), 400

        cookies_file = request.files['cookies']
        if cookies_file.filename == '':
            return jsonify({'error': 'No cookies file selected'}), 400

        cookies_file.save(COOKIES_FILE)
        return jsonify({'message': f'Cookies file saved to {COOKIES_FILE}'})
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
    app.run(host='0.0.0.0', port=5000)
