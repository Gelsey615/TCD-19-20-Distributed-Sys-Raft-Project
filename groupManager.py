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
        self.allNodesHost = {}
        self.allNodesPort = {}

        mainThread = threading.Thread(target = self.run_server)
        mainThread.start()

    def run_server(self):
        while True:
            print(self.allNodesHost)
            print(self.allNodesPort)
            time.sleep(5);
    # add node
    def exposed_addNode(self, newNodeIdx, newNodeHost, newNodePort):
        self.allNodesHost[newNodeIdx] = newNodeHost
        self.allNodesPort[newNodeIdx] = newNodePort
        for nodeIdx in self.allNodesHost:
            if nodeIdx == newNodeIdx:
                continue
            args = (newNodeIdx, newNodeHost, newNodePort, self.allNodesHost[nodeIdx], self.allNodesPort[nodeIdx])
            t = threading.Thread(target = self.notifyAddMember, args= args)
            t.start()

    def notifyAddMember(self, newNodeIdx, newNodeHost, newNodePort, host, port):
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
            t = threading.Thread(target = self.notifyRemoveMember, args= args)
            t.start()

    def notifyRemoveMember(self, oldNodeIdx, host, port):
        try:
            conn = rpyc.connect(host, port)
            conn.root.removeMember(oldNodeIdx)
        except Exception:
            print("Node", oldNodeIdx, "delete at", port, "failed")

    # get node list
    def exposed_getNodeList(self):
        return (self.allNodesHost, self.allNodesPort)

    # set leader
    def exposed_setLeader(self, leaderNodeHost, leaderNodePort):
        self.leaderHost = leaderNodeHost
        self.leaderPort = leaderNodePort

    # get leader
    def exposed_getLeader(self):
        return self.leaderHost, self.leaderPort

if __name__ == '__main__':
    from rpyc.utils.server import ThreadPoolServer
    port = sys.argv[1]
    server = ThreadPoolServer(Middleware(), port = int(port))
    server.start()
