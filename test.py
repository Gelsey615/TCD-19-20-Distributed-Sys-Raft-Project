import rpyc
import sys
import threading

class Client():
    def __init__(self):
        self.leader = 0
        self.middlewareHost = "localhost"
        self.middlewarePort = 5000
        self.allNodesHost, self.allNodesPort = self.getAllMembers()
        print(self.allNodesHost)
        print(self.allNodesPort)
        self.numNodes = len(self.allNodesHost)
        self.test1()


    def connect(self, host, port):
        conn = rpyc.connect(host, port)
        if conn.root.is_leader():
            self.leader = self.leader + 1
            print(self.leader)
            print(port)
        else:
            print("follower", port)

    def getAllMembers(self):
        try:
            conn = rpyc.connect(self.middlewareHost, self.middlewarePort)
            return conn.root.getNodeList()
        except Exception:
            print("Middleware", portNum, "failed returning all members")

    def test1(self):
        for nodeIdx in self.allNodesHost:
            args = (self.allNodesHost[nodeIdx], self.allNodesPort[nodeIdx])
            t = threading.Thread(target = self.connect, args= args)
            t.start()

if __name__ == '__main__':
    client = Client()
