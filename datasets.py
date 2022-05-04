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
    
    
class SpotifyGraph2(Dataset):
    # Contrastive Learning: (track, track) similarity
    def __init__(self, feature_csv, user_like_json, id_map_json, p=1.0, transform=None):
        # P is the ratio of negative example/positive example
        track_feature = pd.read_csv(feature_csv, sep=',', header=None).values
        self.track_feature = torch.from_numpy(track_feature).float()
        self.track_count = track_feature.shape[0]
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
        self.user_count = len(self.user_list)
        self.track_list = list(self.id_map.keys())
        self.build_graph()
        self.second_order_adj()
        self.cache_track_neighbor()
        self.transform = transform

    def combination(self, iterable, r):
        pool = tuple(iterable)
        n = len(pool)
        if r > n:
            return
        indices = list(range(r))
        yield [pool[i] for i in indices]
        while True:
            for i in reversed(range(r)):
                if indices[i] != i + n - r:
                    break
            else:
                return
            indices[i] += 1
            for j in range(i+1, r):
                indices[j] = indices[j-1] + 1
            yield [pool[i] for i in indices]

    def build_graph(self):
        self.edge_index = torch.zeros((2, 62000)).long()
        user_feature = torch.zeros((self.user_count, 11))
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
            # user_feature[i] = embed_features
            # user_feature[i] = torch.rand(11)
            user_feature[i] = torch.zeros(11)

        self.edge_index = self.edge_index[:, :edge_count].to(DEVICE)
        self.edge_count = edge_count
        self.user_feature = user_feature
        self.x = torch.cat((self.track_feature, self.user_feature), dim=0).to(DEVICE)
        self.node_count = self.edge_index.max() + 1

    def cache_track_neighbor(self):
        # Cache Neighbors for efficiency consideration
        # This step is Space and time consuming, but better than
        # sameple everytime in __getitem__
        # 10000 times faster
        self.neighbors = {}
        for i in range(self.track_count):
            self.neighbors[i] = self.track_neighbor(i)

    def second_order_adj(self):
        row_a = self.edge_index[0].cpu().numpy()
        col_a = self.edge_index[1].cpu().numpy()
        data_a = np.ones_like(row_a)
        cscMatrixA = csc_matrix((data_a, (row_a, col_a)), shape=(self.node_count, self.node_count))
        self.adj2 = cscMatrixA * cscMatrixA

    def track_neighbor(self, idx):
        row = self.adj2.getrow(idx).toarray()[0]
        neighbor = np.nonzero(row)[0]
        return neighbor

    def __len__(self):
        return len(self.user_list)

    def sample_neg_right(self, neg_left):
        # neighbor = self.track_neighbor(neg_left)
        neighbor = self.neighbors[neg_left]
        right = random.randint(0, self.track_count)
        while right in neighbor:
            right = random.randint(0, self.track_count)
        return right

    def neg_tracks(self, tracks, count):
        # Not real negative, just not positive
        neg_lefts = random.choices(tracks, k=count)
        neg_left = [int(self.id_map[row]) for row in neg_lefts]
        neg_right = [self.sample_neg_right(row) for row in neg_left] # sample and check not neighbor
        return neg_left, neg_right

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        if self.transform is not None:
            track_features = self.transform(self.track_features)

        uid = self.user_list[idx]
        user_idx = idx + self.track_count # Index of user
        tracks = self.user_like[uid]
        if len(tracks) >= 10:
            embed_tracks = random.choices(tracks, k=10)
        else:
            embed_tracks = tracks
        embed_num = [int(self.id_map[embed_track]) for embed_track in embed_tracks]
        posi_samples = list(self.combination(embed_num, 2))
        left = [row[0] for row in posi_samples]
        right = [row[1] for row in posi_samples]

        length = len(left)
        neg_left, neg_right = self.neg_tracks(tracks, int(self.p * length))
        left = left + neg_left
        right = right + neg_right

        like_label = torch.ones(length)
        # negt_label = -torch.ones(len(neg_left))
        negt_label = torch.zeros(len(neg_left))
        label = torch.cat((like_label, negt_label), dim = 0).long().to(DEVICE)

        sample = {'user_idx': user_idx,
                  'left': left,
                  'right': right,
                  'label': label,
        }

        return sample 
