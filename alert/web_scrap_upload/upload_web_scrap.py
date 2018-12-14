import json
import requests
from pprint import pprint

from geopy.geocoders import Nominatim

HOST_NAME = "http://localhost:8080"

NEWS_POST_REPORT_URL = HOST_NAME + "/cmp220/project/news_feed/news"


def post_news_report_api(creation_date, address, description, type_em):
    geo_locator = Nominatim(timeout=3)
    try:
        location = geo_locator.geocode(address)
        latitude = float(location.latitude)
        longitude = float(location.longitude)
    except:
        latitude = 0.0
        longitude = 0.0
    data = {
        "news": {
            "location":
                {"coordinates": [float(longitude), float(latitude)]},
            "email": str("admin@sjsu.edu"),
            "category": str(type_em),
            "address": str(address),
            "description": str(description),
            "creationDate": str(creation_date)
        }
    }
    pprint(data)
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url=NEWS_POST_REPORT_URL, data=json.dumps(data), headers=headers)
    print response.text
    return json.loads(response.text)


with open('scrapped_data.json') as data_file:
    data = json.load(data_file)
data_records = data["data"]
for data_record in data_records:
    post_news_report_api(data_record["creation_time"], data_record["address"],
                         data_record["description"], data_record["category"])
