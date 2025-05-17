from flask import Flask, request, redirect, session, url_for, render_template_string, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import json, os, yt_dlp, glob, time, random, subprocess

from colorama import init, Fore, Style
import pyfiglet

init(autoreset=True)

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False

USERS_FILE = 'users.json'
VIDEO_FOLDER = 'videos'
os.makedirs(VIDEO_FOLDER, exist_ok=True)

COLORS = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.WHITE]

def print_colored(text):
    print(random.choice(COLORS) + text + Style.RESET_ALL)

# -- Def 1: TikTok Video Downloader --
def download_tiktok_video(url):
    output_path = os.path.join(VIDEO_FOLDER, '%(id)s.%(ext)s')
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': output_path,
        'quiet': True,
        'nocheckcertificate': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return info['id'] + '.mp4'

# -- Def 2: Open Facebook Contact --
def contact():
    subprocess.run(["xdg-open", "https://www.facebook.com/md.shaharia.1675275"])

def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def cleanup_old_videos(folder=VIDEO_FOLDER, max_age_seconds=3600):
    now = time.time()
    for filepath in glob.glob(os.path.join(folder, '*')):
        if os.path.isfile(filepath) and now - os.path.getmtime(filepath) > max_age_seconds:
            try:
                os.remove(filepath)
                print_colored(f"Deleted old video: {filepath}")
            except Exception as e:
                print_colored(f"Error deleting {filepath}: {e}")

@app.route('/')
def home():
    return redirect(url_for('dashboard') if 'user' in session else url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        number = request.form['number']
        password = request.form['password']
        users = load_users()
        if number in users:
            return "Account already exists. Go to login."
        users[number] = generate_password_hash(password)
        save_users(users)
        return redirect(url_for('login'))
    return render_template_string(REGISTER_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        number = request.form['number']
        password = request.form['password']
        users = load_users()
        if number in users and check_password_hash(users[number], password):
            session['user'] = number
            return redirect(url_for('dashboard'))
        return "Invalid login."
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    cleanup_old_videos()
    video_file = None
    error = None

    if request.method == 'POST':
        tiktok_url = request.form['video_url']
        try:
            video_file = download_tiktok_video(tiktok_url)
        except Exception as e:
            error = f"Error downloading video: {e}"

    return render_template_string(DASHBOARD_HTML, video_file=video_file, error=error)

@app.route('/videos/<filename>')
def serve_video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)

# HTML with blinking logo and OWNER SHAHARIA
LOGO_HTML = '''
<style>
@keyframes blinkColor {
  0%   { color: #FF0050; }
  25%  { color: #25F4EE; }
  50%  { color: #000000; }
  75%  { color: #00FF00; }
  100% { color: #FF0050; }
}
.blinking-logo {
  font-family: sans-serif;
  font-size: 32px;
  font-weight: bold;
  animation: blinkColor 1s infinite;
}
.blink-word {
  display: inline-block;
  animation: blinkColor 2s infinite;
  margin: 0 4px;
  font-size: 20px;
}
</style>

<h1 class="blinking-logo">
  <img src="https://upload.wikimedia.org/wikipedia/commons/a/a9/TikTok_logo.svg" height="40" style="vertical-align:middle;">
  TIKTOK DWLD
</h1>
<div style="text-align:center; margin-bottom: 10px;">
  <span class="blink-word">OWNER</span>
  <span class="blink-word">SHAHARIA</span>
</div>
'''

REGISTER_HTML = LOGO_HTML + '''
<h2>Register</h2>
<form method="POST">
    Phone Number: <input name="number"><br><br>
    Password: <input name="password" type="password"><br><br>
    <button type="submit">Register</button>
</form>
<br><a href="/login">Already have an account? Login</a>
'''

LOGIN_HTML = LOGO_HTML + '''
<h2>Login</h2>
<form method="POST">
    Phone Number: <input name="number"><br><br>
    Password: <input name="password" type="password"><br><br>
    <button type="submit">Login</button>
</form>
<br><a href="/register">Don't have an account? Register</a>
'''

DASHBOARD_HTML = LOGO_HTML + '''
<h2>Welcome, {{ session['user'] }}</h2>
<form method="POST">
    <label>Paste TikTok Video URL:</label><br>
    <input name="video_url" style="width: 400px;" required><br><br>
    <button type="submit">Download & Play</button>
</form>
{% if error %}
<p style="color:red;">{{ error }}</p>
{% endif %}
{% if video_file %}
    <h3>Downloaded Video</h3>
    <video width="720" controls autoplay>
        <source src="/videos/{{ video_file }}" type="video/mp4">
        Your browser does not support the video tag.
    </video>
{% endif %}
<br><a href="/logout">Logout</a>
'''

# -- Main Execution --
def main():
    banner = pyfiglet.figlet_format("TIKTOK DWLD")
    print_colored(banner)
    print_colored("Web app starting...")
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()