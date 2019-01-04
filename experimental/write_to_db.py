import sqlite3

import os
import sys
import time

## Get a connection to our existing database
db = sqlite3.connect('C:/Users/Benji/VideoDL/anno.db', timeout=60.0)


dlBuffer = []
parseBuffer = []

def FlushMarkedVids():
    global dlBuffer
    global parseBuffer
    print("Syncing %d dl writes and %d parse writes" % (len(dlBuffer), len(parseBuffer)), file=sys.stderr)
    
    cur = db.cursor()
    
    t0 = time.time()
    cur.execute("BEGIN TRANSACTION;")
    cur.executemany("INSERT OR IGNORE INTO VideoAnnoDL(videoID) VALUES (?);", dlBuffer)
    cur.executemany("INSERT OR IGNORE INTO VideoAnnoParsed(videoID) VALUES (?);", parseBuffer)
    t1 = time.time()
    cur.execute("COMMIT;")
    t2 = time.time()
    
    db.commit()
    
    t3 = time.time()
    
    #print("transactional inserts: %f" % (t1 - t0))
    #print("transactional commit: %f" % (t2 - t1))
    #print("disk commit: %f" % (t3 - t2))
    
    dlBuffer = []
    parseBuffer = []

for line in sys.stdin:
    line = line.strip()
    if line[0] == 'D':
        dlBuffer.append( (line[2:],) )
    elif line[0] == 'P':
        parseBuffer.append( (line[2:],) )
    else:
        print('Malformed line: "%s"' % line, file=sys.stderr)

    if len(dlBuffer) > 1000 or len(parseBuffer) > 1000:
        FlushMarkedVids()

        
# If we finish reading from stdin, catch up on any other writes ina  final batch
FlushMarkedVids()

