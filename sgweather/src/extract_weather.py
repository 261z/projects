import requests

API_URL = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"


def fetch_weather():
    response = requests.get(API_URL, timeout=30)

    response.raise_for_status()

    data = response.json()

    return data

def transform_weather(weather_data):
    data = weather_data["data"]

    area_metadata = data["area_metadata"]
    item = data["items"][0]

    # Create a lookup dictionary for coordinates
    locations = {}

    for area in area_metadata:
        locations[area["name"]] = {
            "latitude": area["label_location"]["latitude"],
            "longitude": area["label_location"]["longitude"],
        }

    records = []

    for forecast in item["forecasts"]:
        area = forecast["area"]

        record = {
            "area": area,
            "latitude": locations[area]["latitude"],
            "longitude": locations[area]["longitude"],
            "forecast": forecast["forecast"],
            "api_timestamp": item["timestamp"],
            "update_timestamp": item["update_timestamp"],
            "valid_start": item["valid_period"]["start"],
            "valid_end": item["valid_period"]["end"],
        }

        records.append(record)

    return records

if __name__ == "__main__":
    weather_data = fetch_weather()
    records = transform_weather(weather_data)

    print("Number of records:", len(records))

    print("\nFirst record:")
    print(records[0])