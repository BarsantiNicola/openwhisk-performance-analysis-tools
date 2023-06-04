import pymongo
from pymongo import MongoClient
from pymongo.results import InsertManyResult, InsertOneResult


class mongo_connection:
    def __init__(self, address: str = "localhost", port: int = 27017, database: str = "default",
                 collection: str = "default", read: bool = False):
        self.client = MongoClient(address, port)
        self.collection = self.client[database][collection]
        if self.collection.estimated_document_count() > 0 and not read:
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

    def fetch_data(self, kind: str, invoker:int=0, action:str="") -> list[dict]:
        match kind:
            case "invokers_power":
                return list(self.collection.find({"kind":  "power_consumed", "invoker": invoker}, {})
                            .sort("timestamp", pymongo.ASCENDING))
            case "minimum_response_time":
                return list(self.collection.find({"kind": "local_response_time"}, {})
                            .sort("timestamp", pymongo.ASCENDING))
            case "service_response_time":
                return list(self.collection.find({"kind": "service_response_time"}, {})
                            .sort("timestamp", pymongo.ASCENDING))
            case "normalized_service_response_time":
                return list(self.collection.find({"kind": "normalized_service_time"}, {})
                            .sort("timestamp", pymongo.ASCENDING))
            case "client_response_time":
                return list(self.collection.find({"kind": "global_response_time"}, {})
                            .sort("timestamp", pymongo.ASCENDING))
            case "data_exchange":
                return list(self.collection.find({"kind": "state-registry-data"}, {})
                            .sort("timestamp", pymongo.ASCENDING))
            case "snapshot_info":
                return list(self.collection.find({"staleActivationNum": {"$exists": 1}}, {})
                            .sort("timestamp", pymongo.ASCENDING))
            case "supervisor_info":
                print(action)
                return list(self.collection.find({"kind": "supervisor-state", "action": action }, {})
                            .sort("timestamp", pymongo.ASCENDING))
            case "container_creation":
                return list(self.collection.find({"kind": "container-created"}, {})
                            .sort("timestamp", pymongo.ASCENDING))
            case "invokers_memory":
                return list(self.collection.find({"kind": "invokers-container-counter", "invoker": invoker}, {})
                            .sort("timestamp", pymongo.ASCENDING))
            case "normalized_service_time":
                return list(self.collection.find({"kind": "normalized_service_time"}, {})
                    .sort("timestamp", pymongo.ASCENDING))
            case "all":
                return self.collection.find()
