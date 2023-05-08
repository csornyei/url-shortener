import os
from fastapi import FastAPI, Request
import sqlalchemy
import redis

app = FastAPI()

db_engine = sqlalchemy.create_engine(os.getenv("DB_URL"))
r = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"))


@ app.get("/")
def home(req: Request):
    return {"message": "Hello world"}
