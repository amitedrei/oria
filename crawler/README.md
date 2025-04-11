## Getting Started

```
cd crawler
pip install uv
uv venv
source .venv/bin/activate
uv sync
````

## .env file
For the worker to work, .env file needs to be created and have the following values:
* GENIUS_KEY -> Genius API key
* MONGO_URL -> String to connect to the mongo **(mongodb+srv://user:password@url_of_mongo.ext)**
* MONGO_DB -> The name of the DB to be used inside the server.

## Execute
python main.py