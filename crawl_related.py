import sqlite3
import sys
import os

import http.client

## TODO(code dup w/ anno.py)
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

## Very simple, just downloads the video HTML page, and parses out the outgoing links to other youtube videos
def CrawlVideoIDForRelatedVideos(id):
    YTconn = http.client.HTTPSConnection("www.youtube.com")
    
    vidURL = '/watch?v=%s' % id
    
    YTconn.request("GET", vidURL)
    res = YTconn.getresponse()
    
    seenVidDict = {}
    
    if res is None:
        print("Got null response...")
    elif res.status == 200:
        data = res.read()
        text = data.decode("utf-8")
        parts = text.split('/watch?v=')
        for i in range(1, len(parts)):
            part = parts[i]
            if len(part) >= 11:
                vidID = part[0:11]
                ## If it contains '.', then it's not a valid video id (this comes up often w/ truncated links)
                if '.' not in vidID and vidID not in seenVidDict:
                    print('https://www.youtube.com/watch?v=%s' % vidID)
                    seenVidDict[vidID] = 1
    else:
        print("Got error %d %s on '%s', failed to download" % (res.status, res.reason, id))
    
    YTconn.close()


videoQueue = [ParseVideoIDFromURL(f) for f in sys.argv[1:]]

for vid in videoQueue:
    ## this isn't strictly necessary, but it is nice so we don't have to separately join the inputs and outputs
    print("https://www.youtube.com/watch?v=%s" % vid)
    CrawlVideoIDForRelatedVideos(vid)
