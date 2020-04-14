import rpyc
import sys
import threading

class Client():
    def __init__(self):
        self.middlewareHost = "localhost"
        self.middlewarePort = 5000
        self.leaderHost, self.leaderPort = self.getLeader()
        print(self.leaderHost)
        print(self.leaderPort)

        self.query()


    def connectAndQuery(self, host, port, queryStr):
        conn = rpyc.connect(host, port)
        result = conn.root.query(queryStr)
        print (result)


    def getLeader(self):
        try:
            conn = rpyc.connect(self.middlewareHost, self.middlewarePort)
            return conn.root.getLeader()
        except Exception:
            print("Middleware", portNum, "failed getting leader")

    def query(self):
        queryStr = 'SELECT RoomID, Type, Floor from RoomInfo where Type = 2'
        args = (self.leaderHost, self.leaderPort, queryStr)
        t = threading.Thread(target = self.connectAndQuery, args= args)
        t.start()

if __name__ == '__main__':
    client = Client()
