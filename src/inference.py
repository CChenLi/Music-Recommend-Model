import json
import boto3
import csv
import numpy as np
import base64
import requests
import os

TOTAL_TRACK = os.environ['total_track']
client_creds = os.environ['client_creds'] # <clientid:clientsecret> from Spotify Application

s3_client = boto3.client('s3')
db_client = boto3.client('dynamodb')

idx2tid_data = (s3_client.get_object(Bucket='model-data-proj', Key='idx2tid.json')['Body']).read().decode('utf-8')
idx2tid = json.loads(idx2tid_data)

tid2idx_data = (s3_client.get_object(Bucket='model-data-proj', Key='tid2idx.json')['Body']).read().decode('utf-8')
tid2idx = json.loads(tid2idx_data)

def get_token():
    client_creds_64 = base64.b64encode(client_creds.encode())
    token_data = {
        'grant_type': 'client_credentials'
    }
    headers = {
        'Authorization': f'Basic {client_creds_64.decode()}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    res = requests.post('https://accounts.spotify.com/api/token', data=token_data, headers=headers).json()
    return res['access_token']

def get_info(trackids):
    api_key = get_token()
    url = "https://api.spotify.com/v1/tracks"
    url_params = {
        "ids": ",".join(trackids)
    }
    headers = {
        'Authorization': 'Bearer %s' % api_key,
        'Accept': 'applicatioin/json',
        'Content-Type': 'application/json'
    }
    response = requests.request('GET', url, headers=headers, params=url_params)
    tracks = response.json()["tracks"]
    res = []
    for track in tracks:
        musicUrl = track["preview_url"]
        if musicUrl is not None:
            if len(track["album"]["images"]) >= 0:
                imageUrl = track["album"]["images"][0]["url"]
            else:
                imageUrl = "https://scontent.fewr1-5.fna.fbcdn.net/v/t1.18169-1/17884567_10154570340077496_8996447567747887405_n.png?stp=dst-png_p148x148&_nc_cat=1&ccb=1-6&_nc_sid=1eb0c7&_nc_ohc=sb6jRnk6Ep4AX9IemqY&_nc_ht=scontent.fewr1-5.fna&oh=00_AT91ys0sCigXG90rAF2_y0PYp8CPc7wRuuokXyl71zEVDQ&oe=6298BB11"
            item = {
                "musicId": track["id"],
                "musicName": track["name"],
                "artistName" : track["artists"][0]["name"],
                "imageUrl" : imageUrl,
                "musicUrl": musicUrl
            }
            res.append(item)
    return res

'''
# Faster when total_track is small
def fetch_embedding():
    csvfile = s3_client.get_object(Bucket='model-data-proj', Key='normalized_embedding.csv')
    csv_data = csvfile['Body'].read().decode("utf-8").replace('\n', ', ')
    embedding = np.fromstring(csv_data, sep=", ").reshape(-1, 64)
    return embedding
'''
    
def get_user_like(userId):
    response = db_client.get_item(
        Key={
            'userId': {
                'S': userId,
            },

        },
        TableName='user-like',
        AttributesToGet=['likelist']
    )
    like_tids = response["Item"]["likelist"]["S"].split(", ")
    return like_tids
    
def get_embedding_batch(tids):
    keys = []
    visited = {}
    for tid in tids:
        key = {
            "tid": {
                "S": tid
            },
            "idx": {
                "S": tid2idx[tid]
            }
        }
        if tid not in visited:
            keys.append(key)
            visited[tid] = 1
    response = db_client.batch_get_item(
        RequestItems={
            'track-features': {
                'Keys': keys,
                'AttributesToGet': ['embedding'],
            }
        }
    )
    embeddings = response["Responses"]["track-features"]
    buf = ", ".join([track["embedding"]["S"] for track in embeddings])
    mat = np.fromstring(buf, sep=", ").reshape(-1, 64)
    return mat

'''
# Preserve Order but slow
def get_single_embedding(tid):
    response = db_client.get_item(
        Key={
            "tid": {
                "S": tid
            },
            "idx": {
                "S": tid2idx[tid]
            },
        },
        TableName='track-features',
        AttributesToGet=['embedding']
    )
    return response["Item"]["embedding"]["S"]

def get_embedding_matrix(tids):
    buf = ", ".join([get_single_embedding(tid) for tid in tids])
    mat = np.fromstring(buf, sep=", ").reshape(-1, 64)
    return mat
'''

def gen_candidate():
    candidates = np.random.randint(0, TOTAL_TRACK, size=100)
    candidates_tids = [idx2tid[str(idx)] for idx in candidates]
    right = get_embedding_batch(candidates_tids)
    return right

def recommendation(like_tids):
    user_embedding = get_embedding_batch(like_tids)
    right = np.concatenate([gen_candidate() for i in range(3)], axis=0).transpose()
    similarity = user_embedding @ right
    max_pool = similarity.max(0)
    rec_idx = np.argpartition(max_pool, -30)[-30:] # This is O(N), Amazing
    return rec_idx

def lambda_handler(event, context):
    userId = event["pathParameters"]["userId"]
    like_tids = get_user_like(userId)
    
    rec_idx = recommendation(like_tids)

    rec_tid = [idx2tid[str(idx)] for idx in rec_idx]

    musics = get_info(rec_tid)
    results = {
        "count": len(musics),
        "music": musics,
        "message": "fetch recommendation data successfully",
    }
    
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,OPTIONS,POST,PUT"
    }
    statusCode = 200
    
    return {
        'statusCode': statusCode,
        'headers': headers,
        'body': json.dumps(results)
    }
