import json
import requests
import datetime
import time
import random
from tqdm import tqdm
import pandas as pd
import re

def wait():
    time.sleep(random.uniform(1, 3))


GRAPHQL_ENDPOINT = "https://www.booking.com/dml/graphql?lang=fr"

MAX_LIMIT = 25

with open('payload.json', 'r', encoding='utf-8') as file:
    payload = json.load(file)

with open('header.json', 'r', encoding='utf-8') as file:
    GRAPHQL_HEADER = json.load(file)

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

options = Options()
options.set_preference("dom.webdriver.enabled", False)  # Try to hide Selenium
options.set_preference("useAutomationExtension", False)
options.set_preference("general.useragent.override", 
                       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36")  # Fake user-agent
options.add_argument("--headless")  # VERY IMPORTANT on Pi without GUI


def get_hotel_id(url, timeout=10):
    driver = webdriver.Firefox(service=Service("driver/geckodriver"), options=options)

    # Open the page
    driver.get(url)
    
    # Wait a random time to mimic human reading
    wait()
    
    try:
        # Wait for the input element with name="hotel_id" to appear
        hotel_input = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.NAME, "hotel_id"))
        )
        # Scroll into view (mimic human behavior)
        driver.execute_script("arguments[0].scrollIntoView(true);", hotel_input)
        time.sleep(random.uniform(0.5, 1.5))
        
        # Get the value attribute
        hotel_id = hotel_input.get_attribute("value")
        hotel_id = int(hotel_id)
    except Exception as e:
        print(f"Hotel ID input not found. Error: {e}")
        hotel_id = None
    driver.quit()
    return hotel_id

def post_graphql(payload):
    response = requests.post(GRAPHQL_ENDPOINT, headers=GRAPHQL_HEADER, json=payload)
    return response.json()

def extract_review_info(card):
    info = {}
    
    # Basic review info
    info['review_score'] = card.get('reviewScore')
    info['reviewed_date'] = datetime.datetime.fromtimestamp(card.get('reviewedDate')).strftime('%Y-%m-%d %H:%M:%S') if card.get('reviewedDate') else None
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

def scrap(hotel_id):
    D = {'meta': {}, 'reviews': []}
    payload_hotel = payload.copy()
    payload_hotel['variables']['input']['hotelId'] = hotel_id

    # First call
    response = post_graphql(payload_hotel)
    scores = response['data']['reviewListFrontend']['ratingScores']
    for s in scores:
        D['meta'][s['name']] = s['value']
    
    cards = response['data']['reviewListFrontend']['reviewCard']

    for card in cards:
        D['reviews'].append(extract_review_info(card))

    
    review_count = response['data']['reviewListFrontend']['reviewsCount']

    skip = MAX_LIMIT
# Create a tqdm progress bar
    with tqdm(total=review_count) as pbar:
        pbar.update(len(cards))
        while skip < review_count:
            # Optional wait to avoid rate limits
            wait()

            # Determine the end index for this batch
            end = min(skip + MAX_LIMIT, review_count)

            # Update payload for this batch
            payload_hotel['variables']['input']['skip'] = skip
            response = post_graphql(payload_hotel)
            cards = response['data']['reviewListFrontend']['reviewCard']

            # Process reviews
            for card in cards: # Skip first dupicated
                D['reviews'].append(extract_review_info(card))

            # Update the progress bar
            pbar.update(len(cards))

            # Update skip for the next batch
            skip = end

    return D

def save_to_file(D, filename="reviews.json"):
    """Save the scraped data to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(D, f, ensure_ascii=False, indent=4)
    print(f"Data saved to {filename}")

def read_hotels_csv(filename="hotels_with_urls.csv"):
    """
    Read the CSV file containing hotel info and URLs.
    """
    try:
        df = pd.read_csv(filename, encoding="utf-8")
        print(f"Loaded {len(df)} hotels from '{filename}'")
        return df
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None

def sanitize_filename(s):
    """
    Remove or replace characters not allowed in filenames.
    """
    s = re.sub(r'[\\/*?:"<>|]', "_", s)
    s = s.replace(" ", "_").lower()
    return s

def main():
    df = read_hotels_csv()
    tuples_list = list(df[["id", "name", "town", "url"]].itertuples(index=False, name=None))


    for id_, name, town, url in tqdm(tuples_list):
        D = {
            'id': id_,
            'name': name,
            'town': town,
            'url': url,
            'booking_id': -1,
            'scrap': {}
        }

        # Scrape the reviews
        try:
            hotel_id = get_hotel_id(url)
            if not hotel_id: continue
            D['booking_id'] = hotel_id
            D_reviews = scrap(hotel_id)
            D['scrap'] = D_reviews

            # Create filename based on id, name, town
            filename = f"{id_}_{sanitize_filename(name)}_{sanitize_filename(town)}.json"

            save_to_file(D, 'scrap/'+filename)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    main()