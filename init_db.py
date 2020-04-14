import sqlite3
import random

conn = sqlite3.connect('pythonsqlite.db')
print ("Opened database successfully")

#conn.execute('''CREATE TABLE RoomInfo
#         (RoomID INT PRIMARY KEY     NOT NULL,
#         Type           INT    NOT NULL,
#         Floor          INT     NOT NULL);''')

#conn.execute('''CREATE TABLE BookInfo
#         (TranID TEXT PRIMARY KEY     NOT NULL,
#         Name           TEXT    NOT NULL,
#         Phone          TEXT    NOT NULL,
#         Email          TEXT    NOT NULL,
#         RoomID         INT     NOT NULL,
#         StartT         INT64   NOT NULL,
#         EndT           INT64   NOT NULL,
#         FOREIGN KEY(RoomID) REFERENCES RoomInfo(RoomID));''')
#print ("Table created successfully")

#for i in range(30):

#    type = random.randint(1, 3)
#    floor = random.randint(1, 5)
#    str = f'INSERT INTO RoomInfo (RoomID,Type,Floor) \
#      VALUES ({i}, {type}, {floor})'
#    print(str)
#    conn.execute(str);

#conn.commit()
queryStr = 'SELECT RoomID, Type, Floor from RoomInfo where Type = 2'
cursor = conn.execute(queryStr)
for row in cursor:
    print ("RoomID = ", row[0], "Type = ", row[1], "Floor = ", row[2])
conn.close()
