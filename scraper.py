import requests
import sys
import os
from storage import MongoStorage
from pymongo import MongoClient

class MongoStorage:
    def __init__(self, url, db_name, collection_name):
        self.client = MongoClient(url)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def insert_events(self, events):
        if events:
            self.collection.insert_many(events)
            print(f"Se insertaron {len(events)} eventos.")
        else:
            print("No hay eventos para insertar.")

#MONGO_URI = "mongodb+srv://diego:diego@waze.5jx8mup.mongodb.net/?retryWrites=true&w=majority&appName=Waze"

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://diego:diego@waze.5jx8mup.mongodb.net/?retryWrites=true&w=majority&appName=Waze"
)


def GET_alertas (b, l, t, r): 
    response = requests.get("https://www.waze.com/live-map/api/georss?top="+t+"&bottom="+b+"&left="+l+"&right="+r+"&env=row&types=alerts,traffic,users")
    if response.status_code == 200:
        data = response.json()
        return data.get ("alerts", []) #Lista de alertas
    
    else: 
        print(f"Error obteniendo datos: {response.status_code}")
        return []
    
def main():
    total_alertas = 0
    mongo = MongoStorage(
        url = MONGO_URI,
        db_name = "waze",
        collection_name = "eventos"
    )

    if mongo.collection.count_documents({}) >= 10000:
        print("Ya existen 10.000 eventos en la base de datos. No se ejecuta el scraper.")
        return

    while (total_alertas < 10000):

        for i in range (10):
            for j in range (10):
                b = str(-33.56672099922156 + (i * ((33.56672099922156-33.33779053275497) /10 ))) 
                l = str(-70.77841542564796 + (j * ((70.77841542564796-70.49744008385109) /10 ))) 
                t = str(-33.33779053275497 - ((10-(i+1)) * ((33.56672099922156-33.33779053275497) / 10)))
                r = str(-70.49744008385109 - (((10-j+1)) * ((70.77841542564796-70.49744008385109) / 10)))

                alertas = GET_alertas (b, l, t, r)

                if not alertas:
                    print(f"No se encontraron alertas para i={i}, j={j}.")
                    continue

                #Guardar eventos en MongoDB
                print(f"Hay {len(alertas)} alertas")
                total_alertas += len(alertas)
                print(f"Hay {total_alertas} alertas en total")
                mongo.insert_events(alertas)

if __name__ == "__main__":
    main()                