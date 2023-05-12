# URL Shortener

This is my FastAPI based URL shortener service. It uses Redis as cache and Postgres as database.

## How to run

You can start the application with Docker, it requires `PORT`, `DB_URL`, `REDIS_HOST` and `REDIS_PORT` environment variables.

There is a Docker Compose file for development purposes, you can start the application with `docker-compose up`. It also starts a Redis and Postgres container.

## Tests

To run the test start up the application with Docker Compose. After the containers are running the tests can be with `docker compose exec api pytest`.

## Notes

- I used FastAPI's dependency injection to make it easier to change the database and cache implementations.
- I added the cache as for the redirect it's very important to be fast.
- Mocking the database and cahce client proven to be more difficult than I thought. I also had problems with running `pytest` on my local computer (because of some issues with global packages and packages in the virtual environment). As I had to run the tests in the Docker container it made sense to use the database and cahce containers as well.

