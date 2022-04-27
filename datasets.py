"""
Author: CChenLi
"""

import torch
from torch.utils.data import Dataset
import json
import pandas as pd
import random

class SpotifyDataset(Dataset):
    """
    embed_feature : (N, 11) tensor, the feature of tracks to embed user with UID `user_list[i]` 
    train_feature : (K, 11) tensor, the feature of random sampled tracks includeing tracks liked by user_list[i] and negative samples
    label: (K) tensor, 1 indicate in the user's playlist, 0 indicate not in user's playlist
    """
    def __init__(self, feature_csv, user_like_json, id_map_json, p, device, transform=None):
        # p is the expectation of ratio of negative example/positive example
        track_feature = pd.read_csv(feature_csv, sep=',', header=None).values
        self.track_feature = torch.from_numpy(track_feature).float()
        self.user_like_json = user_like_json
        self.id_map_json = id_map_json
        self.device = device
        if p < 0:
          raise ValueError("p should be possitive")
        self.p = p
        with open(user_like_json, "r") as fd:
            self.user_like = json.load(fd)

        with open(id_map_json, "r") as fd:
            self.id_map = json.load(fd)

        self.user_list = list(self.user_like.keys())
        self.track_list = list(self.id_map.keys())
        self.transform = transform

    def __len__(self):
        return len(self.user_list)

    def neg_tracks(self, tracks):
        # Not real negative, just not positive
        count = int(random.randint(2, len(tracks)) * self.p)
        candidate = random.choices(self.track_list, k=count)
        negative = [x for x in candidate if x not in tracks]
        return negative

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        if self.transform is not None:
            track_features = self.transform(self.track_features)

        uid = self.user_list[idx]
        tracks = self.user_like[uid]
        if len(tracks) >= 10:
            embed_tracks = random.choices(tracks, k=10)
        else:
            embed_tracks = tracks

        embed_idx = [int(self.id_map[embed_track]) for embed_track in embed_tracks]
        embed_features = self.track_feature[embed_idx, :].to(self.device)

        like_tracks = random.choices(tracks, k=min(len(tracks), random.randint(2, len(tracks))))
        negt_tracks = self.neg_tracks(tracks)
        train_tracks = like_tracks + negt_tracks
        train_idx = [int(self.id_map[train_track]) for train_track in train_tracks]
        train_feature = self.track_feature[train_idx, :].to(self.device)

        like_label = torch.ones(len(like_tracks))
        negt_label = torch.zeros(len(negt_tracks))
        label = torch.cat((like_label, negt_label), dim = 0).long().to(self.device)

        sample = {'embed_feature': embed_features,
                  'train_feature': train_feature,
                  'label': label,
        }

        return sample 


class SpotifyGraph(Dataset):
    """
    user_idx: length (1) list. x[user_idx] is the embedding of the sampled user. Where x is the output of GNN.
    train_idx: length (k) list. x[train_idx] is the embedding of the sampled track. Where x is the output of GNN.
    label': (K) tensor, 1 indicate in the user's playlist, 0 indicate not in user's playlist
    """
    def __init__(self, feature_csv, user_like_json, id_map_json, p=1.0, transform=None):
        # p is the expectation of the ratio of negative example/positive example
        track_feature = pd.read_csv(feature_csv, sep=',', header=None).values
        self.track_feature = torch.from_numpy(track_feature).float()
        self.user_like_json = user_like_json
        self.id_map_json = id_map_json
        if p < 0:
          raise ValueError("p should be possitive")
        self.p = p

        with open(user_like_json, "r") as fd:
            self.user_like = json.load(fd)

        with open(id_map_json, "r") as fd:
            self.id_map = json.load(fd)

        self.user_list = list(self.user_like.keys())
        self.track_list = list(self.id_map.keys())
        self.build_graph()
        self.transform = transform

    def build_graph(self):
        self.edge_index = torch.zeros((2, 3200)).long()
        user_feature = torch.zeros((54, 11))
        edge_count = 0
        for user_number in self.user_like:
            tracks = self.user_like[user_number]
            for i, trackid in enumerate(tracks):
                track_number = int(self.id_map[trackid])
                self.edge_index[0, edge_count] = int(user_number)
                self.edge_index[1, edge_count] = track_number
                self.edge_index[0, edge_count+1] = track_number
                self.edge_index[1, edge_count+1] = int(user_number)
                edge_count += 2

            embed_idx = [int(self.id_map[embed_track]) for embed_track in tracks]
            embed_features = self.track_feature[embed_idx, :].mean(0)
            user_feature[i] = embed_features

        self.edge_index = self.edge_index[:, :edge_count].to(DEVICE)
        self.edge_count = edge_count
        self.user_feature = user_feature
        self.x = torch.cat((self.track_feature, self.user_feature), dim=0).to(DEVICE)

    def __len__(self):
        return len(self.user_list)

    def neg_tracks(self, tracks):
        # Not real negative, just not positive
        count = int(random.randint(2, len(tracks)) * self.p)
        candidate = random.choices(self.track_list, k=count)
        negative = [x for x in candidate if x not in tracks]
        return negative

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        if self.transform is not None:
            track_features = self.transform(self.track_features)

        uid = self.user_list[idx]
        user_idx = idx + 19704
        tracks = self.user_like[uid]
        if len(tracks) >= 10:
            embed_tracks = random.choices(tracks, k=10)
        else:
            embed_tracks = tracks

        like_tracks = random.choices(tracks, k=min(len(tracks), random.randint(2, len(tracks))))
        negt_tracks = self.neg_tracks(tracks)
        train_tracks = like_tracks + negt_tracks
        train_idx = [int(self.id_map[train_track]) for train_track in train_tracks]

        like_label = torch.ones(len(like_tracks))
        negt_label = torch.zeros(len(negt_tracks))
        label = torch.cat((like_label, negt_label), dim = 0).long().to(DEVICE)

        sample = {'user_idx': user_idx,
                  'train_idx': train_idx,
                  'label': label,
        }

        return sample 