import wave
import struct
import math
import os


def create_sound(filename, duration=0.1, freq=440, volume=0.5):
    """יוצר קובץ קול בסיסי בפורמט WAV"""
    os.makedirs('static/sounds', exist_ok=True)
    path = os.path.join('static/sounds', filename)

    sample_rate = 44100.0
    num_samples = int(duration * sample_rate)

    with wave.open(path, 'w') as f:
        f.setnchannels(1)  # Mono
        f.setsampwidth(2)  # 16-bit
        f.setframerate(int(sample_rate))

        for i in range(num_samples):
            # יצירת גל סינוס
            value = int(volume * 32767.0 * math.sin(2.0 * math.pi * freq * i / sample_rate))
            data = struct.pack('<h', value)
            f.writeframesraw(data)

    print(f"✅ Created: {path}")


# יצירת הצלילים הנדרשים
if __name__ == "__main__":
    # צליל קצר ונמוך להפיכת קלף
    create_sound('flip.wav', duration=0.1, freq=400)

    # צליל גבוה ונעים להתאמה (זוג)
    create_sound('match.wav', duration=0.3, freq=880)

    # צליל עולה לניצחון
    create_sound('complete.wav', duration=0.5, freq=1200)

    # צליל מיוחד לשיא חדש
    create_sound('record.wav', duration=0.6, freq=1500)