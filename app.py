from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, abort
import os
import json
import pickle
from scraper.instagram_scraper import InstagramScraper
import queue
from flask import Response


# Store per-user progress queues
progress_queues = {}

app = Flask(__name__)
app.secret_key = os.urandom(24) 


BASE_PATH = 'static/data'
COOKIE_FILE = 'instagram_cookies.pkl'
HISTORY_DIR = 'scrape_history'


# Utilities for per-user history
def get_user_history_file(user):
    os.makedirs(HISTORY_DIR, exist_ok=True)
    return os.path.join(HISTORY_DIR, f"{user}.json")


def load_history(user):
    path = get_user_history_file(user)
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return []


def save_history(user, history):
    path = get_user_history_file(user)
    with open(path, 'w') as f:
        json.dump(history, f)


@app.route('/')
def index():
    # Reuse session if already logged in
    if 'user' in session:
        print("✅ Session found for:", session['user'])
        return redirect(url_for('scrape_page'))

    # Fallback: try extracting from existing cookies
    if os.path.exists(COOKIE_FILE):
        try:
            with open(COOKIE_FILE, "rb") as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    if cookie.get("name") == "ds_user":
                        session['user'] = cookie.get("value")
                        print("✅ Recovered user from cookie:", session['user'])
                        break
        except Exception as e:
            print(f"❌ Error loading cookies: {e}")
            session['user'] = None
            os.remove(COOKIE_FILE)

        if 'user' in session and session['user']:
            return redirect(url_for('scrape_page'))

    # Default: show login page
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    print("🚀 Starting Instagram login...")

    def log(msg):
        print(f"[LOGIN] {msg}")

    scraper = InstagramScraper('', os.path.join(BASE_PATH, "tmp_login"), logger=log)
    actual_username = scraper.launch_browser_for_login()

    if actual_username:
        session['user'] = actual_username
        print("✅ Logged in as:", session['user'])
        return redirect(url_for('scrape_page'))

    print("❌ Login failed: no username detected.")
    return redirect(url_for('index'))





@app.route('/scrape_page')
def scrape_page():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template('scrape.html')


@app.route('/start_scrape', methods=['POST'])
def start_scrape():
    if 'user' not in session:
        return "Unauthorized", 403

    user = session['user']
    progress_queues[user] = queue.Queue()
    return "Ready", 200

@app.route('/run_scrape', methods=['POST'])
def run_scrape():
    if 'user' not in session:
        return redirect(url_for('index'))

    user = session['user']
    q = progress_queues.get(user)
    if not q:
        return "Queue not initialized", 400

    def log(msg):
        print(msg)
        q.put(msg)

    target_username = request.form['username']
    user_path = os.path.join(BASE_PATH, user, target_username)

    scraper = InstagramScraper(
        target_username=target_username,
        path=user_path,
        logger=log
    )

    scraper.scrape()

    # Save history
    history = load_history(user)
    if target_username not in history:
        history.append(target_username)
    save_history(user, history)

    del progress_queues[user]
    return redirect(url_for('gallery', username=target_username))



@app.route('/gallery/<username>')
def gallery(username):
    if 'user' not in session:
        return redirect(url_for('index'))

    logged_in_user = session['user']
    image_dir = os.path.join(BASE_PATH, logged_in_user, username, 'images')
    desc_dir = os.path.join(BASE_PATH, logged_in_user, username, 'descriptions')

    images, descriptions = [], []

    if os.path.exists(image_dir):
        for file in sorted(os.listdir(image_dir)):
            if file.endswith('.jpg'):
                images.append(f"/{image_dir}/{file}")

    if os.path.exists(desc_dir):
        for file in sorted(os.listdir(desc_dir)):
            if file.endswith('.txt'):
                with open(os.path.join(desc_dir, file), 'r', encoding='utf-8') as f:
                    content = f.read()
                    description_line = content.split("Description:")[-1].strip()
                    descriptions.append(description_line)

    combined = list(zip(images, descriptions))
    return render_template('gallery.html', username=username, combined=combined)


@app.route('/history')
def history():
    if 'user' not in session:
        return redirect(url_for('index'))

    logged_in_user = session['user']
    usernames = load_history(logged_in_user)
    return render_template('history.html', usernames=usernames)


@app.route('/download/<user>/<scrape_name>/<path:filename>')
def download_file(user, scrape_name, filename):
    if 'user' not in session or session['user'] != user:
        abort(403)

    # ✅ Construct correct path to the file
    directory = os.path.join(BASE_PATH, user, scrape_name, 'descriptions')
    file_path = os.path.join(directory, filename)

    if not os.path.exists(file_path):
        abort(404)

    return send_from_directory(directory, filename, as_attachment=True)


@app.route('/logout')
def logout():
    print("🚪 Logging out:", session.get('user'))
    session.clear()
    if os.path.exists(COOKIE_FILE):
        os.remove(COOKIE_FILE)
    return redirect(url_for('index'))

@app.route('/progress-stream')
def progress_stream():
    if 'user' not in session:
        return "Unauthorized", 403

    user = session['user']
    q = progress_queues.get(user)

    if not q:
        return "No scrape in progress", 404

    def event_stream():
        while True:
            msg = q.get()
            yield f"data: {msg}\n\n"

    return Response(event_stream(), mimetype='text/event-stream')



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
