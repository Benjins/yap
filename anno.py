##
## USAGE: anno.py [URL of video] [URL of video] ...
## Each URL is an argument
## URL's must start with https://www.youtube.com/watch?
## No other cmd-line arg stuff is in atm
## Will download everything to the current directory
## This will crawl any videos linked in the annotations as well, so it may take a while...
## Stopping the command in the middle of running is okay, anything downloaded will stay,
## but may lose some data that wasn't crawled yet
## Uses Sqlite, puts a lil 'anno.db' file in the current directory, that's just to track what's been cached

## Dependencies
import xml.etree.ElementTree
import sqlite3
import sys
import os
import errno

import http.client

import time


from os import listdir
from os.path import isfile, join

from subprocess import call
from pathlib import Path

## Setup stuff for sqlite, runs each time (will not overwrite data)
## We effectively use sqlite as a persistent, unordered set so know if something is cached locally easily,
## and what processing we've done on it
createStr = """
CREATE TABLE If NOT EXISTS VideoAnnoDL(
   videoID VARCHAR(255) PRIMARY KEY
);
"""
createStr2 = """
CREATE TABLE If NOT EXISTS VideoAnnoParsed(
   videoID VARCHAR(255) PRIMARY KEY
);
"""

indexStr = """
CREATE INDEX If NOT EXISTS DLIdIndex ON VideoAnnoDL (videoID);
"""

indexStr2 = """
CREATE INDEX If NOT EXISTS ParsedIdIndex ON VideoAnnoParsed (videoID);
"""

## Setup db connection and the schemas
db = sqlite3.connect('anno.db', timeout=60.0)
db.execute(createStr)
db.execute(createStr2)
db.execute(indexStr)
db.execute(indexStr2)

db.execute("pragma journal_mode=wal")

db.commit()

############################

## Case-insensitive so that it works on any file system w/o weird quirks
def GetSubFolderNameForVideoID(id):
    return id[0:2].upper()

def GetFullPathForVideoID(id):
    return '%s/%s.annotations.xml' % (GetSubFolderNameForVideoID(id), id)

def DidAnnotationsAndMetadataGetDownloaded(id):
    annoFile = Path(GetFullPathForVideoID(id))
    ## NOTE: No longer downloading meta files for now
    return annoFile.is_file()

## In-memory cache, yes it's volatile but it's only for marking things as downloaded,
## worst case is we'd download it again unnecessarily
outstandingDLWrites = {}
outstandingParsedWrites = {}

def FlushOutstandingWrites():
    global outstandingParsedWrites
    global outstandingDLWrites
    
    # Wrangle the dict into a list of tuples, which executemany takes
    dlWritesEx = []
    for dlWrite in outstandingDLWrites.keys():
        dlWritesEx.append((dlWrite, ))
        
    parseWritesEx = []
    for parseWrite in outstandingParsedWrites.keys():
        parseWritesEx.append((parseWrite, ))

    #print("Syncing outstanding writes to database")
    
    print("Syncing %d dl writes and %d parse writes" % (len(dlWritesEx), len(parseWritesEx)))
    
    cur = db.cursor()
    
    t0 = time.time()
    cur.execute("BEGIN TRANSACTION;")
    cur.executemany("INSERT OR IGNORE INTO VideoAnnoDL(videoID) VALUES (?);", dlWritesEx)
    cur.executemany("INSERT OR IGNORE INTO VideoAnnoParsed(videoID) VALUES (?);", parseWritesEx)
    t1 = time.time()
    cur.execute("COMMIT;")
    t2 = time.time()
    
    db.commit()
    
    t3 = time.time()
    
    print("transactional inserts: %f" % (t1 - t0))
    print("transactional commit: %f" % (t2 - t1))
    print("disk commit: %f" % (t3 - t2))
    
    outstandingDLWrites = {}
    outstandingParsedWrites = {}

def MarkVidAsDownloaded(id):
    global outstandingDLWrites
    outstandingDLWrites[id] = 1
    
    if len(outstandingDLWrites) > 500:
        FlushOutstandingWrites()


def MarkVidAsParsed(id):
    global outstandingParsedWrites
    outstandingParsedWrites[id] = 1
    
    if len(outstandingParsedWrites) > 500:
        FlushOutstandingWrites()

def IsVideoDownloaded(id):
    return (id in outstandingDLWrites) or (db.execute("SELECT * FROM VideoAnnoDL WHERE videoID='%s'" % id).fetchone() is not None)
        
def IsVideoParsed(id):
    return (id in outstandingParsedWrites) or (db.execute("SELECT * FROM VideoAnnoParsed WHERE videoID='%s'" % id).fetchone() is not None)

## TODO: Actual parsing, for now just manually get video id
def ParseVideoIDFromURL(url):
    url = url.strip()
    if (url is not None and url.startswith("https://www.youtube.com/watch?")):
        ## Isolate the Query params
        ## NOTE: This is not exactly correct, but seems to work most of the time
        ## TODO: Proper URL parsing
        url = url.split('https://www.youtube.com/watch?')[1]
        url = url.split('#')[0]
        params = []
        if (url.find('&amp;') != -1):
            params = url.split('&amp;')
        elif (url.find('&') != -1):
            params = url.split('&')
        else:
            params = [ url ]

        for param in params:
            if param.startswith('v='):
                return param[2:]

    return None

