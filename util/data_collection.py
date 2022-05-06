"""
Author: CChenLi
"""
from __future__ import print_function

import json
import requests
from time import gmtime, strftime
import json
from decimal import Decimal
import numpy as np
import random


# Expire in 1 hour, not security issue
playlist_token = "BQD81Kbt0rNIbq4mki4LD--_T0WEaDDfqA8tDV77dawiCKViBvJkUSGak2oluQdmyRvNNXV4slYk3PNUPAGvBVW91R9xNTaws1m_7u39HNhGD570YjsuSjNKHnoaKvFJ7YnEKrUdwqtrnFhghQzX1Iepxam_KQNCoSH7ibLTWqL7VcPgbbj-nHz5"

# Take advantage of GIL to simplify code
OFF_SET = 0
ID_MAP = {}
USER_LIKE = {}
VISITED = {}
UVISITED = {}

def request(url, api_key, url_params=None):
    url_params = url_params or {}
    headers = {
        'Authorization': 'Bearer %s' % api_key,
        'Accept': 'applicatioin/json',
        'Content-Type': 'application/json'
    }
    response = requests.request('GET', url, headers=headers, params=url_params)
    return response.json()


def Playlistid2OwnTrackids(playlistid):
    # Return:
    #   userid: the id for owner of the playlist
    #   trackids: list of ids for the tracks in the playlist
    uri = f"https://api.spotify.com/v1/playlists/{playlistid}"
    playlist = request(uri, playlist_token)
    # print(playlistid)
    if 'owner' in playlist:
        userid = playlist['owner']['id']
        tracks = playlist['tracks']['items']
        trackids = []
        for track in tracks:
            if track["track"] is not None:
                trackid = track['track']['id']
                if trackid is not None:
                    trackids.append(trackid)
        # only sample 30
        if len(trackids) > 30:
            trackids = random.choices(trackids, k=30)
        return True, userid, trackids
    else:
        print('no owner info')
        return False, "temp", "temp"


def getTrackFeature(trackids, csvfile):
    # For each track in trackids
    # Save the track features to id_map.csv as a row
    # ID_MAP maps trackid to row number of track features saved in id_map.csv
    global OFF_SET, ID_MAP

    uri = "https://api.spotify.com/v1/audio-features"
    if len(trackids) == 0:
        return
    if len(trackids) > 1:
        params = {
            'ids': ",".join(trackids)
        }
    else:
        params = {
            'ids': trackids[0]
        }
    tracks = request(uri, playlist_token, params)
    modified_trackids = [] # Increament list, should be optimized
    audio_features = tracks['audio_features']
    for i, audio in enumerate(audio_features):
        if audio is None: # May result in dangling pointer
            print("None audio feature: ", trackids[i])
        else:
            modified_trackids.append(trackids[i])
            new_row = [
                audio['acousticness'],
                audio['danceability'],
                audio['energy'],
                audio['instrumentalness'],
                audio['key'],
                audio['liveness'],
                audio['loudness'],
                audio['mode'],
                audio['speechiness'],
                audio['tempo'],
                audio['valence'],
            ]
            new_row = [str(x) for x in new_row]
            new_row = ",".join(new_row)
            new_row = new_row + "\n"
            if trackids[i] not in ID_MAP:
                csvfile.write(new_row)
                ID_MAP[trackids[i]] = str(OFF_SET)
                OFF_SET += 1  # Python is synchronous
    return modified_trackids


def generatePlaylist(user_id='smedjan'):
    global USER_LIKE
    # Return the playlist user_id has
    uri = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    param = {
        "limit": "50"
    }
    playlists = request(uri, playlist_token, param)['items']
    playlistIDs = [] # Increament list, should be optimized
    for playlist in playlists:
        if 'owner' in playlist:
            owner_id = playlist['owner']['id']
            if (owner_id not in VISITED):
                playlistIDs.append(playlist['id'])
                VISITED[owner_id] = 1
                # print(owner_id, playlist['name'])
    return playlistIDs


def generateUserid(UserIDs, user_id='smedjan'):
    UVISITED[user_id] = 1
    uri = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    param = {
        "limit": "50"
    }
    res = request(uri, playlist_token, param)
    if 'items' in res:
        playlists = res['items']
        for playlist in playlists:
            new_id = playlist['owner']['id']
            # print(playlist['name'])
            if new_id not in UserIDs:  # list is super slow we only run the script once
                UserIDs.append(new_id)
    else:
        print("No item found:")
        print(res)
    return UserIDs


