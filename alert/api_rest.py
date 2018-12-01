import json

import requests

HOST_NAME = "http://localhost:8080"
USER_REGISTER_URL = HOST_NAME + "/cmp220/project/user"
USER_AUTHENTICATE_URL = HOST_NAME + "/cmp220/project/user/authenticate"

NEWS_POST_REPORT_URL = HOST_NAME + "/cmp220/project/news_feed/news"
NEWS_PUT_REPORT_URL = HOST_NAME + "/cmp220/project/news_feed/news"
NEWS_BY_ID_GET_REPORT_URL = HOST_NAME + "/cmp220/project/news_feed/news"
NEWS_GET_REPORT_URL = HOST_NAME + "/cmp220/project/news_feed/news/category"


def user_authenticate_api(email, password):
    data = {
        "email": str(email),
        "password": str(password),

    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url=USER_AUTHENTICATE_URL, data=json.dumps(data), headers=headers)
    print response.text
    return json.loads(response.text)


def user_register_api(name, email, password, street, city, zipcode, phone):
    data = {
        "userProfile": {
            "name": str(name),
            "email": str(email),
            "password": str(password),
            "street": str(street),
            "city": str(city),
            "zipcode": str(zipcode),
            "phone": str(phone)
        }
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url=USER_REGISTER_URL, data=json.dumps(data), headers=headers)
    print response.text
    return json.loads(response.text)


def post_news_report_api(email, address, description, image, type_em, longi, lati):
    data = {
        "news": {
            "location":
                {"coordinates": [float(longi), float(lati)]},
            "email": str(email),
            "category": str(type_em),
            "address": str(address),
            "description": str(description)
        }
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url=NEWS_POST_REPORT_URL, data=json.dumps(data), headers=headers)
    print response.text
    return json.loads(response.text)


def get_news_by_id_report_api(newsId):
    headers = {'Content-Type': 'application/json'}
    response = requests.get(url=NEWS_BY_ID_GET_REPORT_URL + "/" + newsId, headers=headers)
    print response.text
    return json.loads(response.text)


def update_news_by_id_report_api(newsId, description):
    data = {
        "newsId": str(newsId),
        "description": str(description)
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.put(url=NEWS_PUT_REPORT_URL, data=json.dumps(data), headers=headers)
    print response.text
    return json.loads(response.text)


def get_news_report_api(category, latest_time, sortOrder):
    headers = {'Content-Type': 'application/json'}
    queryParams = "?start=0&limit=100"
    response = None
    if category is not None:
        queryParams = queryParams + "&category=" + category
    if latest_time is not None:
        queryParams = queryParams + "&filter_time=las_min:" + latest_time
    if sortOrder is not None:
        queryParams = queryParams + "&sort=" + sortOrder
    response = requests.get(url=NEWS_GET_REPORT_URL + queryParams, headers=headers)
    print response.text
    return json.loads(response.text)
