import sqlite3
import sys
import os

import http.client

##
## Usage: crawl_search.py terms to search for
## Please use only words, there's no url escaping yet... >.<
##
## Note that YouTube will only return ~400 search results this way, since it's just hitting the normal HTML pages
## After that, it just stops (you can see this if you scroll way down, eventually it'll stop loading new results).
##

def TrawlTextForVideoLinks(text, seenVidDict):
    parts = text.split('/watch?v=')
    for i in range(1, len(parts)):
        part = parts[i]
        if len(part) >= 11:
            vidID = part[0:11]
            ## If it contains '.', then it's not a valid video id (this comes up often w/ truncated links)
            if '.' not in vidID and vidID not in seenVidDict:
                print('https://www.youtube.com/watch?v=%s' % vidID)
                seenVidDict[vidID] = 1

def LookforContinuationAndClickTracker(text):
    continID = None
    clickTracker = None

    continParts = text.split('"continuation":"')
    if len(continParts) > 1:
        intermed = continParts[1]
        continID = intermed.split('"')[0]

    clickTrackerParts = text.split('"clickTrackingParams":"')
    if len(clickTrackerParts) > 1:
        intermed = clickTrackerParts[1]
        clickTracker = intermed.split('"')[0]

    return (continID, clickTracker)
        
UserAgent = "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"

## Returns (continID, clickTracker) if found, or (None, None) otherwise
def CrawlVideosForSearchInitial(searchQuery):
    url = "https://www.youtube.com/results?search_query=%s" % searchQuery
    
    
    ##-H "pragma: no-cache"
    ##-H "cache-control: no-cache"
    ##-H "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"
    
    
    headerData = {'pragma': 'no-cache', "cache-control" : "no-cache", "user-agent" : UserAgent}
    
    YTconn = http.client.HTTPSConnection("www.youtube.com")
    YTconn.request("GET", url, headers=headerData)
    
    res = YTconn.getresponse()
    
    seenVidDict = {}
    
    continID = None
    clickTracker = None
    
    if res is None:
        print("Got null response...")
    elif res.status == 200:
        data = res.read()
        text = data.decode("utf-8")
        TrawlTextForVideoLinks(text, seenVidDict)
        (continID, clickTracker) = LookforContinuationAndClickTracker(text)
    else:
        print("Got error %d %s on '%s', failed to download" % (res.status, res.reason, id))
    
    YTconn.close()
    return (continID, clickTracker)

## Returns (continID, clickTracker) if found, or (None, None) otherwise
def CrawlVideosForSearchContinue(searchQuery, continID, clickTracker):
    url = "https://www.youtube.com/results?search_query=%s&pbj=1&ctoken=%s&continuation=%s&itct=%s" % (searchQuery, continID, continID, clickTracker)
    
    ##-H "origin: https://www.youtube.com"
    ##-H "x-youtube-page-label: youtube.ytfe.desktop_20181219_4_RC2"
    ##-H "x-youtube-page-cl: 226370883"
    ##-H "x-spf-referer: https://www.youtube.com/results?search_query=amv+annotations"
    ##-H "pragma: no-cache"
    ##-H "x-youtube-client-version: 2.20181220"
    ##-H "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"
    ##-H "x-youtube-variants-checksum: 3681b770b3fa1e524669701ba8924e26"
    ##-H "cache-control: no-cache"
    ##-H "x-youtube-client-name: 1"
    ##-H "authority: www.youtube.com"
    
    headerData = {'pragma': 'no-cache', "cache-control" : "no-cache", "user-agent" : UserAgent}
    headerData['origin'] = "https://www.youtube.com"
    headerData['x-youtube-page-label'] = "youtube.ytfe.desktop_20181219_4_RC2"
    headerData['x-youtube-page-cl'] = "226370883"
    headerData['x-spf-referer'] = "https://www.youtube.com/results?search_query=%s" % searchQuery
    headerData['x-youtube-client-version'] = "2.20181220"
    headerData['x-youtube-variants-checksum'] = "3681b770b3fa1e524669701ba8924e26"
    headerData['x-youtube-client-name'] = "1"
    headerData['authority'] = "www.youtube.com"
    
    YTconn = http.client.HTTPSConnection("www.youtube.com")
    YTconn.request("GET", url, headers=headerData)
    
    continID = None
    clickTracker = None
    
    res = YTconn.getresponse()
    
    seenVidDict = {}
    
    if res is None:
        print("Got null response...")
    elif res.status == 200:
        data = res.read()
        text = data.decode("utf-8")
        TrawlTextForVideoLinks(text, seenVidDict)
        (continID, clickTracker) = LookforContinuationAndClickTracker(text)
    else:
        print("Got error %d %s on '%s', failed to download" % (res.status, res.reason, id))
    
    YTconn.close()
    return (continID, clickTracker)
    
## search string is the human entered string which has been split into terms, e.g. ["day", "at", "the", "zoo"]
## NOTE: Cannot handle url-escaping just yet, so nothing like quotes, apostrophes, ampersands, etc, just words for now
def CrawlVideosForSearch(searchTerms):
    seperator = '+'
    searchQuery = seperator.join(searchTerms)
    #print("searching for videos: '%s'" % searchQuery)
    
    continID = None
    clickTracker = None
    
    (continID, clickTracker) = CrawlVideosForSearchInitial(searchQuery)

    while continID is not None and clickTracker is not None:
        (continID, clickTracker) = CrawlVideosForSearchContinue(searchQuery, continID, clickTracker)

CrawlVideosForSearch(sys.argv[1:])
