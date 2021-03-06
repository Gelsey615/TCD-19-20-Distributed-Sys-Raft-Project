import rpyc
import sys
import threading
import random
import sqlite3
from sqlite3 import Error
from threading import Timer
import os
import time

class Node(rpyc.Service):

    def __init__(self, argNodeIdx, argNodeHost, argNodePort):
        self.middlewareHost = "localhost"
        self.middlewarePort = 5000
        self.curNodeHost = argNodeHost
        self.curNodePort = argNodePort
        self.curNodeIdx = int(argNodeIdx)

        self.allNodesHost, self.allNodesPort = self.getAllMembers()
        self.numNodes = len(self.allNodesHost)

        self.joinGroup()
        self.leaderDbCopied = False

        # initial status setup
        self.currentState = "follower"
        self.currentTerm = 0
        self.votedFor = None
        self.currentLeader = None
        self.totalVotesCount = 0
        self.leaderTimer = None
        self.followerTimer = None
        self.electionTimer = None
        self.votesCheckTimer = None

        # create db file
        self.dbFile = f'pythonsqlite{self.curNodeIdx}.db'
        if not os.path.exists(self.dbFile):
            file = open(self.dbFile, 'w')
            file.close()
            #todo add reviving process from log

        mainThread = threading.Thread(target = self.run_server)
        mainThread.start()

    def run_server(self):
        while True:
            if self.currentState == 'follower':
                if self.followerTimer == None:
                    self.followerTimer = Timer(random.randint(20000, 30000)/float(10000), self.BecomeCandidate)
                    self.followerTimer.start()
            elif self.currentState == 'candidate':
                if self.electionTimer == None:
                    self.electionTimer = Timer(random.randint(10000, 20000)/float(10000), self.setupElection)
                    self.electionTimer.start()
                if self.votesCheckTimer == None:
                    self.votesCheckTimer = Timer(.2, self.candidateCheckVotes)
                    self.votesCheckTimer.start()
            elif self.currentState == 'leader':
                if self.leaderTimer == None:
                    self.leaderTimer = Timer(1.0, self.leaderAction)
                    self.leaderTimer.start()

    '''
        1.1 Code related to scenario when follower state ends
    '''
    def BecomeCandidate(self):
        print('follwer','node', self.curNodeIdx, 'term', self.currentTerm)
        print('follower','state', self.currentState)
        self.currentState = 'candidate'
        self.setupElection()

    '''
        1.1 ends
    '''

    '''
        1.2 Code related to scenario when current node is in candidate state
    '''

    def setupElection(self):
        print(self.allNodesHost)
        print(self.allNodesPort)
        self.currentTerm += 1
        self.totalVotesCount = 0
        self.totalVotesCount += 1
        self.votedFor = self.curNodeIdx

        if self.electionTimer != None:
            self.electionTimer.cancel()
            self.electionTimer = None
        if self.votesCheckTimer != None:
            self.votesCheckTimer.cancel()
            self.votesCheckTimer = None

        for nodeIdx in self.allNodesHost:
            if nodeIdx == self.curNodeIdx:
                continue
            args = (self.currentTerm, self.curNodeIdx, self.allNodesHost[nodeIdx], self.allNodesPort[nodeIdx])
            t = threading.Thread(target = self.startElection, args= args)
            t.start()

    def startElection(self, currentTerm, curNode, host, portNum):
        try:
            conn = rpyc.connect(host, portNum)
            vote = conn.root.requestVote(currentTerm, curNode)
            if vote == True:
                self.totalVotesCount += 1
        except Exception:
            print("Node", portNum, "crashed")

    def exposed_requestVote(self, term, candidateID):
        if term > self.currentTerm:
            self.voteForThisCandidate(term, candidateID)
            return True
        elif term == self.currentTerm:
            if self.votedFor == None:
                self.voteForThisCandidate(term, candidateID)
                return True
            else:
                return False
        elif term < self.currentTerm:
            return False

    def voteForThisCandidate(self, term, candidateID):
        self.totalVotesCount = 0
        self.currentState = 'follower'
        if self.followerTimer != None:
            self.followerTimer.cancel()
            self.followerTimer = None
        self.currentTerm = term
        self.votedFor = candidateID

    def candidateCheckVotes(self):
        if self.votesCheckTimer != None:
            self.votesCheckTimer.cancel()
            self.votesCheckTimer = None
        print('node', self.curNodeIdx, 'term', self.currentTerm)
        print('state', self.currentState)
        print(self.totalVotesCount)
        if self.totalVotesCount > self.numNodes/2:
            if self.electionTimer != None:
                self.electionTimer.cancel()
                self.electionTimer = None
            self.currentState = 'leader'
            self.currentLeader = self.curNodeIdx
            self.leaderAction()
    '''
        1.2 ends
    '''

    '''
        1.3 Code related to scenario when current node is leader
    '''
    def leaderAction(self):
        if self.leaderTimer != None:
            self.leaderTimer.cancel()
            self.leaderTimer = None
        for nodeIdx in self.allNodesHost:
            if nodeIdx == self.curNodeIdx:
                continue
            args = (self.currentTerm, self.curNodeIdx, nodeIdx, self.allNodesHost[nodeIdx], self.allNodesPort[nodeIdx])
            t = threading.Thread(target = self.sendHeartBeat, args= args)
            t.start()
        self.updateGroupLeader()

    def sendHeartBeat(self, currentTerm, leaderID, followerIdx, followerHost, followerPort):
        try:
            conn = rpyc.connect(followerHost, followerPort)
            respSuccess, respTerm = conn.root.maitainFollowerState(currentTerm, leaderID)
            print('Sent HeartBeat to', followerPort)
            if respSuccess == False:
                self.currentState = 'follower'
                self.currentTerm = respTerm
                self.votedFor = None
        except Exception:
            print("Node", followerPort, "crashed at send heart beat")
            # todo add retry count
            self.leaderDetectFailedNode(followerIdx)

    def exposed_maitainFollowerState(self, term, leaderID):
        if term > self.currentTerm:
            self.followerTimer.cancel()
            self.followerTimer = None
            self.currentTerm = term
            self.currentState = 'follower'
            self.currentLeader = leaderID
            self.votedFor = None
            if self.leaderDbCopied == False:
                self.copyDbFromLeader()
                self.leaderDbCopied = True
            return (True, self.currentTerm)
        elif term == self.currentTerm:
            self.followerTimer.cancel()
            self.followerTimer = None
            self.currentState = 'follower'
            self.currentLeader = leaderID
            if self.leaderDbCopied == False:
                self.copyDbFromLeader()
                self.leaderDbCopied = True
            return (True, self.currentTerm)
        else:
            return (False, self.currentTerm)
    '''
        1.3 ends
    '''

    '''
        1.4 Code related to group management
    '''

    def exposed_addMember(self, newMemIdx, newMemHost, newMemPort):
        self.allNodesHost[newMemIdx] = newMemHost
        self.allNodesPort[newMemIdx] = newMemPort
        self.numNodes = len(self.allNodesHost)


    def exposed_removeMember(self, failNodeIdx):
        del self.allNodesHost[failNodeIdx]
        del self.allNodesPort[failNodeIdx]
        self.numNodes = len(self.allNodesHost)

    def joinGroup(self):
        try:
            conn = rpyc.connect(self.middlewareHost, self.middlewarePort)
            conn.root.addNode(self.curNodeIdx, self.curNodeHost, self.curNodePort)
        except Exception:
            print("Node", self.curNodeIdx, "failed joining group")
        self.allNodesHost[self.curNodeIdx] = self.curNodeHost
        self.allNodesPort[self.curNodeIdx] = self.curNodePort
        self.numNodes = len(self.allNodesHost)

    def leaderDetectFailedNode(self, failNodeIdx):
        try:
            conn = rpyc.connect(self.middlewareHost, self.middlewarePort)
            conn.root.removeNode(self.curNodeIdx, failNodeIdx)
        except Exception:
            print("Node", failNodeIdx, "delete failed")
        del self.allNodesHost[failNodeIdx]
        del self.allNodesPort[failNodeIdx]
        self.numNodes = len(self.allNodesHost)

    def getAllMembers(self):
        try:
            conn = rpyc.connect(self.middlewareHost, self.middlewarePort)
            return conn.root.getNodeList()
        except Exception:
            print("Middleware", self.middlewarePort, "failed returning all members")

    def updateGroupLeader(self):
        try:
            conn = rpyc.connect(self.middlewareHost, self.middlewarePort)
            return conn.root.updateLeader(self.curNodeIdx, self.curNodeHost, self.curNodePort)
        except Exception:
            print("Middleware", self.middlewarePort, "failed setting leader")

    def exposed_is_leader(self):
        return self.currentState == 'leader'
    '''
        1.4 ends
    '''

    '''
        1.5 Code related to db operation
    '''
    def copyDbFromLeader(self):
        tableRoom = '''CREATE TABLE RoomInfo
                 (RoomID INT PRIMARY KEY     NOT NULL,
                 Type           INT    NOT NULL,
                 Floor          INT     NOT NULL);'''
        TableBookInfo = '''CREATE TABLE BookInfo
                 (TranID TEXT PRIMARY KEY     NOT NULL,
                 Name           TEXT    NOT NULL,
                 Phone          TEXT    NOT NULL,
                 Email          TEXT    NOT NULL,
                 RoomID         INT     NOT NULL,
                 StartT         INT64   NOT NULL,
                 EndT           INT64   NOT NULL,
                 FOREIGN KEY(RoomID) REFERENCES RoomInfo(RoomID));'''
        self.conn = sqlite3.connect(self.dbFile)
        self.conn.execute('drop table if exists RoomInfo')
        self.conn.execute('drop table if exists BookInfo')
        self.conn.execute(tableRoom)
        self.conn.execute(TableBookInfo)
        self.leaderDbConn = sqlite3.connect(f'pythonsqlite{self.currentLeader}.db')
        cursor = self.leaderDbConn.execute('SELECT * from RoomInfo')
        for row in cursor:
            self.conn.execute(f'INSERT INTO RoomInfo (RoomID,Type,Floor) \
              VALUES ({row[0]}, {row[1]}, {row[2]})')
        self.leaderDbConn.close()
        self.conn.commit()
        self.conn.close()

    def exposed_query(self, queryStr):
        self.conn = sqlite3.connect(self.dbFile)
        cursor = self.conn.execute(queryStr)
        result = ""
        for row in cursor:
            result += f'RoomId = {row[0]}, Type = {row[1]}, Floor = {row[2]}\n'
        self.conn.close()
        return result

    # client calls this function on Leader node, leader call this function on follower nodes
    # this is the first step of two-phase commit.
    # When all follower nodes return successfully, commitAsLeader is called
    def exposed_bookRoom(self, insertStr):
        self.dbInsert=insertStr

        if self.currentState == 'leader':
            commit = True
            for nodeIdx in self.allNodesHost:
                if nodeIdx == self.curNodeIdx:
                    continue
                try:
                    conn = rpyc.connect(self.allNodesHost[nodeIdx], self.allNodesPort[nodeIdx])
                    result = conn.root.bookRoom(insertStr)
                    if result == False:
                        print("Node", self.allNodesPort[nodeIdx], "commit failed")
                        commit = False
                        break
                except Exception:
                    print("Node", self.allNodesPort[nodeIdx], "commit failed")
                    commit = False
                    break
            if commit:
                return self.commitAsLeader()
            else:
                return False
        return True

    # leader calls this function to notify follower to commit
    def exposed_commitAsFollower(self):
        self.conn = sqlite3.connect(self.dbFile)
        #todo check if execute can happen.
        self.conn.execute(self.dbInsert)
        self.conn.commit()
        self.conn.close()
        return True

    # leader calls this function to notify follower to rollback the last transaction
    def exposed_rollbackAsFollower(self):
        self.conn = sqlite3.connect(self.dbFile)
        self.conn.rollback()
        self.conn.close()

    # Leader tells followers to rollback
    def rollbackAsLeader(self, NodesToRollback):
        self.conn = sqlite3.connect(self.dbFile)
        self.conn.rollback()
        self.conn.close()
        for nodeIdx in NodesToRollback:
            try:
                conn = rpyc.connect(self.allNodesHost[nodeIdx], self.allNodesPort[nodeIdx])
                conn.root.rollbackAsFollower()
            except Exception:
                print("Node", self.allNodesPort[nodeIdx], "rollback failed")

    # Leader tells followers to commit
    def commitAsLeader(self):
        self.conn = sqlite3.connect(self.dbFile)
        self.conn.execute(self.dbInsert)
        self.conn.commit()
        self.conn.close()
        allCommit = True
        committedNodes = []
        for nodeIdx in self.allNodesHost:
            if nodeIdx == self.curNodeIdx:
                continue
            try:
                conn = rpyc.connect(self.allNodesHost[nodeIdx], self.allNodesPort[nodeIdx])
                result = conn.root.commitAsFollower()
                if result == False:
                    print("Node", self.allNodesPort[nodeIdx], "commit failed")
                    allCommit = False
                    break
            except Exception:
                print("Node", self.allNodesPort[nodeIdx], "commit failed")
                allCommit = False
                break
            committedNodes.append(nodeIdx)
        if allCommit == False:
            self.rollbackAsLeader(committedNodes)
        return allCommit

    '''
        1.5 ends
    '''

if __name__ == '__main__':
    from rpyc.utils.server import ThreadPoolServer
    nodeIdx = sys.argv[1]
    host = sys.argv[2]
    port = sys.argv[3]
    server = ThreadPoolServer(Node(nodeIdx, host, port), port = int(port))
    server.start()
