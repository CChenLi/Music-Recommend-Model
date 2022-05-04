import torch
from torch import nn, optim

def trainF(epochs, model, train_dataset, val_dataset):
    optimizer = optim.Adam(model.parameters(), lr=1e-4, weight_decay=0.0001)
    criterion = nn.BCEWithLogitsLoss()
    loss = []
    for epoch in range(epochs):
        for i in range(0, len(train_dataset), 4):
            loss_batch = 0.0
            for idx in range(i, min(i+4, len(train_dataset))):
                data = train_dataset[idx]
                embed_feature = data['embed_feature']
                train_feature = data['train_feature']
                label = data['label']
                pred = model(embed_feature, train_feature)
                loss_batch += criterion(pred, label.float())

            optimizer.zero_grad()
            loss_batch.backward()
            optimizer.step()

        accuracy = 0.0
        for idx in range(len(val_dataset)):
            data = train_dataset[idx]
            embed_feature = data['embed_feature']
            train_feature = data['train_feature']
            label = data['label']
            pred = model(embed_feature, train_feature)
            pred[pred > 0.5] = 1.0
            pred[pred < 0.5] = 0.0
            accuracy += ((pred == label) * 1.0).mean()

        loss.append(loss_batch)
        print("Epoch {}/{}: LOSS: {:.6f} ACC: {:.6f}".format(epoch,
              epochs, loss_batch, accuracy / len(val_dataset)))
    return loss


def trainG(epochs, model, train_dataset, val_dataset):
    optimizer = optim.Adam(model.parameters(), lr=1e-3, weight_decay=0.0001)
    criterion = nn.BCEWithLogitsLoss()
    sim = nn.CosineSimilarity()
    loss = []
    for epoch in range(epochs):
        model.train()
        for i in range(0, len(train_dataset), 4):
            loss_batch = 0.0
            for idx in range(i, min(i+4, len(train_dataset))):
                data = train_dataset[idx]
                user_idx = data['user_idx']
                train_idx = data['train_idx']
                train_size = len(train_idx)
                label = data['label']
                embedding = model(train_dataset.x, train_dataset.edge_index)

                user_embed = embedding[user_idx]
                train_embed = embedding[train_idx]

                simlarity = sim(user_embed.repeat(train_size, 1), train_embed)

                loss_batch += criterion(simlarity, label.float())

            optimizer.zero_grad()
            loss_batch.backward()
            optimizer.step()

        model.eval()
        accuracy = 0.0
        for idx in range(len(val_dataset)):
            data = train_dataset[idx]
            user_idx = data['user_idx']
            train_idx = data['train_idx']
            train_size = len(train_idx)
            label = data['label']
            embedding = model(train_dataset.x, train_dataset.edge_index)
            user_embed = embedding[user_idx]
            train_embed = embedding[train_idx]
            pred = sim(user_embed.repeat(train_size, 1), train_embed)

            pred[pred > 0.5] = 1.0
            pred[pred < 0.5] = 0.0
            accuracy += ((pred == label) * 1.0).mean()

        loss.append(loss_batch)
        print("Epoch {}/{}: LOSS: {:.6f} ACC: {:.6f}".format(epoch,
              epochs, loss_batch, accuracy / len(val_dataset)))
    return loss

def trainG2(epochs, model, train_dataset, val_dataset):
  # Training pipeline for contrastive learning
  optimizer = optim.Adam(model.parameters(),lr=1e-4)
  criterion = nn.BCEWithLogitsLoss()
  # criterion = nn.MSELoss()
  # criterion = nn.CosineEmbeddingLoss()
  sim = nn.CosineSimilarity()
  loss = []
  for epoch in range(epochs):
    model.train()
    for i in range(0, len(train_dataset), 4):
      loss_batch = 0.0
      for idx in range(i, min(i+4, len(train_dataset))):
        data = train_dataset[idx]
        user_idx = data['user_idx']
        left_idx = data['left']
        right_idx = data['right']
        train_size = len(left_idx)
        label = data['label']
        embedding = model(train_dataset.x, train_dataset.edge_index)

        left_embed = embedding[left_idx]
        right_embed = embedding[right_idx]

        similarity = torch.sigmoid(sim(left_embed, right_embed))
        loss_batch += criterion(similarity, label.float())
        # loss_batch += criterion(left_embed, right_embed, label)
        # loss_batch = criterion(similarity, label.float())

      optimizer.zero_grad()
      loss_batch.backward()
      optimizer.step()
    
    model.eval()
    accuracy = 0.0
    for idx in range(len(val_dataset)):
      data = train_dataset[idx]
      user_idx = data['user_idx']
      left_idx = data['left']
      right_idx = data['right']
      train_size = len(left_idx)
      label = data['label']
      embedding = model(train_dataset.x, train_dataset.edge_index)
      left_embed = embedding[left_idx]
      right_embed = embedding[right_idx]
      pred = sim(left_embed, right_embed)
      pred[pred >= 0.0] = 1.0
      pred[pred < 0.0] = 0.0
      accuracy += ((pred == label) * 1.0).mean()
    
    loss.append(loss_batch) 
    print("Epoch {}/{}: LOSS: {:.6f} ACC: {:.6f}".format(epoch, epochs, loss_batch, accuracy / len(val_dataset)))
  return loss
