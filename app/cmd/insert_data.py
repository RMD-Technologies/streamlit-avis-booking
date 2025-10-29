from postgres.PostgresSingleton import PostgresSingleton

from glob import glob
import json
from tqdm import tqdm
import logging

# --- Setup logging ---
logging.basicConfig(
    filename="import_errors.log",
    filemode="a",  # append mode
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

db = PostgresSingleton()
DIR = 'app/output'

for file in tqdm(glob(f"{DIR}/*.json"), desc="Inserting hotels..."):
    try:
        with open(file, mode="r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        logging.exception(f"Error reading file {file}")
        continue  # skip to next file

    try:
        # --- 1️⃣ Insert or update hotel ---
        id_kalio = data.get("id")
        name = data.get("name")
        town = data.get("town")
        url = data.get("url")
        id_booking = data.get("booking_id")

        try:
            db.insert_or_update_kalio(
                id_kalio=id_kalio,
                name=name,
                town=town,
                url=url,
                id_booking=id_booking
            )
        except Exception:
            logging.exception(f"Error inserting/updating hotel {id_kalio}")

        # --- 2️⃣ Insert booking meta (ratings) ---
        meta = data.get("scrap", {}).get("meta", {})
        if meta:
            try:
                db.insert_booking(
                    id_kalio=id_kalio,
                    hotel_staff=meta.get("hotel_staff"),
                    hotel_services=meta.get("hotel_services"),
                    hotel_clean=meta.get("hotel_clean"),
                    hotel_comfort=meta.get("hotel_comfort"),
                    hotel_value=meta.get("hotel_value"),
                    hotel_location=meta.get("hotel_location"),
                    hotel_free_wifi=meta.get("hotel_free_wifi"),
                )
            except Exception:
                logging.exception(f"Error inserting booking meta for hotel {id_kalio}")

        # --- 3️⃣ Insert or update reviews ---
        reviews = data.get("scrap", {}).get("reviews", [])
        for r in reviews:
            try:
                review_url = r.pop("review_url", None)
                if not review_url:
                    logging.error(f"Missing review_url for hotel {id_kalio}, skipping review.")
                    continue

                db.insert_or_update_review(
                    id_kalio=id_kalio,
                    review_url=review_url,
                    **r
                )
            except Exception:
                logging.exception(f"Error inserting review for hotel {id_kalio}")

    except Exception:
        logging.exception(f"Unexpected error processing file {file}")
        continue

# Optional: close connection after all inserts
db.close()
logging.info("✅ Import completed.")
