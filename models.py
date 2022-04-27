import torch
from torch import nn
from torch.utils.data import Dataset
import torch.nn.functional as F
import random


class UserEncoder(nn.Module):
    def __init__(self):
        super(UserEncoder, self).__init__()
        self.aggregate = nn.Sequential(
            nn.Linear(11, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Linear(32, 16),
        )

    def forward(self, x):
        # Average/Max Pooling
        return self.aggregate(x).max(0)[0]

class Similarity(nn.Module):
    def __init__(self):
        super(Similarity, self).__init__() 
        self.song_encode = nn.Sequential(
            nn.Linear(11, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Linear(32, 16),
        )
        self.sim = nn.Sequential(
            nn.Linear(32, 16),
            nn.BatchNorm1d(16),
            nn.ReLU(),
            nn.Linear(16, 2),
            # nn.Softmax(1),
        )
    def forward(self, user_embed, track_feature):
        track_size = track_feature.shape[0]
        track_embed = self.song_encode(track_feature)
        x = torch.cat((user_embed.repeat(track_size, 1), track_embed), dim=1)
        similarity = self.sim(x)
        return similarity

class FullModel(nn.Module):
    def __init__(self):
        super(FullModel, self).__init__()
        self.aggregate = nn.Sequential(
            nn.Linear(11, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Linear(32, 16),
        )
        self.sim = nn.CosineSimilarity()

    def forward(self, embed_feature, track_feature):
        track_size = track_feature.shape[0]

        user_embed = self.aggregate(embed_feature).max(0)[0]
        track_embed = self.aggregate(track_feature)
        similarity = self.sim(user_embed.repeat(track_size, 1), track_embed)
        return similarity

from torch_geometric.nn import GCNConv, GATv2Conv, TransformerConv
class GCN(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = GCNConv(11, 16)
        self.conv2 = GCNConv(16, 32)
        self.conv3 = GCNConv(32, 64)

    def forward(self, x, edge_index):

        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, training=self.training)
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, training=self.training)
        x = self.conv3(x, edge_index)

        return x

class GAT(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = GATv2Conv(11, 16)
        self.conv2 = GATv2Conv(16, 32)
        self.conv3 = GATv2Conv(32, 64)

    def forward(self, x, edge_index):

        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, training=self.training)
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, training=self.training)
        x = self.conv3(x, edge_index)

        return x

class GTN(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = TransformerConv(11, 16)
        self.conv2 = TransformerConv(16, 32)
        self.conv3 = TransformerConv(32, 64)

    def forward(self, x, edge_index):

        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, training=self.training)
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, training=self.training)
        x = self.conv3(x, edge_index)

        return x