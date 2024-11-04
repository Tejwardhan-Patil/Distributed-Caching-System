from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import time

app = FastAPI()

# In-memory cache storage using dictionary for simplicity
cache_store: Dict[str, Dict] = {}

# Configuration for cache expiration in seconds
CACHE_EXPIRATION = 300  # Cache expiry set to 5 minutes

class CacheItem(BaseModel):
    key: str
    value: str
    ttl: Optional[int] = CACHE_EXPIRATION  # Default Time-To-Live (TTL) in seconds

class CacheResponse(BaseModel):
    key: str
    value: str
    ttl: int
    expires_in: int

def check_key_in_cache(key: str):
    if key in cache_store:
        cache_data = cache_store[key]
        current_time = time.time()
        if current_time > cache_data["expiry"]:
            del cache_store[key]
            return None
        else:
            return cache_data
    return None

@app.get("/")
def read_root():
    return {"message": "Cache API is running"}

@app.post("/cache", response_model=CacheResponse)
def add_cache(item: CacheItem):
    current_time = time.time()
    expiry_time = current_time + item.ttl
    
    cache_store[item.key] = {
        "value": item.value,
        "expiry": expiry_time,
        "ttl": item.ttl
    }
    
    return CacheResponse(
        key=item.key, 
        value=item.value, 
        ttl=item.ttl, 
        expires_in=int(expiry_time - current_time)
    )

@app.get("/cache/{key}", response_model=CacheResponse)
def get_cache(key: str):
    cache_data = check_key_in_cache(key)
    
    if cache_data is None:
        raise HTTPException(status_code=404, detail="Cache key not found or expired")
    
    current_time = time.time()
    return CacheResponse(
        key=key, 
        value=cache_data["value"], 
        ttl=cache_data["ttl"], 
        expires_in=int(cache_data["expiry"] - current_time)
    )

@app.put("/cache/{key}", response_model=CacheResponse)
def update_cache(key: str, item: CacheItem):
    cache_data = check_key_in_cache(key)
    
    if cache_data is None:
        raise HTTPException(status_code=404, detail="Cache key not found or expired")
    
    current_time = time.time()
    expiry_time = current_time + item.ttl
    
    cache_store[key] = {
        "value": item.value,
        "expiry": expiry_time,
        "ttl": item.ttl
    }
    
    return CacheResponse(
        key=key, 
        value=item.value, 
        ttl=item.ttl, 
        expires_in=int(expiry_time - current_time)
    )

@app.delete("/cache/{key}")
def delete_cache(key: str):
    if key in cache_store:
        del cache_store[key]
        return {"message": "Cache key deleted"}
    
    raise HTTPException(status_code=404, detail="Cache key not found")

@app.get("/cache/keys")
def list_keys():
    valid_keys = []
    current_time = time.time()
    
    for key, cache_data in cache_store.items():
        if current_time <= cache_data["expiry"]:
            valid_keys.append(key)
        else:
            del cache_store[key]  # Clean up expired cache keys
    
    return {"keys": valid_keys}

@app.delete("/cache")
def clear_cache():
    cache_store.clear()
    return {"message": "All cache keys cleared"}

@app.get("/cache/{key}/ttl")
def get_ttl(key: str):
    cache_data = check_key_in_cache(key)
    
    if cache_data is None:
        raise HTTPException(status_code=404, detail="Cache key not found or expired")
    
    current_time = time.time()
    return {"ttl": cache_data["ttl"], "expires_in": int(cache_data["expiry"] - current_time)}

@app.put("/cache/{key}/extend", response_model=CacheResponse)
def extend_ttl(key: str, ttl: Optional[int] = CACHE_EXPIRATION):
    cache_data = check_key_in_cache(key)
    
    if cache_data is None:
        raise HTTPException(status_code=404, detail="Cache key not found or expired")
    
    current_time = time.time()
    new_expiry = current_time + ttl
    cache_data["expiry"] = new_expiry
    cache_data["ttl"] = ttl
    
    return CacheResponse(
        key=key, 
        value=cache_data["value"], 
        ttl=ttl, 
        expires_in=int(new_expiry - current_time)
    )

# Cache statistics
@app.get("/cache/stats")
def cache_stats():
    total_keys = len(cache_store)
    current_time = time.time()
    
    expired_keys = 0
    for key, cache_data in cache_store.items():
        if current_time > cache_data["expiry"]:
            expired_keys += 1
    
    return {
        "total_keys": total_keys,
        "expired_keys": expired_keys,
        "active_keys": total_keys - expired_keys
    }

# Health check for monitoring tools
@app.get("/health")
def health_check():
    return {"status": "OK"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)