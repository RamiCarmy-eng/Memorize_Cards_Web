from flask import Flask, render_template, request, jsonify
import json
import random
import os
from pathlib import Path

app = Flask(__name__)

DATA_FILE = Path("memory_game_users.json")
IMAGE_FOLDER = Path("static/game_images")


def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


@app.route('/')
def index():
    return render_template('index.html')


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    name = data.get("name")
    password = data.get("password")

    if not name or not password:
        return jsonify({"message": "חסרים שם או סיסמה"}), 400

    users = load_data()

    if name in users:
        if users[name]["password"] == password:
            return jsonify({
                "status": "ok",
                "user": {"name": name}  # אל תחזיר best_score כאן – זה כבר ב-get_game_data
            })
        else:
            return jsonify({"message": "סיסמה שגויה"}), 401
    else:
        # הרשמה
        users[name] = {
            "password": password,
            "best_score": 999,
            "wins": 0
        }
        save_data(users)
        return jsonify({
            "status": "registered",
            "user": {"name": name}
        })


@app.route('/get_game_data')
def get_game_data():
    images = [f.name for f in IMAGE_FOLDER.iterdir() if f.suffix.lower() in ('.png', '.jpg', '.jpeg')]
    users = load_data()

    # יצירת לוח הישגים נקי – רק שם + best_score + wins (אם קיים)
    leaderboard = {}
    for name, info in users.items():
        leaderboard[name] = {
            "best_score": info.get("best_score", 999),
            "wins": info.get("wins", 0)
        }

    return jsonify({
        "images": images,
        "leaderboard": leaderboard
    })

@app.route('/update_stats', methods=['POST'])
def update_stats():
    data = request.json
    users = load_data()
    name = data.get('name')
    if name in users:
        if 'score' in data:  # שיא אישי
            if data['score'] < users[name]['best_score']:
                users[name]['best_score'] = data['score']
        if 'win' in data:  # ניצחון במולטי
            users[name]['wins'] += 1
        save_data(users)
    return jsonify({"status": "success"})


if __name__ == '__main__':
    app.run(debug=True)