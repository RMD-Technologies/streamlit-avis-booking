import streamlit as st
import pandas as pd
from postgres.PostgresSingleton import PostgresSingleton
import os

st.set_page_config(page_title="🏠 Accueil", layout="centered")
st.title("🏨 Tableau de bord Booking.com")

# --------------------
# Singleton SQLite
# --------------------
db = PostgresSingleton(os.getenv("DATABASE_URL"))

# --------------------
# CSV upload to populate DB
# --------------------
st.subheader("📥 Importer un fichier CSV pour peupler la base")

uploaded_file = st.file_uploader(
    "Choisissez un fichier CSV avec les colonnes : name, town, id",
    type=["csv"]
)

if uploaded_file is not None:
    try:
        df_csv = pd.read_csv(uploaded_file)
        required_cols = {"name", "town", "id"}
        if not required_cols.issubset(df_csv.columns):
            st.error(f"Le CSV doit contenir les colonnes : {', '.join(required_cols)}")
        else:
            # Populate database
            for _, row in df_csv.iterrows():
                db.insert_or_update_hotel(
                    id=int(row["id"]),
                    name=row["name"],
                    town=row["town"],
                    url=None,
                    booking_id=None
                )
            st.success(f"✅ {len(df_csv)} hôtels ajoutés ou mis à jour dans la base !")
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier CSV : {e}")

# --------------------
# Statistiques
# --------------------
hotels_count = db.get_hotel_count()
st.subheader("📊 Statistiques")
st.write(f"- Nombre d'hôtels dans la base : **{hotels_count}**")

# --------------------
# Affichage des hôtels
# --------------------
if hotels_count > 0:
    df_hotels = db.get_all_hotels()
    st.dataframe(df_hotels)
else:
    st.info("Aucun hôtel stocké dans la base pour le moment.")
