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

import http.client

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

## Setup db connection and the schemas
db = sqlite3.connect('anno.db')
db.execute(createStr)
db.execute(createStr2)

## Add any new files we may have missed
## NOTE: Won't need to do this normally, and is just to avoid extra downloads if we already have any
##annoFiles = [f[:-16] for f in listdir("./") if isfile(join("./", f)) and f.endswith(".annotations.xml")]
##for f in annoFiles:
##    db.execute("INSERT INTO VideoAnnoDL(videoID) SELECT '%s' WHERE NOT EXISTS(SELECT * FROM VideoAnnoDL WHERE videoID='%s');" % (f, f))

db.commit()

############################

def DidAnnotationsAndMetadataGetDownloaded(id):
    annoFile = Path("./%s.annotations.xml" % id)
    ## NOTE: No longer downloading meta files for now
    return annoFile.is_file()

def IsVideoDownloaded(id):
    return db.execute("SELECT * FROM VideoAnnoDL WHERE videoID='%s'" % id).fetchone() is not None

def IsVideoParsed(id):
    return db.execute("SELECT * FROM VideoAnnoParsed WHERE videoID='%s'" % id).fetchone() is not None

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
        root = xml.etree.ElementTree.parse('%s.annotations.xml' % id).getroot()
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

        ## XXX: If the command terminates early, we may lose some data that way
        db.execute("INSERT OR IGNORE INTO VideoAnnoParsed(videoID) VALUES('%s');" % id)
        db.commit()

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

            with open('%s.annotations.xml' % id, 'w', encoding="utf-8") as f:
                f.write(data.decode("utf-8"))
                f.close()

            if DidAnnotationsAndMetadataGetDownloaded(id):
                db.execute("INSERT INTO VideoAnnoDL(videoID) VALUES('%s');" % id)
                db.commit()
            else:
                print("Could not download video '%s'..." % id)
        else:
            if res is None:
                print("Some error during downloading...")
            else:
                print("Got error %d %s on '%s', failed to download" % (res.status, res.reason, id))

def DownloadAndParseVideo(id):
    if IsVideoDownloaded(id):
        print("Skipping video '%s', already downloaded" % id)
    else:
        DownloadVideo(id)

    ParseVideo(id)

while len(videoQueue) > 0:
    print("Still have %d videos in queue (may have dupes)" % len(videoQueue))
	## BFS For now...DFS wasn't as good
    nextVid = videoQueue.pop(0)
    if nextVid is None:
        print("Ooops....")
    else:
        print("Downloading and parsing next vid: '%s'..." % nextVid)
        DownloadAndParseVideo(nextVid)

print("All done.")
