from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB_NAME", "bird_pipeline")

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI nije postavljen u .env datoteci!")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

def get_species_collection():
    return db["species"]

if __name__ == "__main__":
    print("Spajam se na bazu:", DB_NAME)
    print("Postojeće kolekcije:", db.list_collection_names())



def get_audio_collection():
    return db["audio_files"]



def get_audio_files_collection():
    return db["audio_files"]

def get_classifications_collection():
    return db["classifications"]
