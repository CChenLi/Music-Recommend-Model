# Music-Recommend-Model
Self-supervised GNN Music Recommendation Model with Data collected using [Spotify API](https://developer.spotify.com/).

## V3 Graph Transformer Contrastive Learning For Real-time Inference

### Considering the following mini example with only 3 users and 4 tracks/songs
**Build the dataset by [dataset.SpotifyGraph2](https://github.com/CChenLi/Music-Recommend-Model/blob/319c50305a1d241d67bccc529edb7dc231120c4d/src/datasets.py#L174) and the following the the visualization of the procedure**

<img src="https://user-images.githubusercontent.com/63531857/166812293-6149f381-9f76-4d2a-94bd-d1fa192d2094.png" width="600" />


**Using Contrastive self-supervised pipeline to train the Encoder on the dataset by, code in [trainG2](https://github.com/CChenLi/Music-Recommend-Model/blob/319c50305a1d241d67bccc529edb7dc231120c4d/src/train.py#L90) and [SpotifyGraph2.getitem](https://github.com/CChenLi/Music-Recommend-Model/blob/319c50305a1d241d67bccc529edb7dc231120c4d/src/datasets.py#L284)**


<img src="https://user-images.githubusercontent.com/63531857/166812296-407102a1-f470-45c3-99b1-93a60983cf01.png" width="600" />


**Efficient & Elegant Real-time Inference**. In 
Consider the following case when a user named **Jane** requests for a recommendation list. Our database indicated that Jane has n songs in her liked list:

<img src="https://user-images.githubusercontent.com/63531857/167088999-8714edf4-d979-4322-aaba-7aa234de8ca1.png" width="600" />


**Performance**
- **680ms** average response time on: minimum [AWS Lambda Serverless](https://aws.amazon.com/lambda/), User Like Graph contains **125300+** edges
  - **Comparing with V2**, which use exactly the same encoder and User Like Graph takes **410000ms** to run recommendation for one user. Because the it need to add the user into the graph and run the model on the **HUGE** graph.
  - Advantage is more obvious when graph grow even bigger. **The performance of V3 is not affect by graph size**

**Performance Explaination**
- The above algorithm elegantly obtains the most similar (in terms of **cosine similarity** in embedding space) songs to the user's existing favorite list through matrix operations .
- By directly using (track, track) similarity, The pipeline bypasses the computation of user embedding, which requires ML model service (Huge Overhead)
- By using the above method, I was able to put the time-consuming **machine learning computation offline** on schedule. And query the result in **real-time**



## V1 MLP
- User MLP to embed user and song according to the song in user's playlist.
- Use cos similarity, K-d tree in embedding space between user and song for recommendation
- **Problem** accuracy

## V2 Graph Transformer
- Convert data to (User-Song) [bipartite graph](https://en.wikipedia.org/wiki/Bipartite_graph), edge means "like". Run GNN to generate embedding
- Use cos similarity, K-d tree in embedding space between user and song for recommendation. Accuracy rocket!!!
- **Problem** When new user visit. Need to add user to the **HUGE** graph and re-run GNN to generate embedding for the user, super expansive.

## Data Collection
- All the data were collected through [Spotify API](https://developer.spotify.com/)
- Run **user2track.py** to generate following data:
  - **id_map.csv** the feature of each track
    ```
    ['acousticness'],['danceability'],['energy'],['instrumentalness'],['key'],['liveness'],['loudness'],['mode'],['speechiness'],['tempo'],['valence']
    ```
  - **id_map.json** map trackid to the row number of track's feature in **id_map.csv**
  - **user_like.json** map from userid to track ids the user likes 
  - run **format_like.py** to convert **id_map.json** to **id_map_graph.json**, which is required by GCN dataset
 
### Datasets
- `SpotifyDataset`: `__getitem__` will sample a user *A*. Return 
  - *E*: The set of songs that are used to generate the embedding of A. 
  - *T* The set songs in A's playlist along with songs that are not in A's playlist for training. 
  - The label to indicate which are in A's playlist.
  - User *LOSS(cos(F(E), G(T)), label)* to train the encoder *F* and *G*
  - - Training procedure defined in `train.trainF()`
 
- `SpotifyGraph`: The dataset will convert the `SpotifyDataset` into a [bipartite graph](https://en.wikipedia.org/wiki/Bipartite_graph) where nodes are users and songs. An edge indicate the song is in user's likelist. `__getitem__` will sample a user *A*. Return  
  - *I* the index of *A*, the position of *A*'s embedding generated by GNN
  - *T* the indexes of sampled songs that are either in *A*'s playlist of not, the ratio is determine by a parameter p
  - label indicate if the. song is in A's list
  - **Train**: First run GNN on the graph of `SpotifyGraph`, which gerate *x* the embedding of each node.
  - Then use *LOSS(cos(x[I], x[T]), label)* to optimize
  - Training procedure defined in `train.trainG()`
 
- `SpotifyGraph2`: Compute the second order adjacent matrix, which can efficiently check common user in O(1). `__getitem__` will sample a set songs. the Return  
  - *T* (SongA, SongB, label), sampled songs that are either like by a common user or not. label \in {1, -1}
  - **Train**: First run GNN on the graph of `SpotifyGraph`, which gerate *x* the embedding of each node.
  - Then use *LOSS(cos(x[T[0]], x[T[1]]), label)* to optimize
  - Training procedure defined in `train.trainG2()`
