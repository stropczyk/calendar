import os

from pymongo import MongoClient

username = os.getenv('MONGO_DB_USERNAME')
password = os.getenv('MONGO_DB_PASSWORD')
database = os.getenv('MONGO_DB_NAME')

db = MongoClient(f'mongodb://{username}:{password}@mongo:27017/{database}', authSource='admin')
