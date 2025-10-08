import os
import json
import requests
import tqdm

# === CONFIG ===
INPUT_FOLDER = "scrap"
OUTPUT_FOLDER = "scrap_out"
API_URL = "http://raspberrypi:8000/predict"

# === SETUP ===
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Cache for already predicted texts
prediction_cache = {}

# === PROCESS EACH JSON FILE SEPARATELY ===
json_files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(".json")]

for filename in tqdm.tqdm(json_files, desc="Processing JSON files"):
    input_path = os.path.join(INPUT_FOLDER, filename)
    output_path = os.path.join(OUTPUT_FOLDER, filename)

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"⚠️ Error decoding JSON in file: {filename}")
        continue
    except Exception as e:
        print(f"⚠️ Error reading {filename}: {e}")
        continue

    # Process reviews
    reviews = data.get("scrap", {}).get("reviews", [])
    updated_reviews = []
    for review in reviews:
        review['positive_topics'] = []
        review['negative_topics'] = []
        language = review.get("language", "")
        if language != "fr": continue

        for sent, text in [('positive', review['positive_text']), ('negative', review['negative_text'])]:
            # Check cache
            if type(text) != str: continue 
            if text in prediction_cache:
                predictions = prediction_cache[text]
            else:
                try:
                    response = requests.post(API_URL, json={"input": text}, timeout=10)
                    if response.status_code == 200:
                        predictions = response.json()
                        prediction_cache[text] = predictions
                    else:
                        print(f"⚠️ API error {response.status_code} for review {text} in {filename}")
                        predictions = []
                except Exception as e:
                    print(f"⚠️ Request error for review {text} in {filename}: {e}")
                    predictions = []

            review[f'{sent}_topics'] = [p['topic'] for p in predictions if p['score'] > 0.8]

    # Save updated JSON
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Error saving {filename}: {e}")

print("✅ All JSON files processed and saved in 'scrap_out/' folder.")