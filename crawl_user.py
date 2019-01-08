## Given a channel URL or user w/ shortened channel URL, we can get a list of all video URL's that they have uploaded
## We get these in batches, starting with the initial HTML page sent over by the server,
## And with each batch there is a "continuation" code for getting the next one (if there is one; the last batch doesn't have this code)
## The continuation code is sent for the next batch, and has the next continuation code, etc.

## This script uses curl as a subprocess and downloads some temporary files in the working directory
## (it doesn't have to, I just got lazy figuring out how HTTP requests work in Python :p)

## USAGE:
## python crawl_user.py user {SHORT_CHANNEL_NAME}
## (e.g. MyChannel)
## OR
## python crawl_user.py url {CHANNEL_URL}
## (e.g. https://www.youtube.com/channel/UCtt7vaXAJDG1aSFJB or so)

## Will print out all Youtube video url's to stdout, which you could then feed into the anno.py script

import json
import sys

import traceback

import http.client

def GetDefaultHeaders():
    headers = {}
    headers["x-youtube-page-label"] = "youtube.ytfe.desktop_20181214_4_RC1"
    headers["x-youtube-page-cl"] = "225759553"
    headers["x-youtube-client-version"] = "2.20181215"
    headers["x-youtube-variants-checksum"] = "5c70c3e5906edce906a6396d0ef9768c"
    headers["pragma"] = "no-cache"
    headers["cache-control"] = "no-cache"
    headers["x-youtube-client-name"] = "1"
    headers["accept-language"] = "en-US,en;q=0.9"
    headers["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"
    return headers

conn = http.client.HTTPSConnection('www.youtube.com')
def GetMessageWithRetries(url, headersData={}, maxRetries = 5):
    global conn
    for i in range(maxRetries):
        try:
            #print('Making request "%s"...' % url)
            conn.request("GET", url, headers=headersData)
            res = conn.getresponse()
            #print('Got response')
            
            if res is not None and res.status == 200:
                data = res.read()
                #print('READ DATA')
                return data
            
        except http.client.ResponseNotReady:
            conn = http.client.HTTPSConnection('www.youtube.com')
        except Exception as e:
            traceback.print_exc()
            print("Error, got exception: '%s'" % str(e), file=sys.stderr)
            

    return None

def FollowContinuation(continID, clickTrack):
    nextURL = "/browse_ajax?ctoken=%s&continuation=%s&itct=%s" % (continID, continID, clickTrack)
            
    headers = GetDefaultHeaders()
    
    return GetMessageWithRetries(nextURL, headers)

def ParseChannelResponse(continuationData):    
    items = continuationData['items']
    
    for item in items:
        print("https://www.youtube.com/watch?v=%s" % item['gridVideoRenderer']['videoId'])

    try:
        contins = continuationData['continuations']
        
        contin = contins[0]
        
        next = contin['nextContinuationData']
        
        clickTrack = next['clickTrackingParams']
        continID = next['continuation']
        
        return FollowContinuation(continID, clickTrack)
    except Exception as e:
        #print('Got exception: "%s"' % str(e))
        return None
        
def ParsePlaylistResponse(continuationData):
    items = continuationData['contents']
    
    for item in items:
        print("https://www.youtube.com/watch?v=%s" % item['playlistVideoRenderer']['videoId'])

    try:
        contins = continuationData['continuations']
        
        contin = contins[0]
        
        next = contin['nextContinuationData']
        
        clickTrack = next['clickTrackingParams']
        continID = next['continuation']
        
        return FollowContinuation(continID, clickTrack)
    except:
        return None
    
## Given the file containing
def ParseBrowseResponse(json_data):
    recur = None

    d = json.loads(json_data)
    
    importantData = d[1]
    response = importantData['response']
    if 'continuationContents' in response:
        continContents = response['continuationContents']
        
        if 'gridContinuation' in continContents:
            recur = ParseChannelResponse(continContents['gridContinuation'])
        elif 'playlistVideoListContinuation' in continContents:
            recur = ParsePlaylistResponse(continContents['playlistVideoListContinuation'])
        
    
    ## If we picked up a continuation, then re-parse the file since we downloaded more data
    if recur is not None:
        ParseBrowseResponse(recur.decode('utf-8'))

## Parse the initial HTML page sent by accessing the /videos page for the user
def ParseBrowseResponseInit(response):
    vidIDParse = response.split('/watch?v=')
    for i in range(1, len(vidIDParse)):
        part = vidIDParse[i]
        partSplit = part.split('"')
        if len(partSplit) > 1:
            vidURL = partSplit[0]
            print("https://www.youtube.com/watch?v=%s" % vidURL)
            
            
    continParse = response.split('"continuation":"')
    if len(continParse) > 1:
        continParse = continParse[1].split('","clickTrackingParams":"')
        continID = continParse[0]
        clickTrack = continParse[1].split('"')[0]
        
        recur = FollowContinuation(continID, clickTrack)
        if recur is not None:
            ParseBrowseResponse(recur.decode('utf-8'))
        
## OR just the user's channel URL (NOTE: We add '/videos', so make sure it's just the bare user URL
def ParseUserChannelURLInit(channelURL):
    nextURL = '%s/videos?sort=da' % channelURL
            
    headers = GetDefaultHeaders()
    
    response = GetMessageWithRetries(nextURL, headers)
    if response is not None:
        ParseBrowseResponseInit(response.decode('utf-8'))
        
## If a user has a channel short name, we can use that
def ParseUserInit(username):
    ParseUserChannelURLInit('/user/%s' % username)
    
def ParseChannelInit(username):
    ParseUserChannelURLInit('/channel/%s' % username)

def ParsePlaylistInit(playlistID):
    nextURL = '/playlist?list=%s' % playlistID
    
    headers = GetDefaultHeaders()
    
    response = GetMessageWithRetries(nextURL, headers)
    if response is not None:
        ParseBrowseResponseInit(response.decode('utf-8'))
    
if len(sys.argv) >= 3:
    if sys.argv[1] == 'user':
        ParseUserInit(sys.argv[2])
    elif sys.argv[1] == 'channel':
        for channelID in sys.argv[2:]:
            try:
                ParseChannelInit(channelID)
            except Exception as e:
                traceback.print_exc()
                print("Error, got exception: '%s'" % str(e), file=sys.stderr)
    elif sys.argv[1] == 'playlist':
        for playlistID in sys.argv[2:]:
            ParsePlaylistInit(playlistID)
    else:
        print("Uhhh.....come again?")
else:
    print("Please see usage docs just as soon as I write them")
    
