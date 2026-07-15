import os
from pymongo import MongoClient

def main():
    mongo_uri = "mongodb://localhost:27017/minpro"
    print("Connecting to:", mongo_uri)
    client = MongoClient(mongo_uri)
    db = client.get_default_database()
    print("Database name:", db.name)
    
    print("\nUsers in database:")
    users = list(db.users.find())
    for u in users:
        print(u)

if __name__ == "__main__":
    main()
