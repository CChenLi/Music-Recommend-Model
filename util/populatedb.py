from itertools import count
import boto3
import json
import numpy as np

dynamodb = boto3.resource('dynamodb')

def data2string(array):
    res = np.array2string(array, separator=', ').replace('\n', '')[1: -1]
    return res

def populate_track_feature():
    table = dynamodb.Table("track-features")
    embedding = np.genfromtxt("normalized_embedding.csv", delimiter=',')
    features = np.genfromtxt("id_map.csv", delimiter=',')
    with open("idx2tid.json", "r") as fd:
        idx2tid = json.load(fd)

    for idx in range(features.shape[0]):
        if idx % 1000 == 0:
            print("processed: ", idx)
        # buf = data2string(features[idx])
        # arr = np.fromstring(buf, sep=", ")
        item_dict = {
            "tid": idx2tid[str(idx)],
            "idx": str(idx),
            "embedding": data2string(embedding[idx]),
            "feature":data2string(features[idx]),
        }
        # print(item_dict)
        db_response = table.put_item(Item=item_dict)

def populate_user_like():
    count = 0
    table = dynamodb.Table("user-like")
    with open("user_like.json", "r") as fd:
        user_like = json.load(fd)
    for userId in user_like:
        if count % 100 == 0:
            print("Processed: ", count)
        count += 1
        raw_list = user_like[userId]
        if raw_list:
            like_list = ", ".join(user_like[userId])
            item_dict = {
                "userId": userId,
                "likelist": like_list
            }
            db_response = table.put_item(Item=item_dict)



if __name__=="__main__":
    populate_user_like()