import os
import time
import requests
import psycopg2
from datetime import datetime

API_KEY     = os.getenv("API_KEY")
FLIGHTS_URL = "http://api.aviationstack.com/v1/flights"

BLACK_SEA_IATAS = ["IST", "SAW", "AER", "TBS"]

# bbox Чёрного моря
MIN_LAT, MAX_LAT = 40.5, 46.5
MIN_LON, MAX_LON = 27.5, 41.5

# параметры пагинации
PAGE_LIMIT = 100
MAX_PAGES  = 3

# подключение к БД
conn = psycopg2.connect(
    dbname   = os.getenv("DB_NAME"),
    user     = os.getenv("DB_USER"),
    password = os.getenv("DB_PASSWORD"),
    host     = os.getenv("DB_HOST"),
    port     = os.getenv("DB_PORT"),
)
cursor = conn.cursor()

processed = 0
skipped   = 0

def insert_flight(f):
    global processed, skipped

    # фильтрация по live‐координатам
    live = f.get("live") or {}
    lat, lon = live.get("latitude"), live.get("longitude")
    if lat is not None and lon is not None:
        if not (MIN_LAT <= lat <= MAX_LAT and MIN_LON <= lon <= MAX_LON):
            skipped += 1
            return

    # вытаскиваем dictы вылета/прилёта
    dep = f.get("departure", {}) or {}
    arr = f.get("arrival",   {}) or {}

    dep_iata = dep.get("iata")
    arr_iata = arr.get("iata")

    dep_iata_db = dep_iata if dep_iata in BLACK_SEA_IATAS else None
    arr_iata_db = arr_iata if arr_iata in BLACK_SEA_IATAS else None

    dep_airport = dep.get("airport")
    arr_airport = arr.get("airport")

    # модель самолёта
    ac = f.get("aircraft") or {}
    model = ac.get("model") or ac.get("iata") or ac.get("icao")
    if not model:
        skipped += 1
        return

    airline   = f.get("airline", {}).get("name")
    callsign  = f.get("flight",  {}).get("number")
    icao_code = f.get("flight",  {}).get("icao")
    date_str  = f.get("flight_date")

    if not all([airline, callsign, icao_code, dep_airport, arr_airport, date_str]):
        skipped += 1
        return

    # парсим дату
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        skipped += 1
        return

    # INSERT airline
    cursor.execute(
        "INSERT INTO airlines(name) VALUES(%s) "
        "ON CONFLICT(name) DO NOTHING RETURNING id",
        (airline,)
    )
    res = cursor.fetchone()
    airline_id = res[0] if res else None
    if airline_id is None:
        cursor.execute("SELECT id FROM airlines WHERE name=%s", (airline,))
        airline_id = cursor.fetchone()[0]

    # INSERT model
    cursor.execute(
        "INSERT INTO aircraft_models(model_name) VALUES(%s) "
        "ON CONFLICT(model_name) DO NOTHING RETURNING id",
        (model,)
    )
    res = cursor.fetchone()
    model_id = res[0] if res else None
    if model_id is None:
        cursor.execute(
            "SELECT id FROM aircraft_models WHERE model_name=%s", (model,)
        )
        model_id = cursor.fetchone()[0]

    # INSERT flight
    cursor.execute(
        """
        INSERT INTO flights
        (callsign, icao_code, aircraft_model_id, airline_id,
        departure_airport, arrival_airport, timestamp, dep_iata, arr_iata)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (callsign, icao_code, model_id, airline_id,
        dep_airport, arr_airport, dt,
        dep_iata_db, arr_iata_db)
    )

    processed += 1

def fetch_for_iata(iata_code, direction):
    # тянем до MAX_PAGES страниц (offset=0,100,200)
    for page in range(MAX_PAGES):
        offset = page * PAGE_LIMIT
        params = {
            "access_key": API_KEY,
            "flight_status":"active",
            "limit": PAGE_LIMIT,
            "offset": offset,
            f"{direction}_iata": iata_code
        }
        try:
            r = requests.get(FLIGHTS_URL, params=params, timeout=10)
        except requests.RequestException as e:
            print(f"[{iata_code}/{direction}] Сеть: {e}")
            return

        if r.status_code == 429:
            print(f"[{iata_code}/{direction}] rate‑limit, stop.")
            return
        if not r.ok:
            print(f"[{iata_code}/{direction}] HTTP {r.status_code}, stop.")
            return

        lst = r.json().get("data") or []
        if not lst:
            return

        print(f"[{iata_code}/{direction}] page {page+1}, got {len(lst)}")
        for f in lst:
            insert_flight(f)

        time.sleep(1)


### ――― основной запуск ―――

for code in BLACK_SEA_IATAS:
    for dir_ in ("dep","arr"):
        fetch_for_iata(code, dir_)

conn.commit()
cursor.close()
conn.close()

print(f"Inserted: {processed}, skipped: {skipped}")