def generateUserids(starting_uids):
    UserIDs = starting_uids
    count = 0
    for id in starting_uids:
        if id not in UVISITED:
            if count % 100 == 0:
                print("VISITED: ", count)
            UserIDs = generateUserid(UserIDs, id)
            count += 1
            if count  >= 1000:
                return UserIDs
    return UserIDs

def populate(playlistIDs, csvfile):
    # For each play list in playlistIDs
    # Get the Creator(userid): [tracks in playlist] for the playlist
    # Get and save the feature of each track in the playlist
    global USER_LIKE
    for playlistID in playlistIDs:
        flag, userid, trackids = Playlistid2OwnTrackids(playlistID)
        if flag:
            if userid not in USER_LIKE:
                modified_trackids = getTrackFeature(trackids, csvfile) # get feature and remove bad request
                USER_LIKE[userid] = modified_trackids
            else:
                print("Duplicate: ", userid)

##################
# Main Functions #
##################

def collect_more_user():
    # Run this recursively the get more userIDs
    UserIDs = ['smedjan', '1226836970', 'migo', 'michellekadir', 'robbanrapp', 'pitchfork', '125214440', 'billboard.com', 'sonymusicentertainment', 'legacysweden', 'jhsizemore', 'rsedit', 'efeghali', 'hammond', 'ulyssestone', 'liesen', 'jon', 'latenighttales', 'davidwhiting', 'thesoullounge', 'robbed', 'm6bcz0eqjib3kbg9v8nxv6k0f', 'absolutedance', 'myplay.com', 'sonymusicuk', 'sonymusicfinland', 'butr', 'upbeatcountry', 'osicktk', 'knowonelovesme', 'madonspurs', 'callestrandberg', 'jc415', '225maj3hqpdbqhxihtfoyphdy', 'mmabxr', '124705937', '1233988243', '1217796051', 'spotify', 'thesoundsofspotify', 'daftpunkofficial', 'steaktonight', 'j.matti', 'discoverthebluedot', '22tracks', 'djsashaofficial', 'p4w8wldecy9aww21upwa9n4dd', 'farmfestival', 'purenoiserecords', 'filtr', 'toplatino', 'sonymusicnl', 'sonymusic', 'mejoresplaylistsspotify', 'filtr.ca', 'bigbeatrecords', 'cleanbandit', 'kazuri', 'filtrmexico', 'sommerminner', 'filtrindia', 'filtrmiddleeast', '1174030805', 'fabianfarell', '6pfhllxfz62pdnjbqecw1ff4t', '21gozfqzp762vy7k7glyp62ka', 'anirudhravichander', 'filtr.travel', 'vl58sfb2jis143cc3mp7i6r2y', 'r3hab', 'wandwofficial', 'funk3y_', '1159036600', 'npzu1d85y6rkvqpucrshn0kgo', 'wedamnz', 'bkzhh44eczeqcxfrfan4cljl7', 'shebanimusic', 'pza6wtalem2no1o1lnnyby5j1', '11172008990', 'audition.', 'qabs236pr21ax4fgvu60lnubw', 'bigedmsounds', 'armadamusicofficial', 'arminvanbuurenofficial', '4djkwbl2dqnuybdxqvzht74nz', 'jonsinemusic', 'stmpdrcrds', '2rz2ohfn28ot3d7jn6rubpkr1', 'qzpjm0swzzeakc6hi9h1hoodf', '12122005472', 'antwandago', '1118377681', 'dondiablomusic', 'martingarrix', '1161105711', 'fezsfinest', 'xunemag', 'sanik007', 'soundplate', 'workhardplaylisthard', '2nightmgmt', '22djyrxnakv4iejuk3egwpviy', '119641708', 'alokofficial', '12142992301', 'topsify', 'hujfjm5lg1g6pdm9py6zcosyk', '1186407738', 'andrew_rayel', 'loudluxury', 'xj02qobbsw65rlu1ofw45nxih', 'ferrycorsten', 'arty_music', 'maxim_lany', 'assafmusic', 'tensnake', 'chicane_sunsets', 'autografmusic', 'sj_rm', 'jebgfwnhd24uziddyf52v4tqm', 'rupperink', 'futureofhouse', '11120667552', 'hardwellofficial', '1155541680', 'spinninrecordsofficial', 'deadmau5official', 'ovn4bzcasfbbgyw4h63z5xmpt', 'warnermusicus', 'datenightofficial', 'blacksunsetedm', 'sixdec', 'tvw7nqzof44nm6zrohy0sofnr', '1120975109', 'honkballer', 'katrienhert', 'edsheeran', 'g4hofficial', 'sunnawagemann', '1168522792', 'biranheplaylist', 'dirtylilblunt', '1136187203', '1119851226', 'palatje', 'digsternl', 'coldplay__', 'revealedrec', 'arjan1978', '1110214374', 'sonymusicthelegacy', '114130747', '1175525415', 'mau5trapofficial', 'gravityroomrec', 'playlistme.nl', 'topsify_kids', 't8q714ro6innqo9ouvppll224', 'ladertons', 'sharifsx', 'jyyb3vzozc5pr8kpuxta7kaig', 'rachelbrathen', '1245625361', '1162081443', 'tommywl1', 'nederlandse_top_40', 'ruudjansen', 'paulonings', 'festileaks', '3fm', 'pmamrecordings', 'musicbox_online', 'michellus', 'rush87', 'digimuziek', '112921300', '1117257589', 'janpieter1985', 'gunnarrt', 'pleinvrees', '121934137', 'hanse.ekkers', 'lynnn123', '1259553058', 'pelle.andersson', 'kent1337', 'ryan-o', 'biljartsjaak', '1117903005', 'guardianmusic', '123694088', '129592975', 'universalmusiclegends', '1133856070', 'ruudschilders', 'twannette', 'radio2nl', '1111430149', 'fiirw94txkud5p8cxu45ki6b3', 'kontorrecordsofficial', '1131621098', '3voor12', 'kixass456', 'gerardsim2', 'peter_ka', 'everhard1993', '116099541', 'kieron', 'sam85uk', 'yaikz!', 'pairofladiesqq', 'mcif1ae7o9ngih9dngqg3ptd8']
    UserIDs = generateUserids(UserIDs)
    print(UserIDs)
    with open('users.txt', 'w') as fd:
        fd.write('\n'.join(UserIDs))

