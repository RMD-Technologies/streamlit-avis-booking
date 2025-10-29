import streamlit as st
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager 
import platform


st.set_page_config(page_title="1. Scrap ID Booking", layout="centered")
st.title("🏨 Scrap ID Booking.com")
st.write("Cette page permet d'extraire automatiquement les URLs des hôtels depuis un fichier CSV.")

# ==============================
# Fonctions utilitaires
# ==============================

ENDPOINT = "https://www.booking.com/searchresults.fr.html?ss="

def wait():
    """Pause aléatoire pour éviter d'être détecté comme bot"""
    time.sleep(random.uniform(1, 3))

def build_query(hotel_name, town):
    query = ENDPOINT + '+'.join(town.split()) + '+' + '+'.join(hotel_name.split())
    return query.lower()

def read_file(uploaded_file):
    """Lecture d'un fichier CSV en DataFrame"""
    try:
        df = pd.read_csv(uploaded_file)
        return df
    except Exception as e:
        st.error(f"Erreur de lecture du fichier : {e}")
        return None

def setup_driver():
    options = Options()
    options.add_argument("--headless")  # Optionnel : exécuter sans fenêtre
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)

    system = platform.system()
    machine = platform.machine()

    if system == "Linux" and "arm" in machine.lower():
        # Probablement Raspberry Pi
        driver_path = "driver/geckodriver-rp"  # Assurez-vous qu'il est installé via apt
        service = Service(driver_path)
    else:
        # PC classique : utiliser GeckoDriverManager
        service = Service(GeckoDriverManager().install())

    driver = webdriver.Firefox(service=service, options=options)
    return driver

def get_hotel_url(driver, hotel, town):
    """Retourne l'URL du premier hôtel trouvé"""
    query = build_query(hotel, town)
    driver.get(query)
    wait()

    try:
        a_tag = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='hotel']"))
        )
        href = a_tag.get_attribute("href")
        return href.split("?")[0]
    except Exception:
        return ""

def get_hotel_id(url, timeout=10):
    """Retourne l'id booking depuis l'URL de l'hôtel"""
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

    return hotel_id


# ==============================
# Interface Streamlit
# ==============================
from postgres.PostgresSingleton import PostgresSingleton
from utils.filter_hotel_to_select import filter_hotel_to_select

db = PostgresSingleton()

# Get all hotels from DB
df_hotels = db.get_all_kalios()  # id as index

if df_hotels.empty:
    st.info("Aucun hôtel disponible dans la base.")
else:
    # Call the custom Streamlit module for filtering
    selected_hotels = filter_hotel_to_select(
        df_hotels,
    )

    if selected_hotels is not None and not selected_hotels.empty:
        st.write(f"✅ {len(selected_hotels)} hôtels sélectionnés pour le scraping.")

        if st.button("🚀 Lancer le scraping des hôtels sélectionnés"):
            with st.spinner("Initialisation du navigateur..."):
                driver = setup_driver()

            results = []
            total = len(selected_hotels)
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Iterate over selected hotels
            for count, (i, row) in enumerate(selected_hotels.iterrows(), start=1):
                id_ = i  # still use index for DB
                name = row["name"] if pd.notna(row["name"]) else ""
                town = row["town"] if pd.notna(row["town"]) else ""

                status_text.text(f"🔍 Recherche : {name} ({town})")
                try:
                    url = get_hotel_url(driver, name, town)
                    id_booking = get_hotel_id(url)
                    db.insert_or_update_kalio(id_kalio=id_, url=url, id_booking=id_booking)
                except Exception as e:
                    # Log the error but continue
                    st.error(f"⚠️ Erreur pour {name} ({town}): {e}")

                progress_bar.progress(count / total)

            driver.quit()
            st.success("✅ Scraping terminé et base mise à jour avec succès !")
    else:
        st.info("Veuillez sélectionner au moins un hôtel à scraper.")