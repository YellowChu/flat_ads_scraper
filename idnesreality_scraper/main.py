import requests
from bs4 import BeautifulSoup
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
msg['Subject'] = 'Nové byty z Reality Idnes'

cluster = MongoClient(os.environ.get("MONGODB_CLIENT"))
db = cluster["inzeraty"]
collection = db["delete_later"]

pageone = "https://reality.idnes.cz/s/prodej/byty/cena-do-5500000/brno/?s-qc%5BsubtypeFlat%5D%5B0%5D=2k&s-qc%5BsubtypeFlat%5D%5B1%5D=21&s-qc%5BsubtypeFlat%5D%5B2%5D=3k&s-qc%5BsubtypeFlat%5D%5B3%5D=31&s-qc%5BsubtypeFlat%5D%5B4%5D=4k&s-qc%5BsubtypeFlat%5D%5B5%5D=41&s-qc%5BsubtypeFlat%5D%5B6%5D=5k&s-qc%5BsubtypeFlat%5D%5B7%5D=atypical&s-qc%5BusableAreaMin%5D=50"
pagetwo = "https://reality.idnes.cz/s/prodej/byty/cena-do-5500000/brno/?s-qc%5BsubtypeFlat%5D%5B0%5D=2k&s-qc%5BsubtypeFlat%5D%5B1%5D=21&s-qc%5BsubtypeFlat%5D%5B2%5D=3k&s-qc%5BsubtypeFlat%5D%5B3%5D=31&s-qc%5BsubtypeFlat%5D%5B4%5D=4k&s-qc%5BsubtypeFlat%5D%5B5%5D=41&s-qc%5BsubtypeFlat%5D%5B6%5D=5k&s-qc%5BsubtypeFlat%5D%5B7%5D=atypical&s-qc%5BusableAreaMin%5D=50&page=1"
pagethree = "https://reality.idnes.cz/s/prodej/byty/cena-do-5500000/brno/?s-qc%5BsubtypeFlat%5D%5B0%5D=2k&s-qc%5BsubtypeFlat%5D%5B1%5D=21&s-qc%5BsubtypeFlat%5D%5B2%5D=3k&s-qc%5BsubtypeFlat%5D%5B3%5D=31&s-qc%5BsubtypeFlat%5D%5B4%5D=4k&s-qc%5BsubtypeFlat%5D%5B5%5D=41&s-qc%5BsubtypeFlat%5D%5B6%5D=5k&s-qc%5BsubtypeFlat%5D%5B7%5D=atypical&s-qc%5BusableAreaMin%5D=50&page=2"

def realityIdnesScrapper(page):
    to_send = ""
    response = requests.get(page)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        adverts = soup.find_all("div", {"class": "c-products__inner"})
        advertInfo = ""
        link = ""
        idnes_id = ""
        counter = 1
        for advert in adverts:
            if not str(advert) == "\n":
                advertInfo = advert.text
                advertInfo = advertInfo.replace("\n", "")
                advertInfo = advertInfo.replace("\t", " ")
                advertInfo = advertInfo.replace("\xa0", "")
                advertInfo = ' '.join(advertInfo.split())

                for a in advert.find_all("a", href=True):
                    link = "reality.idnes.cz" + a["href"]
                    toCut = link.split('/')[-1]
                    link = link.replace(toCut, "")
                    idnes_id = link.split('/')[-2]

            if not link == "":
                numOfSameId = collection.count_documents({"_id": idnes_id}, limit=1)
                if numOfSameId == 0:
                    post = {
                        "_id": idnes_id,
                        "info": advertInfo,
                        "link": link,
                    }

                    collection.insert_one(post)
                    to_send = to_send + advertInfo + "\n" + link + "\n\n"

    return to_send

while True:
    advertsPageOne = realityIdnesScrapper(pageone)
    advertsPageTwo = realityIdnesScrapper(pagetwo)
    advertsPageThree = realityIdnesScrapper(pagethree)

    to_send = advertsPageOne + advertsPageTwo + advertsPageThree

    if not to_send == "":
        print("sending")
        msg.set_content(to_send)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

    time.sleep(30)
