# Music-Recommend-Model
Graph Neural Network Music Recommendation Model with Data collected form [Spotify API](https://developer.spotify.com/)

### V3 Graph Transformer (No User Embedding, Real-time inference)
- Reduce problem comparing with V2
  - from `REQUEST -> RUN DEEP LEARNING MODEL -> response`, which requires decent server to run deep learning model
  - to `REQUEST -> QUERY DB -> response`, which can be achieved by minimal serveless [lambda](https://aws.amazon.com/lambda/)
- Same dataset as V2 (Check V2 to understand V3). But train with 
  - (SongA, SongB, 1) if SongA SongB are liked by a common user
  - (SongA, SongB, -1) if SongA SongB are not liked by a common user
- Recommend by *argmin_{song}-d(Liked_songs, song)*
- **EFFICIENT** sample SongA SongB that are not liked by a common user? Search? **NO!**
  - I have **sparse** addjacent matrix *M*, and I only need compute *M^2* *once* efficiently and reuse.
  - \mathbbm{1} M^2_{i, j} indicate song i and j are liked by a common user. That is O(1) optimized from O(N^2)
> Glad I still remember the Graph thoery class in sophomore. Super huge boost in efficiency

### V1 MLP
- User MLP to embed user and song according to the song in user's playlist.
- Use cos similarity, K-d tree in embedding space between user and song for recommendation
- **Problem** accuracy

### V2 Graph Transformer
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
