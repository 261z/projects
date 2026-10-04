import os

import psycopg
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
    )

def load_weather(records):
    insert_sql = """
        INSERT INTO raw.weather_forecast (
            area,
            latitude,
            longitude,
            forecast,
            api_timestamp,
            update_timestamp,
            valid_start,
            valid_end
        )
        VALUES (
            %(area)s,
            %(latitude)s,
            %(longitude)s,
            %(forecast)s,
            %(api_timestamp)s,
            %(update_timestamp)s,
            %(valid_start)s,
            %(valid_end)s
        )
        ON CONFLICT (area, api_timestamp)
        DO NOTHING;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(insert_sql, records)
            inserted_rows = cur.rowcount

        conn.commit()

    print(
    f"Processed {len(records)} records. "
    f"Inserted {inserted_rows} new records."
    )

if __name__ == "__main__":
    from extract_weather import fetch_weather, transform_weather

    weather_data = fetch_weather()
    records = transform_weather(weather_data)

    load_weather(records)