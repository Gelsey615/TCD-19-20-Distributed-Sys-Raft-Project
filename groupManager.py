import rpyc
import sys
import threading
from threading import Timer
import os
import time

class Middleware(rpyc.Service):

    def __init__(self):
        self.leaderHost = ""
        self.leaderPort = 0
        self.leaderIdx = -1
        self.checkLeaderTimer = None
        self.allNodesHost = {}
        self.allNodesPort = {}

        mainThread = threading.Thread(target = self.run_server)
        mainThread.start()

    def run_server(self):
        while True:
            if self.checkLeaderTimer == None:
                self.checkLeaderTimer = Timer(1.1, self.checkLeader)
                self.checkLeaderTimer.start()

    # add node
    def exposed_addNode(self, newNodeIdx, newNodeHost, newNodePort):
        self.allNodesHost[newNodeIdx] = newNodeHost
        self.allNodesPort[newNodeIdx] = newNodePort
        for nodeIdx in self.allNodesHost:
            if nodeIdx == newNodeIdx:
                continue
            args = (newNodeIdx, newNodeHost, newNodePort, self.allNodesHost[nodeIdx], self.allNodesPort[nodeIdx])
            t = threading.Thread(target = self.broadcastAddMember, args= args)
            t.start()

    def broadcastAddMember(self, newNodeIdx, newNodeHost, newNodePort, host, port):
        try:
            conn = rpyc.connect(host, port)
            conn.root.addMember(newNodeIdx, newNodeHost, newNodePort)
        except Exception:
            print("Node", newNodeIdx, "failed joining group")

    # remove node
    def exposed_removeNode(self, leaderIdx, oldNodeIdx):
        del self.allNodesHost[oldNodeIdx]
        del self.allNodesPort[oldNodeIdx]
        for nodeIdx in self.allNodesHost:
            if nodeIdx == leaderIdx:
                continue
            args = (oldNodeIdx, self.allNodesHost[nodeIdx], self.allNodesPort[nodeIdx])
            t = threading.Thread(target = self.broadcastRemoveMember, args= args)
            t.start()

    def broadcastRemoveMember(self, oldNodeIdx, host, port):
        try:
            conn = rpyc.connect(host, port)
            conn.root.removeMember(oldNodeIdx)
        except Exception:
            print("Node", oldNodeIdx, "delete at", port, "failed")

    # get node list
    def exposed_getNodeList(self):
        return (self.allNodesHost, self.allNodesPort)

    # set leader
    def exposed_updateLeader(self, leaderNodeIdx, leaderNodeHost, leaderNodePort):
        self.leaderIdx = leaderNodeIdx
        self.leaderHost = leaderNodeHost
        self.leaderPort = leaderNodePort
        if self.checkLeaderTimer != None:
            self.checkLeaderTimer.cancel()
            self.checkLeaderTimer = None

    # get leader
    def exposed_getLeader(self):
        return self.leaderHost, self.leaderPort

    # check leader:
    def checkLeader(self):
        print("check leader")
        if self.leaderHost != "":
            try:
                conn = rpyc.connect(self.leaderHost, self.leaderPort)
                if conn.root.is_leader() != True:
                    self.leaderHost = ""
                    self.leaderPort = 0
                    self.leaderIdx = -1
            except Exception:
                print("Leader", self.leaderPort, "connection failed.")
                del self.allNodesHost[self.leaderIdx]
                del self.allNodesPort[self.leaderIdx]
                for nodeIdx in self.allNodesHost:
                    args = (self.leaderIdx, self.allNodesHost[nodeIdx], self.allNodesPort[nodeIdx])
                    t = threading.Thread(target = self.broadcastRemoveMember, args= args)
                    t.start()
                self.leaderHost = ""
                self.leaderPort = 0
                self.leaderIdx = -1
                print(self.allNodesHost)
                print(self.allNodesPort)

        if self.checkLeaderTimer != None:
            self.checkLeaderTimer.cancel()
            self.checkLeaderTimer = None


if __name__ == '__main__':
    from rpyc.utils.server import ThreadPoolServer
    port = sys.argv[1]
    server = ThreadPoolServer(Middleware(), port = int(port))
    server.start()
