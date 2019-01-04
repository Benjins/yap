import encodings.idna

import asyncio
import ssl

import sys
import os
import errno

import json

import sqlite3

import os
import sys
import time

import xml.etree.ElementTree

## you can try to import aiofiles "the normal way",
## but I'm doing local importing because w/e
#import aiofiles
sys.path.append('E:/VideoDL/Anno/yap/experimental')
import aiofiles


## Command for the SSL key/cert
## openssl req -newkey rsa:2048 -nodes -keyout pymotw.key -x509 -days 365 -out pymotw.crt

ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.check_hostname = False
ssl_context.load_cert_chain('yap/experimental/pymotw.crt', 'yap/experimental/pymotw.key')


## Get a connection to our existing database
db = sqlite3.connect('C:/Users/Benji/VideoDL/anno.db', timeout=60.0)

async def ReadChunkedTransferEncoding(reader):
    fullContent = bytearray()
    
    while True:
        line = await reader.readline()
        if line is None or len(line) <= 2:
            break
        text = line.decode('utf-8').strip()
        chunkLen = int(text, 16)
        #print("Got chunk of length: %d" % chunkLen)
        
        if chunkLen == 0:
            ## I think??
            finalEnd = await reader.readexactly(2)
            break
        
        data = await reader.readexactly(chunkLen)
        #print("Chunk of len %d" % len(data))
        fullContent += data
        junkEnd = await reader.readexactly(2)
        #print("Junk end: '%s'" % junkEnd.decode('utf-8'))
        
    return fullContent

async def ReadFullResponse(reader, len):
    data = await reader.readexactly(len)
    return data
  
async def SendMessageToConn(reader, writer, message):
    #print(f'Send: {message!r}')
    writer.write(message.encode('utf-8'))
    
    try:
        headerData = {}
        
        httpCode = "HTTP/1.1"
        returnCode = "400"
        returnMsg = "Dunno Lol"
        
        isFirst = True
        while True:
            line = await reader.readline()
            text = line.decode('utf-8').strip() ## Removes the trailing newline

            if len(line) <= 2:
                break
            
            if isFirst:
                isFirst = False
                ## First line, parse differently
                lineParts = text.split(' ', 2)
                if len(lineParts) != 3:
                    print('Bad first line of http response? "%s"' % text, file=sys.stderr)
                    return None, True

                httpCode = lineParts[0]
                returnCode = lineParts[1]
                returnMsg = lineParts[2]
            else:
                headerParts = text.split(': ', 1)
                headerData[headerParts[0]] = headerParts[1]
                #print('Header: "%s"' % headerParts[0])

        #print('%s %s %s' % (httpCode, returnCode, returnMsg), file=sys.stderr)
        #print(headerData)
        if returnCode == '200': 
            fullContents = None
            if 'Transfer-Encoding' in headerData and headerData['Transfer-Encoding'] == 'chunked':
                fullContents = await ReadChunkedTransferEncoding(reader)
            elif 'Content-Length' in headerData:
                fullContents = await ReadFullResponse(reader, int(headerData['Content-Length']))
            else:
                print("ERRORRORORR: Write code for handling non-chunked responses", file=sys.stderr)
                return None, True

            return fullContents, False
        else:
            return None, True
            
    
    except Exception as e:
        #raise
        print("Error, got exception: '%s'" % str(e), file=sys.stderr)
        return None, True
        

def GetSubFolderNameForVideoID(id):
    return id[0:2].upper()

def GetFullPathForVideoID(id):
    return '%s/%s.annotations.xml' % (GetSubFolderNameForVideoID(id), id)
        
outstandingDLWrites = {}
def IsVideoDownloaded(id):
    return (id in outstandingDLWrites) or (db.execute("SELECT * FROM VideoAnnoDL WHERE videoID='%s'" % id).fetchone() is not None)

outstandingParseWrites = {}
def IsVideoParsed(id):
    return (id in outstandingParseWrites) or (db.execute("SELECT * FROM VideoAnnoParsed WHERE videoID='%s'" % id).fetchone() is not None)
    
