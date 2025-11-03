import streamlit as st
import json
import requests
from datetime import datetime, date
import time
import random
from postgres import PostgresSingleton
from utils.filter_hotel_to_select import filter_hotel_to_select

st.set_page_config(page_title="2. Scrap Avis Booking", layout="centered")
st.title("💬 Scraping des avis Booking.com")
st.write("Récupération des **avis clients Booking.com** à partir des identifiants d’hôtel déjà extraits.")

# ========================================
# Singleton SQLite
# ========================================
db = PostgresSingleton()
conn = db.get_connection()

GRAPHQL_ENDPOINT = "https://www.booking.com/dml/graphql?lang=fr"
MAX_LIMIT = 25
# Charger payload et headers
with open("scrap_util/header.json", "r", encoding="utf-8") as f:
    HEADERS = json.load(f)
with open("scrap_util/payload.json", "r", encoding="utf-8") as f:
    PAYLOAD_TEMPLATE = json.load(f)

# ========================================
# Fonctions utilitaires
# ========================================
def wait():
    time.sleep(random.uniform(1, 3))

def post_graphql(payload, headers):
    response = requests.post(GRAPHQL_ENDPOINT, headers=headers, json=payload)
    return response.json()

def extract_review_info(card):
    info = {}
    
    # Basic review info
    info['review_score'] = card.get('reviewScore')
    info['reviewed_date'] = datetime.fromtimestamp(card.get('reviewedDate')).strftime('%Y-%m-%d %H:%M:%S') if card.get('reviewedDate') else None
    info['is_approved'] = card.get('isApproved')
    info['helpful_votes'] = card.get('helpfulVotesCount')
    info['review_url'] = card.get('reviewUrl')
    
    # Guest details
    guest = card.get('guestDetails', {})
    info['guest_username'] = guest.get('username')
    info['guest_type'] = guest.get('guestTypeTranslation')
    info['guest_country'] = guest.get('countryName')
    info['guest_country_code'] = guest.get('countryCode')
    info['guest_avatar_url'] = guest.get('avatarUrl')
    info['guest_anonymous'] = guest.get('anonymous')
    
    # Review text
    text = card.get('textDetails', {})
    info['review_title'] = text.get('title')
    info['positive_text'] = text.get('positiveText')
    info['negative_text'] = text.get('negativeText')
    info['language'] = text.get('lang')
    
    # Booking details
    booking = card.get('bookingDetails', {})
    info['stay_status'] = booking.get('stayStatus')
    info['checkin_date'] = booking.get('checkinDate')
    info['checkout_date'] = booking.get('checkoutDate')
    info['num_nights'] = booking.get('numNights')
    room = booking.get('roomType', {})
    info['room_name'] = room.get('name')
    info['room_id'] = room.get('id')
    
    return info



def is_review_newer_than(last_review_date, reference_date):
    """
    Compare the last reviewed_date of a given kalio_id with a reference date.
    Returns:
        - True if the last review is newer than reference_date
        - False if older or no review exists
    """
    if not last_review_date or not reference_date:
        return False  # missing data

    # Convert string to datetime if needed
    if isinstance(reference_date, str):
        try:
            reference_date = datetime.strptime(reference_date, "%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print(f"⚠️ Invalid reference_date string: {reference_date} ({e})")
            return False

    # Convert date to datetime if needed
    if isinstance(reference_date, date) and not isinstance(reference_date, datetime):
        reference_date = datetime.combine(reference_date, datetime.min.time())

    return last_review_date >= reference_date


def scrap_one_hotel(hotel_id, booking_id, payload_template, headers):
    last_review_date = db.get_last_reviewed_date(hotel_id) # Should be called one time


    payload = payload_template.copy()
    payload['variables']['input']['hotelId'] = int(booking_id)
    if not last_review_date: payload['variables']['input']['sorter'] = "OLDER_FIRST"

    # First call
    response = post_graphql(payload, headers)

    # Extract data
    data = response.get('data', {}).get('reviewListFrontend', {})

    # Add meta review score of hotel
    scores = data.get('ratingScores', {})
    meta = {s['name']: s['value'] for s in scores}

    db.insert_booking(
        id_kalio=hotel_id,
        hotel_staff=meta.get('hotel_staff'),
        hotel_services=meta.get('hotel_services'),
        hotel_clean=meta.get('hotel_clean'),
        hotel_comfort=meta.get('hotel_comfort'),
        hotel_value=meta.get('hotel_value'),
        hotel_location=meta.get('hotel_location'),
        hotel_free_wifi=meta.get('hotel_free_wifi')
    )
    
    cards = data.get('reviewCard', [])

    collected = 0
    # Insert first batch
    for card in cards:
        info = extract_review_info(card)
        if is_review_newer_than(last_review_date, info['reviewed_date']): return
        review_url = info.pop('review_url', None)  # remove it from kwargs
        db.insert_or_update_review(hotel_id, review_url, **info)
    collected += len(cards)

   
    progress = st.progress(0)
    
    total_reviews = data.get('reviewsCount', len(cards))
    skip = MAX_LIMIT

    while skip < total_reviews:
        wait()

        payload['variables']['input']['skip'] = skip


        response = post_graphql(payload, headers)
        cards = response.get('data', {}).get('reviewListFrontend', {}).get('reviewCard', [])
        for card in cards:
            info = extract_review_info(card)
            if is_review_newer_than(last_review_date, info['reviewed_date']):
                if progress:
                    progress.empty()
                return
            review_url = info.pop('review_url', None)  # remove it from kwargs
            db.insert_or_update_review(hotel_id, review_url, **info)

        collected += len(cards)
        progress.progress(min(collected / total_reviews, 1.0))
        
        skip += MAX_LIMIT

    
    progress.empty()


# ========================================
# Interface Streamlit
# ========================================


# Appel du module de filtrage personnalisé
selected_hotels = filter_hotel_to_select(is_id_booking=True)

if selected_hotels is not None and not selected_hotels.empty:
    st.write(f"✅ {len(selected_hotels)} hôtels sélectionnés pour le scraping.")

    if st.button("🚀 Lancer le scraping des hôtels sélectionnés"):
        global_bar = st.progress(0)
        status_text = st.empty()
        total_hotels = len(selected_hotels)

        for i, row in enumerate(selected_hotels.itertuples()):
            hotel_id = row.Index
            booking_id = row.id_booking
            name = row.name
            town = row.town
            try:
                status_text.text(f"🔍 Extraction des avis pour {name} ({town})...")
                scrap_one_hotel(hotel_id, booking_id, PAYLOAD_TEMPLATE, HEADERS)
            except Exception as e:
                st.error(f"Erreur pour {name}: {e}")
            global_bar.progress((i + 1) / total_hotels)

        status_text.empty()
        st.success("✅ Scraping terminé et avis insérés dans SQLite !")
