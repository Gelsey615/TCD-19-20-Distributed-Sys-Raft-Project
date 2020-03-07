# TCD-19-20-Distributed-Sys-Raft-Project

## Set up
### First time clone
To initialize sqlite table
1. python manage.py migrate
2. python manage.py makemigrations room

### Edit .git/info/exclude to avoid committing pyc, sqlite and migration files
1. cd to your local folder of this git project
2. vim .git/info/exclude
3. add the following lines to the file and save:

  \*.pyc

  db.sqlite3

  \*/migrations/\*

## Functional Architecture -- Django Apps:

### 1. Election:
This process is ahead of any database related operation. Update or commit within the database can only happen when the group has a leader.

#### functions:
a. vote:
* Each node will have group member nodes' information when it first time joins the group. How to have this information will be explained in details in the Group Management part.
* Voting could be based on the member information or any other rules. This requires further research.
* This function is related to the url "vote". Once a node's "vote" url is hit, this function is executed.

b. follower - candidate - leader state:

* follower: a node starts as a follower with a default random timeout(tf) to wait for heartbeat from the leader. If timeout is due and no heartbeat arrives, this node enters candidate state. If heartbeat arrives, this node remains follower state and waits for another heartbeat or tf running out to become a candidate. Note there is a loop between tf and leader heartbeats. Please check raft website for a more direct visualization. This loop is related to the url "heartbeat". Once a follower's "heartbeat" url is hit, the loop restarts.

* candidate: send out http request to other nodes, request vote. If it gets the majority of the votes, this node becomes the leader. If it does not get the majority of the votes, it remains candidate state and keep request voting, until 1. it becomes the leader(this could happen when more nodes older than it die, if voting is somehow based on member age.) or 2. another node becomes leader.

* leader: send out heartbeat to followers to maintain stable. Heartbeat time interval(th) should be less than any node's tf. This can be achieved by, say, if the range for random default tf is 200ms-300ms, then th should be less than the shortest tf, which is 200ms.

#### url:
* vote: any candidate node can hit this url to request voting.
* heartbeat: the leader node hits this url to maintain stable state.

### 2. Room:
This module defines database related operation. After the group has a leader, database changes go through the leader. The leader first updates its own value in memory and then requests to update followers' values in memory. After all update requests to the followers return successfully, the leader commits and then requests to inform followers to commit.

#### inner function:
a. update:
* Update value in memory.
* This function is related to url "update". Once a node's "update" url is hit, this function is executed.
* Leader node executes this function because a client hits its "update" url, and followers execute this function because the leader hits their "update" url.

b. commit:
* Commit changes in memory to the database.
* For the follower nodes, this function is related to url "commit". Once a follower node's "commit" url is hit, this function is executed.
* For the leader node, this function's execution purely depends on the successful returns of previous update requests to the follower nodes.
* In conclusion, each node should have the "commit" url but how commit function is called depends on the role of the node.

c. log:
* Each node should log its update and commit operations.
* This function does not expose any url because it's a purely private operation in each node which requests no interaction with other nodes.

#### url:
* update: update room information, operations like adding new rooms, adding new booking orders, removing booking orders etc.
* commit: leader node hits this url to inform followers to execute commit function

### 3. Group Management:
to be continued...
