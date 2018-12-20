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

from subprocess import call

def FollowContinuation(continID, clickTrack, filename):
    nextURL = "https://www.youtube.com/browse_ajax?ctoken=%s&continuation=%s&itct=%s" % (continID, continID, clickTrack)
            
    ytLabel = "x-youtube-page-label: youtube.ytfe.desktop_20181214_4_RC1"
    ytPageCL = "x-youtube-page-cl: 225759553"
    ytClientVersion = "x-youtube-client-version: 2.20181215"
    ytChecksum = "x-youtube-variants-checksum: 5c70c3e5906edce906a6396d0ef9768c"
    args = ['curl', nextURL, '-H', "accept-language: en-US,en;q=0.9", '-H', ytLabel, '-H', ytPageCL, '-H', "pragma: no-cache", '-H', ytClientVersion, '-H', ytChecksum, '-H', "cache-control: no-cache", '-H', "x-youtube-client-name: 1", '--silent', '--output', filename]
    
    call(args)

## Given the file containing
def ParseBrowseResponse(filename):
    recur = False

    with open(filename, encoding="utf8") as json_data:
        d = json.load(json_data)
        
        importantData = d[1]
        response = importantData['response']
        continuationData = response['continuationContents']['gridContinuation']
        
        items = continuationData['items']
        
        for item in items:
            print("https://www.youtube.com/watch?v=%s" % item['gridVideoRenderer']['videoId'])

        try:
            contins = continuationData['continuations']
            
            contin = contins[0]
            
            next = contin['nextContinuationData']
            
            clickTrack = next['clickTrackingParams']
            continID = next['continuation']
            
            FollowContinuation(continID, clickTrack, filename)
            
            recur = True
        except:
            recur = False
        
        json_data.close()
        
    
    ## If we picked up a continuation, then re-parse the file since we downloaded more data
    if recur:
        ParseBrowseResponse(filename)

## Parse the initial HTML page sent by accessing the /videos page for the user
def ParseBrowseResponseInit(filename):
    with open(filename, encoding="utf8") as responseFile:
        response = responseFile.read()
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
            
            FollowContinuation(continID, clickTrack, 'continue.json')
            ParseBrowseResponse('continue.json')
        
## OR just the user's channel URL (NOTE: We add '/videos', so make sure it's just the bare user URL
def ParseUserChannelURLInit(channelURL):

    pragmaNoCache = "pragma: no-cache"
    cacheNoCache = "cache-control: no-cache"
    userAgent = "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"

    args = ['curl', '%s/videos' % channelURL, '-H', pragmaNoCache, '-H', cacheNoCache, '-H', userAgent, '--silent', '--output', 'userFeedInit.html']
    call(args)
    ParseBrowseResponseInit('userFeedInit.html')
        
## If a user has a channel short name, we can use that
def ParseUserInit(username):
    ParseUserChannelURLInit('https://www.youtube.com/user/%s' % username)

if len(sys.argv) == 3:
    if sys.argv[1] == 'user':
        ParseUserInit(sys.argv[2])
    elif sys.argv[1] == 'url':
        ParseUserChannelURLInit(sys.argv[2])
    else:
        print("Uhhh.....come again?")
else:
    print("Please see usage docs just as soon as I write them")
    
