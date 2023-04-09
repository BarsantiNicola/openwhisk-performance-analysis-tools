from pymongo import MongoClient
from pymongo.results import InsertManyResult, InsertOneResult


class mongo_connection:
    def __init__(self, address: str = "localhost", port: int = 27017, database: str = "default",
                 collection: str = "default"):
        self.client = MongoClient(address, port)
        self.collection = self.client[database][collection]
        if self.collection.estimated_document_count() > 0:
            self.collection = None
            self.client.close()
            raise UnboundLocalError("Error, the given database/collection is already being used, abort to prevent "
                                    "inconsistent results")

    def __del__(self):
        self.collection = None
        self.client.close()

    def insert_one(self, data: dict) -> InsertOneResult:
        if self.collection is not None:
            return self.collection.insert_one(data)
        else:
            return InsertOneResult(0, False)

    def insert_many(self, data: list) -> InsertManyResult:
        if self.collection is not None:
            return self.collection.insert_many(data)
        else:
            return InsertManyResult([], False)
