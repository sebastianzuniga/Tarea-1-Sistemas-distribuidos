import redis
from pymongo import MongoClient

cache = redis.StrictRedis(host="localhost", port=6379, decode_responses=True)

#mongodb+srv://diego:diego@waze.5jx8mup.mongodb.net/?retryWrites=true&w=majority&appName=Waze
client = MongoClient("mongodb+srv://diego:diego@waze.5jx8mup.mongodb.net/?retryWrites=true&w=majority&appName=Waze")
db = client["waze"]
collection = db["eventos"]

def get_event(event_id):
    cached_event = cache.get(event_id)
    if cached_event:
        print(f"Evento obtenido del caché: {cached_event}")
        return cached_event

    event = collection.find_one({"_id": event_id})
    if event:
        cache.set(event_id, str(event), ex=3600) # aqui cambiar 3600 por el ttl dinamico
        print(f"Evento obtenido de MongoDB y guardado en caché: {event}")
        return event

    print("Evento no encontrado")
    return None



#* 
# ##DATOS
# 
# === Estadísticas Cache LRU en Redis CON  ===                                                                                                                                                                  
# trafficgen-1  | Hits: 236
# trafficgen-1  | Misses: 3204
# 
# Tamaño Cache: 10000                                                                                                                                                                                      
# trafficgen-1  | Hits: 385                                                                                                                                                                                                
# trafficgen-1  | Misses: 5055
# 
# trafficgen-1  | Esperando a que haya 10 000 eventos en MongoDB…

# trafficgen-1  | Tamaño Query: 200                                                                                                                                                                                        
# trafficgen-1  | Hits: 197                                                                                                                                                                                                
# trafficgen-1  | Misses: 1803
# 

# trafficgen-1  | Esperando a que haya 10 000 eventos en MongoDB…
# trafficgen-1  | ¡Ya hay suficientes eventos!
# trafficgen-1  | Iniciando tráfico Poisson λ=2.0
# trafficgen-1  |
# trafficgen-1  | === Estadísticas Cache LRU en Redis ===
# trafficgen-1  | Tamaño Query: 200
# trafficgen-1  | Hits: 339
# trafficgen-1  | Misses: 3661
# trafficgen-1 exited with code 0

# trafficgen-1  | Esperando a que haya 10 000 eventos en MongoDB…
# trafficgen-1  | ¡Ya hay suficientes eventos!
# trafficgen-1  | Iniciando tráfico Poisson λ=2.0                                                                                                                                                                          
# trafficgen-1  |                                                                                                                                                                                                          
# trafficgen-1  | === Estadísticas Cache LRU en Redis ===
# trafficgen-1  | Tamaño Query: 200                                                                                                                                                                                        
# trafficgen-1  | Hits: 468                                                                                                                                                                                                
# trafficgen-1  | Misses: 5532
# trafficgen-1 exited with code 0
    
# *#