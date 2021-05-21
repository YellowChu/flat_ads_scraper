import requests
import json
from pymongo import MongoClient
import time
import smtplib
from email.message import EmailMessage
import os

EMAIL_ADDRESS = 'sender@gmail.com'
EMAIL_PASSWORD = os.environ.get("email_sender_pw")

contacts = ['receiver1@mail.com', 'receiver2@email.com']

msg = EmailMessage()
msg['From'] = EMAIL_ADDRESS
msg['To'] = ', '.join(contacts)
msg['Subject'] = 'Nové byty z Sreality'

cluster = MongoClient(os.environ.get("MONGODB_CLIENT"))
db = cluster["inzeraty"]
collection = db["delete_later"]

url = "https://www.sreality.cz/api/cs/v2/estates?category_main_cb=1&category_sub_cb=4%7C5%7C6%7C7%7C8%7C9%7C10%7C11%7C12%7C16&category_type_cb=1&czk_price_summary_order2=0%7C5500000&locality_district_id=72&locality_region_id=14&per_page=100&tms=1617291082200&usable_area=50%7C10000000000"

# headers = {
#     "authority": "www.sreality.cz",
#     "method": "GET",
#     "path": "/api/cs/v2/estates?category_main_cb=1&category_sub_cb=4%7C5%7C6%7C7%7C8%7C9%7C10%7C11%7C12%7C16&category_type_cb=1&czk_price_summary_order2=0%7C5500000&locality_district_id=72&locality_region_id=14&per_page=60&tms=1617291082200&usable_area=50%7C10000000000",
#     "scheme": "https",
#     "accept": "application/json",
#     "accept-encoding": "gzip, deflate, br",
#     "accept-language": "en-US,en;q=0.9,cs;q=0.8",
#     "cookie": '__insp_nv=true; __insp_targlpt=Qnl0eSBrIHByb27DoWptdSBCcm5vLW3Em3N0byDigKIgU3JlYWxpdHkuY3o%3D; __insp_targlpu=aHR0cHM6Ly93d3cuc3JlYWxpdHkuY3ovaGxlZGFuaS9wcm9uYWplbS9ieXR5L2Jybm8%3D; __insp_wid=821249485; __insp_norec_sess=true; __insp_slim=1603125093948; sid=id=15618656102541074445|t=1577359397.592|te=1614184984.856|c=3D1E9D6C4629CE1C01BDC031C678A158; cmppersisttestcookie=1614184985040; __gfp_64b=bcfFZLPXgwkIYj54sCc5NNGrl4WrKnzTpVMzl2qVeE..M7|1578098073; euconsent-v2=CO99bTWPDk5O1D3ACBCSBSCsAP_AAEPAAITIF8wKwAAgAKAAgABUAC4AGQAQAAoABUAC0AGQANAAcwBEAEUAI4ASQAmABPACqAFuAMIAxAB-gEAAQQAhABEACxAGaAOIAdwBCACegFIALqAYEA04BrAEagI6ASCAm0BbgC8wF8gXnAYAAqABcADIAIAAaAA5gCIAIoATAAngBVADEAIQARAAsQBmgDuAIQARYAuoBgQDWAJBATaAvMAA.YAAAAAAAAAAA; ds=1YGOsrJI4fe3MzBWzZVSouFLGHGIVzxOihVr7fdNsF29fGwg3mFzLFhOXD7Nd5ZWTTxVBf; ps=1YGOsrJI4fe3MzBWzZVSouFLGHGIVzxOihVr7fdNsF29fGwg3mFzLFhOXD7Nd5ZWTTxVBf; lps=eyJfZnJlc2giOmZhbHNlLCJfcGVybWFuZW50Ijp0cnVlfQ.E0d4oA.rsGh6rD5Niczfmt6JT8uzOK3kRI; per_page=60; lastsrch="{\"category_main_cb\": \"1\"\054 \"locality_district_id\": \"72\"\054 \"tms\": \"1617291058587\"\054 \"category_sub_cb\": \"4|5|6|7|8|9|10|11|12|16\"\054 \"usable_area\": \"50|10000000000\"\054 \"czk_price_summary_order2\": \"0|5500000\"\054 \"per_page\": \"60\"\054 \"locality_region_id\": \"14\"\054 \"category_type_cb\": \"1\"}"; szncsr=1617287482',
#     "referer": "https://www.sreality.cz/hledani/prodej/byty/brno?velikost=2%2Bkk,2%2B1,3%2Bkk,3%2B1,4%2Bkk,4%2B1,5%2Bkk,5%2B1,6-a-vice,atypicky&plocha-od=50&plocha-do=10000000000&cena-od=0&cena-do=5500000",
# }

while True:
    # response = requests.get(url, headers=headers)
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

