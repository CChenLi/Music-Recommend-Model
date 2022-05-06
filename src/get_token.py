import base64
import requests

TOTAL_TRACK = os.environ['total_track'] # 22480
client_creds = os.environ['client_creds'] # <clientid:clientsecret> from Spotify Application

def get_info(trackids, api_key):
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
        if musicUrl is None:
            musicUrl = "No preview"
            no_prev += 1

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


if __name__=="__main__":
    trackids = ["4XrilgzGsMBrzAiUz3MePx", "7zKTQhQPCGnh2PgP93Pxsu"]
    api_key = get_token()
    track_info = get_info(trackids, api_key)
    print(track_info)