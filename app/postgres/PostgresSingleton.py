import threading
import pandas as pd
from sqlalchemy import create_engine
import psycopg2
from datetime import date


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

        # SQLAlchemy
        self.sql_alchemy_engine = create_engine(
            db_url.replace("postgres://", "postgresql+psycopg2://", 1)
        )

        # psycopg2
        self.conn = psycopg2.connect(self.db_url)
        self.conn.autocommit = True
        self._create_tables()

    def _create_tables(self):
        cursor = self.get_cursor()

        # --- Table des hôtels ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS kalios (
            id_kalio SERIAL PRIMARY KEY,
            name TEXT,
            town TEXT,
            url TEXT UNIQUE,
            id_booking TEXT UNIQUE
        )
        """)

        # --- Table des évaluations (ratings) ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id SERIAL PRIMARY KEY,
            id_kalio INTEGER REFERENCES kalios(id_kalio) ON DELETE CASCADE,
            date_scrap DATE,
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
            id_kalio INTEGER NOT NULL REFERENCES kalios(id_kalio) ON DELETE CASCADE,
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
            UNIQUE(id_kalio, review_url)
        )
        """)

        print(f"✅ Tables créées avec succès dans PostgreSQL")

    # --------------------
    # Connection & cursor
    # --------------------
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
    def insert_or_update_kalio(self, id_kalio=None, name=None, town=None, url=None, id_booking=None):
        cursor = self.get_cursor()
        cursor.execute("""
            INSERT INTO kalios (id_kalio, name, town, url, id_booking)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT(id_kalio) DO UPDATE SET
                name = COALESCE(EXCLUDED.name, kalios.name),
                town = COALESCE(EXCLUDED.town, kalios.town),
                url = COALESCE(EXCLUDED.url, kalios.url),
                id_booking = COALESCE(EXCLUDED.id_booking, kalios.id_booking);
        """, (id_kalio, name, town, url, id_booking))
    
    def insert_booking(
        self,
        id_kalio,
        hotel_staff=None,
        hotel_services=None,
        hotel_clean=None,
        hotel_comfort=None,
        hotel_value=None,
        hotel_location=None,
        hotel_free_wifi=None
    ):
        cursor = self.get_cursor()
        
        # Use today's date for date_scrap
        date_scrap = date.today()
        
        columns = [
            "id_kalio", "date_scrap", "hotel_staff", "hotel_services",
            "hotel_clean", "hotel_comfort", "hotel_value", "hotel_location",
            "hotel_free_wifi"
        ]
        
        values = [
            id_kalio, date_scrap, hotel_staff, hotel_services,
            hotel_clean, hotel_comfort, hotel_value, hotel_location,
            hotel_free_wifi
        ]
        
        placeholders = ", ".join(["%s"] * len(values))
        
        sql = f"""
            INSERT INTO bookings ({', '.join(columns)})
            VALUES ({placeholders})
        """
        
        try:
            cursor.execute(sql, values)
        except Exception as e:
            print(f"Error inserting booking for id_kalio={id_kalio}: {e}")

    # --------------------
    # Insert or update review
    # --------------------
    def insert_or_update_review(self, id_kalio, review_url, **kwargs):
        cursor = self.get_cursor()

        # Convert booleans
        for key in ["is_approved", "guest_anonymous"]:
            if key in kwargs and kwargs[key] is not None:
                kwargs[key] = bool(kwargs[key])

        columns = ["id_kalio", "review_url"] + list(kwargs.keys())
        values = [id_kalio, review_url] + list(kwargs.values())
        placeholders = ", ".join(["%s"] * len(values))
        updates = ", ".join([f"{col} = COALESCE(EXCLUDED.{col}, reviews.{col})" for col in kwargs.keys()])

        sql = f"""
            INSERT INTO reviews ({', '.join(columns)})
            VALUES ({placeholders})
            ON CONFLICT(id_kalio, review_url) DO UPDATE SET
                {updates}
        """
        cursor.execute(sql, values)

    # --------------------
    # Utility methods
    # --------------------
    def get_kalio_count(self):
        try:
            cursor = self.get_cursor()
            cursor.execute("SELECT COUNT(*) FROM kalios;")
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error getting kalio count: {e}")
            return 0

    def get_all_kalios(self):
        try:
            return pd.read_sql(
                "SELECT * FROM kalios;", 
                self.sql_alchemy_engine, 
                index_col="id_kalio"
            )
        except Exception as e:
            print(f"Error fetching kalios: {e}")
            return pd.DataFrame()