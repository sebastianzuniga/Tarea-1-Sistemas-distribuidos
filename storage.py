from pymongo import MongoClient

class MongoStorage:
    def __init__ (self, uri = "mongodb+srv://diego:diego@waze.5jx8mup.mongodb.net/?retryWrites=true&w=majority&appName=Waze", db_name = "waze", collection_name = "eventos"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def insert_events(self, events):
        if events:
            self.collection.insert_many(events)
            print(f"Se insertaron {len(events)} eventos..")
        else:
            print("No hay eventos para insertar..")

        