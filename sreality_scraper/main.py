import requests
import json
from pymongo import MongoClient
import time
import smtplib
from email.message import EmailMessage
import os

EMAIL_ADDRESS = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PW")

contacts = [os.environ.get("EMAIL_RECEIVER")]

msg = EmailMessage()
msg['From'] = EMAIL_ADDRESS
msg['To'] = ', '.join(contacts)
msg['Subject'] = 'Nové byty z Sreality'

cluster = MongoClient(os.environ.get("MONGODB_CLIENT"))
db = cluster["inzeraty"]
collection = db["delete_later"]

url = "https://www.sreality.cz/api/cs/v2/estates?category_main_cb=1&category_sub_cb=4%7C5%7C6%7C7%7C8%7C9%7C10%7C11%7C12%7C16&category_type_cb=1&czk_price_summary_order2=0%7C5500000&locality_district_id=72&locality_region_id=14&per_page=100&tms=1617291082200&usable_area=50%7C10000000000"

while True:
    response = requests.get(url)
    if response.status_code == 200:
        content = json.loads(response.content.decode("utf-8"))

        to_send = ""
        for estate in content["_embedded"]["estates"]:
            name = estate["name"]
            locality = estate["seo"]["locality"]
            price = estate["price"]
            hash_id = estate["hash_id"]

            size = ""
            plus_idx = name.find('+')
            if plus_idx == -1:
                continue
            if name[plus_idx+1] == "k":
                size = name[plus_idx-1] + "+" + "kk"
            else:
                size = name[plus_idx-1] + "+" + name[plus_idx+1]

            link = "sreality.cz/detail/prodej/byt/" + size + "/" + locality + "/" + str(hash_id)

            num_of_same_id = collection.count_documents({"_id": hash_id}, limit=1)
            if num_of_same_id == 0:
                post = {
                    "_id": hash_id,
                    "name": name,
                    "price": price,
                    "locality": estate["locality"],
                    "link": link,
                }

                collection.insert_one(post)

                to_send = to_send + name + "\n" + str(price) + ",-kč\n" + estate["locality"] + "\n" + link + "\n\n"

        if not to_send == "":
            print("sending")
            msg.set_content(to_send)
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                smtp.send_message(msg)
    else:
        print("Did not connect")

    time.sleep(30)

