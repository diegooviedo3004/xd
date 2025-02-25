from flask import Flask, request, render_template, jsonify
import os
import subprocess

app = Flask(__name__)

# Directory to store cookies and downloaded files
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    # Get URL and cookies file from the form
    video_url = request.form.get('url')
    cookies_file = request.files.get('cookies')

    if not video_url or not cookies_file:
        return jsonify({'error': 'URL and cookies file are required'}), 400

    # Save cookies file to the downloads directory
    cookies_path = os.path.join(DOWNLOAD_DIR, 'cookies.txt')
    cookies_file.save(cookies_path)

    try:
        # Run yt-dlp with the cookies file
        command = [
            'yt-dlp',
            '--cookies', cookies_path,
            '-o', os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            video_url
        ]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            return jsonify({'message': 'Download successful', 'output': result.stdout})
        else:
            return jsonify({'error': 'Download failed', 'details': result.stderr}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
