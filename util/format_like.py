import json

if __name__=="__main__":
    with open("user_like.json", "r") as fd:
        original = json.load(fd)

    modified = {}
    idx = 22481 # number of tracks
    counter = 1
    for user in original:
        tracks = original[user]
        if tracks is not None: # request failure may result in None
            if len(tracks) >= 10:
                modified[str(idx)] = tracks
                idx += 1
                counter += 1
                print(counter)

    with open("user_like_graph.json", 'w') as fd:
        json.dump(modified, fd)

    with open("id_map.json", "r") as fd:
        tid2idx = json.load(fd)

    idx2tid = {}
    for tid in tid2idx:
        idx = tid2idx[tid]
        idx2tid[idx] = tid

    with open("idx2tid.json", 'w') as fd:
        json.dump(idx2tid, fd)
