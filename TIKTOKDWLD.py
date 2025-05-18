from flask import Flask, request, redirect, session, url_for, render_template_string, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import json, os, yt_dlp, glob, time, random, subprocess, sys, webbrowser
from colorama import init, Fore, Style
import pyfiglet

init(autoreset=True)

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

USERS_FILE = 'users.json'
VIDEO_FOLDER = 'videos'
os.makedirs(VIDEO_FOLDER, exist_ok=True)

COLORS = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.WHITE]

def print_colored(text):
    print(random.choice(COLORS) + text + Style.RESET_ALL)

def download_video(url):
    output_path = os.path.join(VIDEO_FOLDER, '%(id)s.%(ext)s')
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': output_path,
        'quiet': True,
        'nocheckcertificate': True,
        'postprocessors': [],
        'noplaylist': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return info['id'] + '.mp4'

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
        video_url = request.form['video_url']
        try:
            video_file = download_video(video_url)
        except Exception as e:
            error = f"Error downloading video: {e}"

    return render_template_string(DASHBOARD_HTML, video_file=video_file, error=error)

@app.route('/videos/<filename>')
def serve_video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)

ASCII_LOGO = '''
<div id="ascii-logo" style="white-space: pre; font-family: monospace; font-size: 14px;"></div>
<script>
const colors = ["red", "green", "yellow", "blue", "magenta", "cyan", "white"];
const asciiArt = `888888 888888     8888b.   dP"Yb  Yb        dP 88b 88 88      dP"Yb     db    8888b.  
  88     88        8I  Yb dP   Yb  Yb  db  dP  88Yb88 88     dP   Yb   dPYb    8I  Yb 
  88     88        8I  dY Yb   dP   YbdPYbdP   88 Y88 88  .o Yb   dP  dP__Yb   8I  dY 
  88     88       8888Y"   YbodP     YP  YP    88  Y8 88ood8  YbodP  dP""""Yb 8888Y"`;

function renderAscii(color) {
    document.getElementById('ascii-logo').innerHTML = `<span style="color:${color}">${asciiArt}</span>`;
}

let i = 0;
setInterval(() => {
    renderAscii(colors[i % colors.length]);
    i++;
}, 500);
</script>
'''

REGISTER_HTML = ASCII_LOGO + '''
<h2>Register</h2>
<form method="POST">
    Phone Number: <input name="number"><br><br>
    Password: <input name="password" type="password"><br><br>
    <button type="submit">Register</button>
</form>
<br><a href="/login">Already have an account? Login</a>
'''

LOGIN_HTML = ASCII_LOGO + '''
<h2>Login</h2>
<form method="POST">
    Phone Number: <input name="number"><br><br>
    Password: <input name="password" type="password"><br><br>
    <button type="submit">Login</button>
</form>
<br><a href="/register">Don't have an account? Register</a>
'''

DASHBOARD_HTML = ASCII_LOGO + '''
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
<br><a href="https://www.facebook.com/md.shaharia.1675275" target="_blank">Contact Owner</a>
<br><a href="/logout">Logout</a>
'''

def main():
    banner = pyfiglet.figlet_format("TIKTOK DWLD")
    print_colored(banner)

    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port_input = input("Enter port to run on (default 5001): ").strip()
        port = int(port_input) if port_input.isdigit() else 5001

    url = f"http://localhost:{port}/"
    print_colored(f"Starting on {url}")
    try:
        webbrowser.open(url)
    except:
        print_colored("Could not open browser automatically.")

    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()