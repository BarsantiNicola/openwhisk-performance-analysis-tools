from mongo_connection import mongo_connection
def create_energy(host:str, scenario_name):
    client = mongo_connection(host,27017,"test",scenario_name, True)
    results = []
    for invoker in [0, 1, 2, 3, 4]:
        data = client.fetch_data("invokers_memory", invoker)
        print("Data Fetched")
        power_per_container= 88/7
        for d in data:
            memory = int(d["memory"])
            if memory == 0:
                results.append(
                    {
                        "kind": "power_consumed",
                        "invoker":invoker,
                        "power": 0,
                        "timestamp": d["timestamp"]
                    })
            else:
                results.append(
                    {
                        "kind": "power_consumed",
                        "invoker":invoker,
                        "power": 100 + (memory-1)*power_per_container,
                        "timestamp": d["timestamp"]
                    })
    client.insert_many(results)
    sum = 0
    for result in results:
        sum += result["power"]
    results.append({"sum":sum})
    return results

def compute_energy(host:str, scenario_name:str):
    client = mongo_connection(host,27017,"test",scenario_name, True)
    results = []
    for invoker in [0,1,2,3,4]:
        composition = 0
        data = client.fetch_data("invokers_power", invoker)
        if len(data)>2:
            print("Data Fetched")
            last_occ=-1
            timestamps = []
            for d in data:
                if last_occ != -1:
                    composition += d["power"]*(d["timestamp"]-last_occ)
                last_occ = d["timestamp"]
                timestamps.append(last_occ)
            results.append(
                {
                "invoker": invoker,
                "energy":  composition/(max(timestamps)-min(timestamps))
                })
    return results