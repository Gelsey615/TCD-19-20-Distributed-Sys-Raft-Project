import rpyc
import sys
import threading
from threading import Timer

class Client(rpyc.Service):
    def __init__(self):
        self.middlewareHost = "localhost"
        self.middlewarePort = 5000
        self.leaderTimer = None
        self.requestLeader()

        self.queryTimer = None
        self.bookTimer = None
        self.roomStartId = 30

        mainThread = threading.Thread(target = self.run_server)
        mainThread.start()

    def run_server(self):
        while True:
            if self.queryTimer == None:
                self.queryTimer = Timer(5.0, self.query)
                self.queryTimer.start()
            if self.bookTimer == None:
                self.bookTimer = Timer(7.0, self.insert)
                self.bookTimer.start()

    def requestLeader(self):
        print("requesting leader ip address")
        self.leaderHost, self.leaderPort = self.getLeader()
        if self.leaderHost == "":
            if self.leaderTimer != None:
                self.leaderTimer.cancel()
            self.leaderTimer = Timer(3.0, self.requestLeader)
            self.leaderTimer.start()

    def getLeader(self):
        try:
            conn = rpyc.connect(self.middlewareHost, self.middlewarePort)
            return conn.root.getLeader()
        except Exception:
            print("Middleware", portNum, "failed getting leader")


    def connectAndQuery(self, host, port, queryStr):
        try:
            conn = rpyc.connect(host, port)
            result = conn.root.query(queryStr)
            if result == "":
                print ("No such room\n")
            else:
                print (result)
        except Exception:
            print("connection to server failed, requesting new IP address")
            self.requestLeader()

    def connectAndInsert(self, host, port, insertStr):
        try:
            conn = rpyc.connect(host, port)
            result = conn.root.bookRoom(insertStr)
            print("Add room successfully: ", result, "\n")
        except Exception:
            print("connection to server failed, requesting new IP address")
            self.requestLeader()

    def query(self):
        if self.queryTimer != None:
            self.queryTimer.cancel()
            self.queryTimer = None
        if self.leaderHost == "":
            print("no server connection")
            return
        #print("connecting", self.leaderHost, self.leaderPort)
        queryStr = 'SELECT RoomID, Type, Floor from RoomInfo where Type = 4'
        args = (self.leaderHost, self.leaderPort, queryStr)
        t = threading.Thread(target = self.connectAndQuery, args= args)
        t.start()

    def insert(self):
        if self.bookTimer != None:
            self.bookTimer.cancel()
            self.bookTimer = None
        if self.leaderHost == "":
            print("no server connection")
            return
        #print("connecting", self.leaderHost, self.leaderPort)
        inserStr = f'INSERT INTO RoomInfo (RoomID,Type,Floor) VALUES ({self.roomStartId+1}, 4, 3)'
        self.roomStartId += 1
        args = (self.leaderHost, self.leaderPort, inserStr)
        t = threading.Thread(target = self.connectAndInsert, args= args)
        t.start()

if __name__ == '__main__':
    from rpyc.utils.server import ThreadPoolServer
    client = ThreadPoolServer(Client(), port = 4999)
    client.start()