def collect_train_data():
    csvfile = open("id_map.csv", 'w')
    with open('users.txt', 'r') as fd:
        Uids = fd.read().split('\n')
    print("User Count: ", len(Uids))

    for uid in Uids[:600]:
        print("Processing Likelist for: ", uid)
        playlistIDs = generatePlaylist(uid)
        populate(playlistIDs, csvfile)

    csvfile.close()

    with open("id_map.json", 'w') as fd:
        json.dump(ID_MAP, fd)

    with open("user_like.json", 'w') as fd:
        json.dump(USER_LIKE, fd)

def collect_track_info():
    with open("id_map.json", "r") as fd:
        tid2idx = json.load(fd)
    count = 0
    no_prev = 0
    music_info = {}
    for tid in tid2idx:
        if count % 1000 == 0:
            print("processed: ", count)
        count += 1
        uri = f"https://api.spotify.com/v1/tracks/{tid}"
        res = request(uri, playlist_token)
        musicUrl = res["preview_url"]
        if musicUrl is None:
            musicUrl = "No preview"
            no_prev += 1

        if len(res["album"]["images"]) >= 0:
            imageUrl = res["album"]["images"][0]["url"]
        else:
            imageUrl = "https://scontent.fewr1-5.fna.fbcdn.net/v/t1.18169-1/17884567_10154570340077496_8996447567747887405_n.png?stp=dst-png_p148x148&_nc_cat=1&ccb=1-6&_nc_sid=1eb0c7&_nc_ohc=sb6jRnk6Ep4AX9IemqY&_nc_ht=scontent.fewr1-5.fna&oh=00_AT91ys0sCigXG90rAF2_y0PYp8CPc7wRuuokXyl71zEVDQ&oe=6298BB11"
        item = {
            "musicId": tid,
            "musicName": res["name"],
            "artistName" : res["artists"][0]["name"],
            "imageUrl" : imageUrl,
            "musicUrl": musicUrl
        }
        music_info[tid] = item

    print(f"{no_prev}/{count} songs has no preview_url")
    with open("music_detail.json", 'w') as fd:
        json.dump(music_info, fd)

if __name__=="__main__":
    collect_track_info()