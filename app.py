from flask import Flask, render_template, request, send_file
from pytubefix import YouTube
import os
import shutil
import subprocess
import re

app = Flask(__name__)

# Folder untuk menyimpan file sementara
DOWNLOAD_FOLDER = 'downloads'

# Pastikan folder download ada
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form['video_url']
        quality = request.form['quality']
        
        # Hapus isi folder download sebelum mendownload video baru
        for file in os.listdir(DOWNLOAD_FOLDER):
            file_path = os.path.join(DOWNLOAD_FOLDER, file)
            os.remove(file_path)

        try:
            yt = YouTube(video_url)

            # Mencetak semua stream yang tersedia untuk debugging
            print("Stream yang tersedia:")
            for stream in yt.streams:
                print(f"Resolusi: {stream.resolution}, Type: {stream.type}, Progressive: {stream.is_progressive}")

            # Inisialisasi variabel untuk stream video dan audio
            video_stream = None
            audio_stream = None

            # Logika pemilihan stream
            if quality == 'highest':
                video_stream = yt.streams.filter(progressive=False).order_by('resolution').desc().first()
            else:
                video_stream = yt.streams.filter(resolution=quality, progressive=False).first()
                if not video_stream:
                    video_stream = yt.streams.filter(progressive=True).order_by('bitrate').desc().first()

            audio_stream = yt.streams.filter(only_audio=True).order_by('bitrate').desc().first()

            if not video_stream or not audio_stream:
                return "Tidak ada stream yang tersedia untuk kualitas yang dipilih."

            video_path = video_stream.download(output_path=DOWNLOAD_FOLDER)
            audio_path = audio_stream.download(output_path=DOWNLOAD_FOLDER)

            final_video_title = re.sub(r'[<>:"/\\|?*]', '', yt.title)
            video_quality = video_stream.resolution if video_stream.resolution else "unknown"
            final_video_path = os.path.join(DOWNLOAD_FOLDER, f"{final_video_title} - {video_quality}.mp4")
            merge_command = [
                'ffmpeg',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-strict', 'experimental',
                final_video_path
            ]
            subprocess.run(merge_command, check=True)

            os.remove(video_path)
            os.remove(audio_path)

            return send_file(final_video_path, as_attachment=True)

        except Exception as e:
            return f"Terjadi kesalahan saat memproses video: {str(e)}"

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
