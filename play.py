import os, socket, cv2
from flask import Flask, render_template_string, send_from_directory, url_for

app = Flask(__name__)

# Directory setup for thumbnails
THUMB_DIR = "thumbnails"
if not os.path.exists(THUMB_DIR):
    os.makedirs(THUMB_DIR)

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def generate_thumbnail(video_path, thumb_path):
    """Uses OpenCV to grab a frame for the preview."""
    if not os.path.exists(thumb_path):
        cap = cv2.VideoCapture(video_path)
        success, frame = cap.read()
        if success:
            # Resize for faster loading
            frame = cv2.resize(frame, (320, 180))
            cv2.imwrite(thumb_path, frame)
        cap.release()

# Updated UI with Gestures, LocalStorage (Resume), and PiP
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>py frames</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Poppins:wght@300;600&display=swap" rel="stylesheet">
    <style>
        :root { 
            --primary: #ff4b2b; 
            --secondary: #ff416c;
            --bg: #050510; 
            --card-bg: rgba(255, 255, 255, 0.03);
            --glass: rgba(255, 255, 255, 0.1); 
        }
        
        body { 
            font-family: 'Poppins', sans-serif; background: var(--bg); color: white; 
            margin: 0; padding: 20px; overflow-x: hidden;
            background-image: radial-gradient(circle at 50% -20%, #2a1b3d 0%, #050510 80%);
        }

        .container { max-width: 1200px; margin: auto; }
        
        h1 { 
            font-family: 'Orbitron', sans-serif; 
            background: linear-gradient(90deg, #ff416c, #ff4b2b); 
            -webkit-background-clip: text; 
            -webkit-text-fill-color: transparent; 
            letter-spacing: 5px;
            text-shadow: 0 10px 20px rgba(255, 75, 43, 0.3);
            margin-bottom: 5px;
        }

        .ip-banner {
            font-size: 0.9rem;
            color: #888;
            margin-bottom: 30px;
            border-left: 3px solid var(--primary);
            padding-left: 15px;
        }

        /* Video Player Styling */
        .video-container { 
            position: relative; border-radius: 24px; overflow: hidden; 
            box-shadow: 0 0 50px rgba(0,0,0,0.9), 0 0 20px rgba(255, 75, 43, 0.2);
            border: 1px solid rgba(255,255,255,0.1);
        }
        video { width: 100%; display: block; background: black; }

        /* Modern Grid Layout */
        .movie-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); 
            gap: 30px; 
            padding: 20px 0; 
        }

        /* Enhanced Interactive Cards */
        .card { 
            position: relative;
            background: var(--card-bg); 
            border-radius: 20px; 
            overflow: hidden; 
            cursor: pointer; 
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
            border: 1px solid rgba(255,255,255,0.08);
            backdrop-filter: blur(12px);
        }

        .card:hover { 
            transform: translateY(-10px) scale(1.02); 
            border-color: var(--primary);
            box-shadow: 0 15px 30px rgba(255, 75, 43, 0.2);
        }

        .thumb-wrapper {
            position: relative;
            width: 100%;
            height: 160px;
            overflow: hidden;
        }

        .thumb { 
            width: 100%; height: 100%; object-fit: cover; 
            transition: 0.5s;
        }

        .card:hover .thumb { transform: scale(1.1); }

        /* Play Icon Overlay */
        .play-overlay {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(255, 75, 43, 0.2);
            display: flex; align-items: center; justify-content: center;
            opacity: 0; transition: 0.3s;
        }
        .card:hover .play-overlay { opacity: 1; }

        .card-info { 
            padding: 18px; 
            background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);
        }

        .movie-title {
            font-size: 0.95rem; font-weight: 600; margin: 0;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
            color: #eee;
        }
        
        .badge { 
            background: linear-gradient(45deg, var(--secondary), var(--primary)); 
            padding: 4px 10px; border-radius: 8px; font-size: 0.65rem; 
            margin-bottom: 8px; display: inline-block; text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Scrollbar Styling */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg); }
        ::-webkit-scrollbar-thumb { background: #333; border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--primary); }

    </style>
</head>
<body>
    <div class="container">
        <h1>PY FRAMES</h1>
        <div class="ip-banner">📡 Streaming live at <b>{{ ip }}:5000</b></div>
        
        {% if play_file %}
            <a href="/" style="color:#aaa; text-decoration:none; display:inline-block; margin-bottom:15px;">← Back to Main</a>
            <h3 id="title" style="margin-bottom:20px;">Now Playing: <span style="color:var(--primary)">{{ play_file }}</span></h3>
            <div class="video-container">
                <video id="mainPlayer" controls playsinline>
                    <source src="/video_raw/{{ play_file }}" type="video/mp4">
                </video>
            </div>
            <script>
                const video = document.getElementById('mainPlayer');
                const storageKey = "resume_{{ play_file }}";
                video.addEventListener('loadedmetadata', () => {
                    const savedTime = localStorage.getItem(storageKey);
                    if (savedTime) video.currentTime = savedTime;
                });
                video.addEventListener('timeupdate', () => {
                    localStorage.setItem(storageKey, video.currentTime);
                });
                video.addEventListener('dblclick', () => {
                    if (document.pictureInPictureElement) document.exitPictureInPicture();
                    else video.requestPictureInPicture();
                });
            </script>
        {% else %}
            <div class="movie-grid">
                {% for movie in movies %}
                <div class="card" onclick="window.location.href='/watch/{{ movie }}'">
                    <div class="thumb-wrapper">
                        <img class="thumb" src="/thumb/{{ movie }}.jpg" onerror="this.src='https://placehold.co/320x180/111/white?text=No+Preview'">
                        <div class="play-overlay">
                            <svg width="50" height="50" viewBox="0 0 24 24" fill="white"><path d="M8 5v14l11-7z"/></svg>
                        </div>
                    </div>
                    <div class="card-info">
                        <span class="badge">4K Ultra HD</span>
                        <p class="movie-title">{{ movie }}</p>
                    </div>
                </div>
                {% endfor %}
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    # 1. Get list of current video files
    video_files = [f for f in os.listdir('.') if f.endswith(('.mp4', '.mkv', '.webm'))]
    
    # 2. Get list of existing thumbnails
    thumb_files = os.listdir(THUMB_DIR)
    
    # 3. WIPE DATA: Remove thumbnails that don't have a matching video
    # Since thumbnails are named "filename.ext.jpg", we check if "filename.ext" exists
    for thumb in thumb_files:
        original_video_name = thumb.replace('.jpg', '')
        if original_video_name not in video_files:
            try:
                os.remove(os.path.join(THUMB_DIR, thumb))
                print(f"🗑️ Cleaned up old thumbnail: {thumb}")
            except Exception as e:
                print(f"Error deleting {thumb}: {e}")

    # 4. Generate new thumbnails for current videos
    for f in video_files:
        generate_thumbnail(f, os.path.join(THUMB_DIR, f + ".jpg"))
        
    return render_template_string(HTML_TEMPLATE, movies=video_files, ip=get_ip(), play_file=None)

@app.route('/watch/<filename>')
def watch(filename):
    return render_template_string(HTML_TEMPLATE, movies=[], ip=get_ip(), play_file=filename)

@app.route('/video_raw/<filename>')
def video_raw(filename):
    return send_from_directory(os.getcwd(), filename)

@app.route('/thumb/<filename>')
def get_thumb(filename):
    return send_from_directory(THUMB_DIR, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)