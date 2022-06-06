# Music-Recommend-Model
Self-supervised GNN Music Recommendation Model with Data collected using [Spotify API](https://developer.spotify.com/).
- AWS serverless backend is [Here](https://github.com/CChenLi/Music-Recommend-Lambda)
- Frontend is [Here](https://github.com/JoanWu5/cc-music-recommendation-frontend)
- Website hosted on [Music Recommendation](http://project-frontend222.s3-website-us-east-1.amazonaws.com/build2/index.html)

## V3 Graph Transformer Contrastive Learning For Real-time Inference

**Description:** Run GNN on most recent User-Song graph to update embedding for each song on schedule.   
**Training Objective:** The cos similarity between two songs' embedding represents the probability that they are neighbor.   
**Recommendation** Query the saved embedding the find songs that are most similar to the songs in user's liked list as recommendation on real-time.

> **Define:** Song-1 and Song-2 are neighbor if there exist at least one user, whose liked list contains both Song-1 and Song-2. Normal way to check if two songs are neighbor requires search through all user's liked list, which will take forever as the database grows bigger. I will use tricks from graph theory to solve this problem.

### Considering the following mini example with only 3 users and 4 tracks/songs
**Build the dataset by [dataset.SpotifyGraph2](https://github.com/CChenLi/Music-Recommend-Model/blob/319c50305a1d241d67bccc529edb7dc231120c4d/src/datasets.py#L174) and the following the the visualization of the procedure**

<img src="https://user-images.githubusercontent.com/63531857/166812293-6149f381-9f76-4d2a-94bd-d1fa192d2094.png" width="600" />

- **Optimization detail:** By computing and saving **B** using **sparse adjacent matrix multiplication**, we are able to find the neighbor of any song in O(1) time. Otherwise, we need to search through all user's likedlist to check if two songs are neighbor, that's O(N^2).
- Caching **B** makes sampling training data super efficient (See below).

**Using Contrastive self-supervised pipeline to train the Encoder on the dataset by, code in [trainG2](https://github.com/CChenLi/Music-Recommend-Model/blob/319c50305a1d241d67bccc529edb7dc231120c4d/src/train.py#L90) and [SpotifyGraph2.getitem](https://github.com/CChenLi/Music-Recommend-Model/blob/319c50305a1d241d67bccc529edb7dc231120c4d/src/datasets.py#L284)**


<img src="https://user-images.githubusercontent.com/63531857/166812296-407102a1-f470-45c3-99b1-93a60983cf01.png" width="600" />


**Efficient & Elegant Real-time Inference**. [inference.py](https://github.com/CChenLi/Music-Recommend-Model/blob/main/src/inference.py)
Consider the following case when a user named **Jane** requests for a recommendation list. Our database indicated that Jane has n songs in her liked list:

<img src="https://user-images.githubusercontent.com/63531857/167088999-8714edf4-d979-4322-aaba-7aa234de8ca1.png" width="600" />

The embedding is normalized, which **does no affect cosine distance**. And largely simplified operatioin.

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
All the data were collected through [Spotify API](https://developer.spotify.com/)

### Collect Data from Spotify
**2 main functions in [data_collection.py](https://github.com/CChenLi/Music-Recommend-Model/blob/main/util/data_collection.py)**
- [collect_more_user](https://github.com/CChenLi/Music-Recommend-Model/blob/3869d18d6930fd86c0da089ea90dfb1f3066fbf4/util/data_collection.py#L179)
  - RUN **DFS**: *user-playlist-user* to get more user ids and save to txt file.
- [collect_train_data](https://github.com/CChenLi/Music-Recommend-Model/blob/3869d18d6930fd86c0da089ea90dfb1f3066fbf4/util/data_collection.py#L187)
  - Expand to the neighbor users of users collected above and request their liked list, save to userid:[track ids] json file **user_like.json**
  - Collect 11 features of each song in the songs liked by users and save to **id_map.csv**. Features are
    ```
    ['acousticness'],['danceability'],['energy'],['instrumentalness'],['key'],['liveness'],['loudness'],['mode'],['speechiness'],['tempo'],['valence']
    ```
### Format the data
**Use [format_like.py]() to format the files. Required to build the Graph**
