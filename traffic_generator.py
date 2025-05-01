import os, time, random
import numpy as np
from datetime import datetime, timedelta
from pymongo import MongoClient, UpdateOne
import redis
#import cache

# Configs desde env
MONGO_URI    = os.getenv("MONGO_URI")
REDIS_HOST   = os.getenv("REDIS_HOST", "redis")
REDIS_PORT   = int(os.getenv("REDIS_PORT", 6379))
MAX_EVENTS   = int(os.getenv("TRAFFIC_EVENTS", 10000))
SAMPLE_SIZE  = int(os.getenv("TRAFFIC_SAMPLE_SIZE", 20))
BASE_TTL     = int(os.getenv("TRAFFIC_BASE_TTL", 50))
RATE         = float(os.getenv("TRAFFIC_RATE", 2.0))
QUERIES      = int(os.getenv("TRAFFIC_QUERIES", 1000))

# Conexiones
mongo_client = MongoClient(MONGO_URI)
client = MongoClient("mongodb+srv://diego:diego@waze.5jx8mup.mongodb.net/?retryWrites=true&w=majority&appName=Waze")
db           = client["waze"]
col          = db["eventos"]
rds          = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
#cache = redis.StrictRedis(host="localhost", port=6379, decode_responses=True)

def wait_for_events():
    print("Esperando a que haya 10 000 eventos en MongoDB…")
    while col.count_documents({}) < MAX_EVENTS:
        print(f"  Actualmente: {col.count_documents({})}")
        time.sleep(1)
    print("¡Ya hay suficientes eventos!")

def assign_ttl(events):
    now = datetime.now()
    ops = []
    ttls = []
    for ev in events:
        ttl = random.randint(BASE_TTL//2, BASE_TTL*2)
        expires = now + timedelta(seconds=ttl)
        ops.append(UpdateOne({"_id": ev["_id"]}, {"$set": {"expires_at": expires}}))
        ttls.append(ttl)
    if ops:
        col.bulk_write(ops)
    return ttls

#Mejorar
def get_event(event_id, ttl):
    cached_event = str(event_id["_id"])

    street = str(event_id.get("street", "Desconocido"))
    event_type = str(event_id.get("type", "Desconocido") )

    if cached_event:
        print(f"Evento generado: ID: {cached_event}, CALLE: {street}, TIPO: {event_type}")
        return cached_event

    event = col.find_one({"_id": event_id})
    if event:
        
        rds.set(event_id, str(event), ex=ttl) # aqui cambiar 3600 por el ttl dinamico
        print(f"Evento obtenido de MongoDB y guardado en caché: {event}")
        return event

    print("Evento no encontrado")
    return None
    

if __name__ == "__main__":
    wait_for_events()

    print(f"Iniciando tráfico Poisson λ={RATE}")
    for i in range(QUERIES):
        # 1) muestreo
        events = list(col.aggregate([{"$sample": {"size": SAMPLE_SIZE}}]))
        # 2) asignar TTL
        ttls = assign_ttl(events)
        # 3) cache + contadores
        for ev, ttl in zip(events, ttls):
            get_event(ev, ttl)
        time.sleep(np.random.exponential(1.0/RATE))

    # Al terminar, mostra hits/misses
    hits   = int(rds.get("cache:hits")   or 0)
    misses = int(rds.get("cache:misses") or 0)
    print(f"\n=== Estadísticas Cache RANDOM en Redis ===")
    print(f"Tamaño Query: {QUERIES}") #experimental
    print(f"Hits: {hits}")
    print(f"Misses: {misses}")
    print("-----------------------")
    total_requests = hits + misses
    if total_requests > 0:
        hit_percent = (hits / total_requests) * 100  # Porcentaje de hits
        print(f"Porcentaje de hits: {hit_percent:.2f}%")
    else:
        print("No hay registros de hits o misses.")


#tamaño del cache depende del generador de trafico

#docker exec -it tarea1v2-redis-1 bash
#root@c4420e9d0982:/data# redis-cli
# 127.0.0.1:6379> get cache:hits
# 127.0.0.1:6379> get cache:misses