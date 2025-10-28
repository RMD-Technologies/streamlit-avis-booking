import threading
import os
import pandas as pd
from sqlalchemy import create_engine
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values

class PostgresSingleton:
    _instance = None
    _lock = threading.Lock()  # pour thread-safe

    def __new__(cls, db_url="postgresql://user:password@localhost:5432/booking_reviews"):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(PostgresSingleton, cls).__new__(cls)
                    cls._instance._init_db(db_url)
        return cls._instance

    def _init_db(self, db_url):
        self.db_url = db_url

        #SQLAlchemy
        self.sql_alchemy_engine = create_engine(db_url.replace("postgres://", "postgresql+psycopg2://", 1))

        # psycopg2
        self.conn = psycopg2.connect(self.db_url)
        self.conn.autocommit = True
        self._create_tables()

    def _create_tables(self):
        cursor = self.get_cursor()

        # --- Table des hôtels ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS hotels (
            id SERIAL PRIMARY KEY,
            name TEXT,
            town TEXT,
            url TEXT UNIQUE,
            booking_id TEXT UNIQUE,
            hotel_staff REAL,
            hotel_services REAL,
            hotel_clean REAL,
            hotel_comfort REAL,
            hotel_value REAL,
            hotel_location REAL,
            hotel_free_wifi REAL
        )
        """)

        # --- Table des avis ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id SERIAL PRIMARY KEY,
            hotel_id INTEGER NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
            review_score REAL,
            reviewed_date TIMESTAMP,
            is_approved BOOLEAN,
            helpful_votes INTEGER DEFAULT 0,
            review_url TEXT NOT NULL,
            guest_username TEXT,
            guest_type TEXT,
            guest_country TEXT,
            guest_country_code TEXT,
            guest_avatar_url TEXT,
            guest_anonymous BOOLEAN,
            review_title TEXT,
            positive_text TEXT,
            negative_text TEXT,
            language TEXT,
            stay_status TEXT,
            checkin_date TIMESTAMP,
            checkout_date TIMESTAMP,
            num_nights INTEGER,
            room_name TEXT,
            room_id TEXT,
            UNIQUE(hotel_id, review_url)
        )
        """)
        print(f"✅ Tables créées avec succès dans PostgreSQL")

    def get_connection(self):
        return self.conn

    def get_cursor(self):
        return self.conn.cursor()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()
        PostgresSingleton._instance = None
        print(f"✅ Connexion PostgreSQL fermée")
    
    # --------------------
    # Insert or update hotel
    # --------------------
    def insert_or_update_hotel(
        self,
        id,
        name=None,
        town=None,
        url=None,
        booking_id=None,
        hotel_staff=None,
        hotel_services=None,
        hotel_clean=None,
        hotel_comfort=None,
        hotel_value=None,
        hotel_location=None,
        hotel_free_wifi=None
    ):
        cursor = self.get_cursor()
        cursor.execute("""
            INSERT INTO hotels (
                id, name, town, url, booking_id,
                hotel_staff, hotel_services, hotel_clean, hotel_comfort,
                hotel_value, hotel_location, hotel_free_wifi
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(id) DO UPDATE SET
                name = COALESCE(EXCLUDED.name, hotels.name),
                town = COALESCE(EXCLUDED.town, hotels.town),
                url = COALESCE(EXCLUDED.url, hotels.url),
                booking_id = COALESCE(EXCLUDED.booking_id, hotels.booking_id),
                hotel_staff = COALESCE(EXCLUDED.hotel_staff, hotels.hotel_staff),
                hotel_services = COALESCE(EXCLUDED.hotel_services, hotels.hotel_services),
                hotel_clean = COALESCE(EXCLUDED.hotel_clean, hotels.hotel_clean),
                hotel_comfort = COALESCE(EXCLUDED.hotel_comfort, hotels.hotel_comfort),
                hotel_value = COALESCE(EXCLUDED.hotel_value, hotels.hotel_value),
                hotel_location = COALESCE(EXCLUDED.hotel_location, hotels.hotel_location),
                hotel_free_wifi = COALESCE(EXCLUDED.hotel_free_wifi, hotels.hotel_free_wifi);
        """, (
            id, name, town, url, booking_id,
            hotel_staff, hotel_services, hotel_clean, hotel_comfort,
            hotel_value, hotel_location, hotel_free_wifi
        ))
    
    def insert_or_update_review(self, hotel_id, review_url, **kwargs):
        cursor = self.get_cursor()

        # Convert booleans
        for key in ["is_approved", "guest_anonymous"]:
            if key in kwargs and kwargs[key] is not None:
                kwargs[key] = bool(kwargs[key])

        columns = ["hotel_id", "review_url"] + list(kwargs.keys())
        values = [hotel_id, review_url] + list(kwargs.values())
        placeholders = ", ".join(["%s"] * len(values))
        updates = ", ".join([f"{col} = COALESCE(EXCLUDED.{col}, reviews.{col})" for col in kwargs.keys()])

        sql = f"""
            INSERT INTO reviews ({', '.join(columns)})
            VALUES ({placeholders})
            ON CONFLICT(hotel_id, review_url) DO UPDATE SET
                {updates}
        """
        cursor.execute(sql, values)
        
    def get_hotel_count(self):
        try:
            cursor = self.get_cursor()
            cursor.execute("SELECT COUNT(*) FROM hotels")
            return cursor.fetchone()[0]
        except:
            return 0

    def get_all_hotels(self):
        try:
            return pd.read_sql("SELECT * FROM hotels", self.sql_alchemy_engine, index_col="id")
        except:
            return pd.DataFrame()
