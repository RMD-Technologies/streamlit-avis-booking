import sqlite3
import threading
import os
import pandas as pd

class SQLiteSingleton:
    _instance = None
    _lock = threading.Lock()  # pour thread-safe

    def __new__(cls, db_file="db/booking_reviews.db"):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(SQLiteSingleton, cls).__new__(cls)
                    cls._instance._init_db(db_file)
        return cls._instance

    def _init_db(self, db_file):
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        #self.conn.set_trace_callback(print)
        self._create_tables()

    def _create_tables(self):
        # Table hôtels
        cursor = self.get_cursor()

        # --- Table des hôtels ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS hotels (
            id INTEGER PRIMARY KEY,
            name TEXT,
            town TEXT,
            url TEXT UNIQUE,
            booking_id TEXT UNIQUE,

            -- Champs meta (tous optionnels)
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotel_id INTEGER NOT NULL,
            review_score REAL,
            reviewed_date TEXT,
            is_approved INTEGER,
            helpful_votes INTEGER DEFAULT 0,
            review_url TEXT NOT NULL,
            guest_username TEXT,
            guest_type TEXT,
            guest_country TEXT,
            guest_country_code TEXT,
            guest_avatar_url TEXT,
            guest_anonymous INTEGER,
            review_title TEXT,
            positive_text TEXT,
            negative_text TEXT,
            language TEXT,
            stay_status TEXT,
            checkin_date TEXT,
            checkout_date TEXT,
            num_nights INTEGER,
            room_name TEXT,
            room_id TEXT,
            FOREIGN KEY (hotel_id) REFERENCES hotels(id) ON DELETE CASCADE,
            UNIQUE(hotel_id, review_url)
        )
        """)

        self.commit()
        print(f"✅ Tables créées avec succès dans '{self.db_file}'")

    def get_connection(self):
        return self.conn

    def get_cursor(self):
        return self.conn.cursor()

    def commit(self):
        return self.conn.commit()

    def close(self):
        self.conn.close()
        SQLiteSingleton._instance = None
        print(f"✅ Connexion fermée pour '{self.db_file}'")
    
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
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = COALESCE(excluded.name, hotels.name),
                town = COALESCE(excluded.town, hotels.town),
                url = COALESCE(excluded.url, hotels.url),
                booking_id = COALESCE(excluded.booking_id, hotels.booking_id),
                hotel_staff = COALESCE(excluded.hotel_staff, hotels.hotel_staff),
                hotel_services = COALESCE(excluded.hotel_services, hotels.hotel_services),
                hotel_clean = COALESCE(excluded.hotel_clean, hotels.hotel_clean),
                hotel_comfort = COALESCE(excluded.hotel_comfort, hotels.hotel_comfort),
                hotel_value = COALESCE(excluded.hotel_value, hotels.hotel_value),
                hotel_location = COALESCE(excluded.hotel_location, hotels.hotel_location),
                hotel_free_wifi = COALESCE(excluded.hotel_free_wifi, hotels.hotel_free_wifi);
        """, (
            id, name, town, url, booking_id,
            hotel_staff, hotel_services, hotel_clean, hotel_comfort,
            hotel_value, hotel_location, hotel_free_wifi
        ))
        self.commit()
    
    def insert_or_update_review(self, hotel_id, review_url, **kwargs):
        cursor = self.get_cursor()

        # Convert booleans to 0/1
        for key in ["is_approved", "guest_anonymous"]:
            if key in kwargs and kwargs[key] is not None:
                kwargs[key] = int(kwargs[key])

        columns = ", ".join(["hotel_id", "review_url"] + list(kwargs.keys()))
        placeholders = ", ".join(["?"] * (2 + len(kwargs)))
        updates = ", ".join([f"{col} = COALESCE(excluded.{col}, reviews.{col})" for col in kwargs.keys()])

        values = [hotel_id, review_url] + list(kwargs.values())

        sql = f"""
            INSERT INTO reviews ({columns})
            VALUES ({placeholders})
            ON CONFLICT(hotel_id, review_url) DO UPDATE SET
                {updates}
        """

        cursor.execute(sql, values)
        self.conn.commit()
        
    def get_hotel_count(self):
        try:
            cursor = self.get_cursor()
            cursor.execute("SELECT COUNT(*) FROM hotels")
            return cursor.fetchone()[0]
        except:
            return 0

    def get_all_hotels(self):
        try:
            return pd.read_sql("SELECT * FROM hotels", self.get_connection(),  index_col="id")
        except:
            return pd.DataFrame()
