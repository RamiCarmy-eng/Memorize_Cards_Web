from flask import Flask, render_template, request, jsonify
import json
from pathlib import Path

app = Flask(__name__)
DATA_FILE = Path('memory_game_users.json')
IMAGE_FOLDER = Path("static/game_images")


def get_image_list():
    """Get all images from the game_images directory"""
    if IMAGE_FOLDER.exists() and IMAGE_FOLDER.is_dir():
        images = [f.name for f in IMAGE_FOLDER.iterdir()
                  if f.suffix.lower() in {'.png', '.jpg', '.jpeg', '.gif', '.webp'}]
        print(f"[IMAGES] Found {len(images)} images in {IMAGE_FOLDER}")
        return sorted(images)
    else:
        print(f"[WARNING] Images directory not found: {IMAGE_FOLDER}")
        return []


def load_data():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Convert old format to new format
            if 'users' not in data:
                print("[MIGRATION] Converting old data format to new format...")
                old_users = {k: v for k, v in data.items() if k != 'images'}
                images = get_image_list()

                data = {
                    "users": old_users,
                    "images": images
                }
                save_data(data)
                print("[MIGRATION] Data migration complete!")

            # Always refresh images list
            data['images'] = get_image_list()

            return data
        except json.JSONDecodeError:
            print("[ERROR] Corrupted JSON file. Creating new one.")
            return {"users": {}, "images": get_image_list()}

    print("[INIT] Creating new data file...")
    return {"users": {}, "images": get_image_list()}


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    data = load_data()
    req = request.get_json()
    name = req.get('name')
    password = req.get('password')

    if name in data['users']:
        if data['users'][name]['password'] == password:
            return jsonify({"message": "Login successful", "user": data['users'][name]}), 200
        else:
            return jsonify({"message": "Wrong password"}), 401
    else:
        # Create new user
        data['users'][name] = {
            "password": password,
            "wins": 0,
            "best_scores": {
                "4x4": None,
                "6x6": None,
                "8x8": None
            }
        }
        save_data(data)
        return jsonify({"message": "User created", "user": data['users'][name]}), 200


@app.route('/update_stats', methods=['POST'])
def update_stats():
    data = load_data()
    req = request.get_json()

    name = req.get('name')
    difficulty = req.get('difficulty')
    turns = req.get('turns')
    time_taken = req.get('time')
    mode = req.get('mode')
    win = req.get('win')

    print(f"[UPDATE_STATS] Received: name={name}, diff={difficulty}, turns={turns}, time={time_taken}s, mode={mode}")

    if name not in data['users']:
        return jsonify({"message": "User not found"}), 404

    user = data['users'][name]

    # עדכון ניצחונות במצב זוגי
    if mode == 'Multi' and win:
        user['wins'] = user.get('wins', 0) + 1
        print(f"[UPDATE_STATS] 🏆 Win added for {name}. Total wins: {user['wins']}")

    # עדכון שיא אישי במצב שחקן יחיד
    if mode == 'Single' and turns is not None and time_taken is not None:
        # וידוא שקיים אובייקט best_scores
        if "best_scores" not in user:
            user["best_scores"] = {"4x4": None, "6x6": None, "8x8": None}

        current_best = user['best_scores'].get(difficulty)

        # לוגיקת החלטה: האם זה שיא חדש?
        is_new_record = False

        # 1. אם מעולם לא נקבע שיא
        if current_best is None or current_best.get('turns') is None:
            is_new_record = True
        else:
            old_turns = current_best.get('turns')
            old_time = current_best.get('time', 9999)

            # 2. אם כמות התורות קטנה יותר
            if turns < old_turns:
                is_new_record = True
            # 3. אם כמות התורות שווה, אבל הזמן מהיר יותר
            elif turns == old_turns and time_taken < old_time:
                is_new_record = True
            # 4. תיקון נתונים: אם קיים שיא אבל הזמן הוא 0
            elif old_time == 0:
                is_new_record = True

        if is_new_record:
            user['best_scores'][difficulty] = {
                "turns": turns,
                "time": time_taken
            }
            print(f"[UPDATE_STATS] ✅ NEW RECORD! {name} | {difficulty}: {turns} turns, {time_taken}s")
        else:
            print(f"[UPDATE_STATS] ⏭️ No improvement. Current best for {name}: {current_best.get('turns')} turns")

    save_data(data)
    return jsonify({"message": "Stats updated", "user": user}), 200


@app.route('/get_game_data', methods=['GET'])
def get_game_data():
    data = load_data()
    print(f"[GET_GAME_DATA] Sending {len(data['images'])} images to client")
    return jsonify({
        "images": data['images'],
        "leaderboard": data['users']
    })


if __name__ == '__main__':
    images = get_image_list()
    print(f"\n{'=' * 50}")
    print(f"🎮 Memory Game Server Starting...")
    print(f"📁 Images directory: {IMAGE_FOLDER}")
    print(f"🖼️  Total images available: {len(images)}")
    print(f"📊 User data file: {DATA_FILE}")
    print(f"{'=' * 50}\n")

    app.run(debug=True, port=5000)