dlBuffer = []
parseBuffer = []

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
                return param[2:13]

    return None
    
def ParseForMoreAnnotations(contents):
    global dlBuffer
    root = xml.etree.ElementTree.fromstring(contents)
    for annotation in root.iter('annotation'):
        action = annotation.find('action')
        if action is not None:
            urlElem = action.find('url')
            if urlElem is not None:
                urlStr = urlElem.get('value')
                if urlStr is not None and urlStr.startswith("https://www.youtube.com/watch?"):
                    #print("Found new URL to crawl: '%s'" % urlStr)
                    newVidID = ParseVideoIDFromURL(urlStr)
                    if newVidID is not None and not IsVideoDownloaded(newVidID):
                        outstandingDLWrites[newVidID] = 1
                        #print('New Vid URL: "%s"' % newVidID, file=sys.stderr)
                        dlBuffer.append(newVidID)
                        
        
async def DownloadAnnotationsForVideoID(reader, writer, vidID):
    message = 'GET /annotations_invideo?video_id=%s HTTP/1.1\r\nHost: www.youtube.com\r\nConnection: keep-alive\r\n\r\n' % vidID
    fullContents, shouldReconnect = await SendMessageToConn(reader, writer, message)
    
    if shouldReconnect:
        return True
    elif fullContents is None:
        fullContents, shouldReconnect = await SendMessageToConn(reader, writer, message)

    if shouldReconnect:
        return True
    elif fullContents is not None:
        text = fullContents.decode('utf-8')
        if not IsVideoParsed(vidID):
            ParseForMoreAnnotations(text)
            parseBuffer.append(vidID)
            outstandingParseWrites[vidID] = 1
            #print('P %s' % vidID)
        filename = GetFullPathForVideoID(vidID)
        async with aiofiles.open(filename, 'w', encoding="utf-8") as f:
            await f.write(text)

    return False
            
async def DLAnnotations(vidIDs):
    reader, writer = await asyncio.open_connection('www.youtube.com', 443, ssl=ssl_context)

    for vidID in vidIDs:
        shouldReconnect = await DownloadAnnotationsForVideoID(reader, writer, vidID)
        if shouldReconnect:
            writer.close()
            await writer.wait_closed()
            reader, writer = await asyncio.open_connection('www.youtube.com', 443, ssl=ssl_context)
    
    #print('Close the connection')
    writer.close()
    await writer.wait_closed()

async def ParallelDL():
    global dlBuffer
    global parseBuffer
    
    ourDLBuffer = dlBuffer
    
    dlBuffer = []

    TOTAL_COUNT = len(ourDLBuffer)
    
    print('Running download batch of %d...' % len(ourDLBuffer), file=sys.stderr)
    
    RUNNER_COUNT = 16
    BATCH_PER_RUNNER = (TOTAL_COUNT + RUNNER_COUNT - 1) // RUNNER_COUNT
    
    tasks = ()
    
    for i in range(RUNNER_COUNT):
        start = i * BATCH_PER_RUNNER
        end = (i+1) * BATCH_PER_RUNNER
        tasks += ( DLAnnotations(ourDLBuffer[start:end]), )
    
    await asyncio.gather(*tasks)
    
    for id in ourDLBuffer:
        print('D %s' % id)
    
    for id in parseBuffer:
        print('P %s' % id)
        
    parseBuffer = []
    
for line in sys.stdin:
    vidID = ParseVideoIDFromURL(line.strip())
    if not IsVideoDownloaded(vidID):
        dlBuffer.append(vidID)

    if len(dlBuffer) >= 5000:
        print('Kicking off batch, DL buffer: %d items' % len(dlBuffer), file=sys.stderr)
        asyncio.run(ParallelDL())
        
# If we read all of stdin, kick off another batch to get any stragglers
while len(dlBuffer) > 0:
    asyncio.run(ParallelDL())
