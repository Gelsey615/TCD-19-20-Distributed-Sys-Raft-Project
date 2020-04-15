import sqlite3
import random

roomInfo = []
for i in range(30):
    type = random.randint(1, 3)
    floor = random.randint(1, 5)
    str = f'INSERT INTO RoomInfo (RoomID,Type,Floor) \
      VALUES ({i}, {type}, {floor})'
    roomInfo.append(str)

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

for i in range(3):
    conn = sqlite3.connect(f'pythonsqlite{i}.db')
    conn.execute(tableRoom)
    conn.execute(TableBookInfo)
    for str in roomInfo:
        conn.execute(str)
    conn.commit()
    conn.close()