## Temporary queue for video traversal
## NOTE: breadth-first as a result
## NOTE: Only temporary, not saved out so some data may be lost in case of crash/early exit
videoQueue = [ParseVideoIDFromURL(f) for f in sys.argv[1:]]

## If we are forcing parsing, we make sure we don't parse the same file twice in this session,
## So an in-memory dict of the ones we've already hit is used
## Otherwise, we'd infinite loop potentially
forceParseDictCheck = {}

## Even if we've already downloaded something, parse it again to
forceParse = False

## Only download annotations for videos in the argv list, don't crawl to others
disableCrawl = False

## If we've downloaded annotations, we can parse them for any out-going links to YouTube videos
## From there, we can download those annotations, and continue on
## Based on 2 minutes of looking at the annotation format that youtube-dl saves out
def ParseVideo(id):
    if disableCrawl:
        return
    elif (forceParse and id in forceParseDictCheck) or (not forceParse and IsVideoParsed(id)):
        ## If we are forcing parsing, check that we didn't already parse this video in this session
        ## If we are not forcing parsing, check the persistent set of parsed videos in the database
        print("Skipping Video Parsing")
    elif not IsVideoDownloaded(id):
        print("'%s' Not yet downloaded, cannot parse" % id)
    elif not DidAnnotationsAndMetadataGetDownloaded(id):
        print("Error, we think '%s' was downloaded but the files are missing" % id)
    else:
        root = xml.etree.ElementTree.parse(GetFullPathForVideoID(id)).getroot()
        for annotation in root.iter('annotation'):
            action = annotation.find('action')
            if action is not None:
                urlElem = action.find('url')
                if urlElem is not None:
                    urlStr = urlElem.get('value')
                    if urlStr is not None and urlStr.startswith("https://www.youtube.com/watch?"):
                        print("Found new URL to crawl: '%s'" % urlStr)
                        videoQueue.append(ParseVideoIDFromURL(urlStr))

        ## If we are forcing parsing (i.e, checking against the newly constructed in-memory set of already parsed videos),
        ## Then the in-memory set is the one we update
        ## In both cases, we update the persistent set of parsed videos
        if forceParse:
            forceParseDictCheck[id] = 0

        MarkVidAsParsed(id)

def MaybeMakeDirectory(dirname):
    try:
        os.makedirs(dirname)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
        
## The connection to YouTube...kinda important for this
YTconn = http.client.HTTPSConnection("www.youtube.com")

def DownloadVideo(id):
    global YTconn
    if IsVideoDownloaded(id):
        print("Skipping Video Download")
    else:
        annoURL = '/annotations_invideo?video_id=%s' % id
        res = None
        retry = True
        ## If we get a ResponseNotReady error, it means our keepalive ran out
        ## In that case, we re-establish our connection and try again
        ## If we get a different error, it probably failed for real, so we just give up
        while retry:
            try:
                ## TODO: Any headers that need to be set would go here
                YTconn.request("GET", annoURL)
                res = YTconn.getresponse()
                retry = False
            except http.client.ResponseNotReady:
                print("Re-establishing connection...")
                YTconn = http.client.HTTPSConnection("www.youtube.com")
            except Exception as e:
                print("Encountered other error...")
                ## For debugging, this is useful
                ## Otherwise, immortality has its perks
                ##raise e 
                retry = False

        if res is not None and res.status == 200:
            data = res.read()

            folder = GetSubFolderNameForVideoID(id)
            MaybeMakeDirectory(folder)
            
            filename = GetFullPathForVideoID(id)
            with open(filename, 'w', encoding="utf-8") as f:
                f.write(data.decode("utf-8"))
                f.close()

            if DidAnnotationsAndMetadataGetDownloaded(id):
                MarkVidAsDownloaded(id)
            else:
                print("Could not download video '%s'..." % id)
        else:
            if res is None:
                print("Some error during downloading...")
            else:
                print("Got error %d %s on '%s', failed to download" % (res.status, res.reason, id))

def DownloadAndParseVideo(id):
    DownloadVideo(id)
    ParseVideo(id)

##unparsedListCur = db.execute("SELECT * FROM VideoAnnoDL WHERE NOT EXISTS (SELECT * FROM VideoAnnoParsed WHERE VideoAnnoParsed.videoID = VideoAnnoDL.videoID) LIMIT 5000")
##
##for i in range(5000):
##    vidID = unparsedListCur.fetchone()[0]
##    if vidID is not None:
##        ParseVideo(vidID)
##    else:
##        break
    
##with open('UserCrawl/youtube_vid_id_list.txt') as vidIdList:
##    for vidID in vidIdList:
##        vidID = vidID.strip()
##        print('Working on %s' % vidID)
##        DownloadVideo(vidID)
    
while len(videoQueue) > 0:
    print("Still have %d videos in queue (may have dupes)" % len(videoQueue))
	## BFS For now...DFS wasn't as good
    nextVid = videoQueue.pop(0)
    if nextVid is None:
        print("Ooops....")
    else:
        print("Downloading and parsing next vid: '%s'..." % nextVid)
        DownloadAndParseVideo(nextVid)

## Any outstanding writes to our "memory cache" need to be flushed to disk now
FlushOutstandingWrites()
        
print("All done.")
