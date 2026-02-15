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
                "user": {
                    "name": name,
                    "best_scores": users[name].get("best_scores", {"4x4": 999, "6x6": 999, "8x8": 999})
                }
            })
        else:
            return jsonify({"message": "סיסמה שגויה"}), 401
    else:
        # הרשמה
        users[name] = {
            "password": password,
            "best_scores": {"4x4": 999, "6x6": 999, "8x8": 999}, # שיאים נפרדים
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

    leaderboard = {}
    for name, info in users.items():
        # אנחנו שולחים את כל המילון כפי שהוא
        leaderboard[name] = {
            "best_scores": info.get("best_scores", {"4x4": 999, "6x6": 999, "8x8": 999}),
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
    difficulty = data.get('difficulty')  # ה-JS ישלח למשל "4x4"
    score = data.get('score')

    if name in users:
        # עדכון שיא אישי לפי רמה
        if score is not None and difficulty:
            # וודא שקיים מילון שיאים, אם לא - צור אחד
            if "best_scores" not in users[name]:
                users[name]["best_scores"] = {"4x4": 999, "6x6": 999, "8x8": 999}

            current_best = users[name]["best_scores"].get(difficulty, 999)
            if score < current_best:
                users[name]["best_scores"][difficulty] = score

        # עדכון ניצחונות במצב זוגי
        if data.get('win'):
            users[name]['wins'] = users[name].get('wins', 0) + 1

        save_data(users)
        return jsonify({"status": "success"})

    return jsonify({"status": "error", "message": "User not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)