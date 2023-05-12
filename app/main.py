import asyncio
from fastapi import FastAPI, Request, Depends, HTTPException
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .db import Base, engine, SessionLocal
from .models import Url, Visit
from .cache import Cache

app = FastAPI()

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_cache():
    redis_cache = Cache()
    try:
        yield redis_cache
    finally:
        redis_cache.client.close()


@ app.get("/")
def home(req: Request):
    return {"message": "Hello world"}


@app.post("/shorten", status_code=201)
async def shorten_url(req: Request, 
                      db: Session = Depends(get_db), 
                      cache: Cache = Depends(get_cache)):
    body = await req.json()

    if "url" not in body:
        raise HTTPException(status_code=400, detail="URL is required")

    try:
        new_url = Url.create_unique_url(db, body["url"])
        cache.cache_url(new_url.shortcode, new_url.url)
    except IntegrityError:
        db.rollback()
        existing_url = Url.get_url_by_original_url(db, body["url"])

        if existing_url:
            return RedirectResponse(f"/urls/{existing_url.shortcode}",
                                    status_code=303)
        else:
            raise HTTPException(
                status_code=500,
                detail="An error occured while creating the URL")

    return {"location": f"/urls/{new_url.shortcode}"}


@app.get("/urls/{shortcode}")
async def redirect_url(shortcode: str, 
                       db: Session = Depends(get_db), 
                       cache: Cache = Depends(get_cache)):
    existing_url = cache.retrieve_url(shortcode)
    if existing_url:
        asyncio.create_task(Visit.create_visit_shortcode(db, shortcode))
        cache.extend_url(shortcode)
        return RedirectResponse(existing_url)

    existing_url = Url.get_url_by_shortcode(db, shortcode)

    if existing_url:
        asyncio.create_task(Visit.create_visit(db, existing_url))
        cache.cache_url(shortcode, existing_url.url)
        return RedirectResponse(existing_url.url)
    else:
        raise HTTPException(
            status_code=404, detail="There is no url with this shortcode")


@app.get("/urls/{shortcode}/stats")
async def url_stats(shortcode: str, db: Session = Depends(get_db)):
    url = Url.get_url_with_stats(db, shortcode)

    if url:
        return {
            "url": url.url,
            "created_at": url.created_at,
            "hits": len(url.visits)
        }
    else:
        raise HTTPException(
            status_code=404, detail="There is no url with this shortcode")
