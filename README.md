# TCD-19-20-Distributed-Sys-Raft-Project

## First time clone
To initialize sqlite table 
1. python manage.py migrate
2. python manage.py makemigrations room

## Set up .git/info/exclude to avoid committing pyc, sqlite and migration files
1. cd to your local folder of this git project
2. vim .git/info/exclude
3. add the following lines to the file and save:

  \*.pyc
  
  db.sqlite3
  
  room/migrations/\*
