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

import traceback

## Command for the SSL key/cert
## openssl req -newkey rsa:2048 -nodes -keyout pymotw.key -x509 -days 365 -out pymotw.crt
ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.check_hostname = False
ssl_context.load_cert_chain('yap/experimental/pymotw.crt', 'yap/experimental/pymotw.key')


## Get a connection to our existing database

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
    try:
        writer.write(message.encode('utf-8'))
    
        headerData = {}
        
        httpCode = "HTTP/1.1"
        returnCode = "400"
        returnMsg = "Dunno Lol"
        
        isFirst = True
        while True:
            line = await reader.readline()
            text = line.decode('utf-8').strip() ## Removes the trailing newline

            if len(line) <= 2:
                if isFirst:
                    print('Bad first line found: "%s"' % text, file=sys.stderr)
                    return None,True
                break
            
            if isFirst:
                isFirst = False
                ## First line, parse differently
                lineParts = text.split(' ', 2)
                if len(lineParts) < 3:
                    print('Bad first line of http response? "%s"' % text, file=sys.stderr)
                    break

                httpCode = lineParts[0]
                returnCode = lineParts[1]
                returnMsg = lineParts[2]
            else:
                headerParts = text.split(': ', 1)
                headerData[headerParts[0]] = headerParts[1]
                #print('Header: "%s"' % headerParts[0])

        
        fullContents = None
        if 'Transfer-Encoding' in headerData and headerData['Transfer-Encoding'] == 'chunked':
            fullContents = await ReadChunkedTransferEncoding(reader)
        elif 'Content-Length' in headerData:
            fullContents = await ReadFullResponse(reader, int(headerData['Content-Length']))
        else:
            print("ERRORRORORR: Write code for handling non-chunked responses", file=sys.stderr)
            print('%s %s %s' % (httpCode, returnCode, returnMsg), file=sys.stderr)
            print(headerData, file=sys.stderr)
        
        #print('%s %s %s' % (httpCode, returnCode, returnMsg), file=sys.stderr)
        #print(headerData,file=sys.stderr)
        if returnCode == '200': 
            if 'Connection' in headerData and headerData['Connection'] == 'close':
                print('Server letting us know they\'re closing the connection...', file=sys.stderr)
                return fullContents,True
            else:
                return fullContents,False
        else:
            return None,True
            
    
    except Exception as e:
        #raise
        traceback.print_exc()
        print("Error, got exception: '%s'" % str(e), file=sys.stderr)
        return None,True
        
seenVidDict = {}
        
async def ParseVideoIDsForRelated(vidIDs):
    reader, writer = await asyncio.open_connection('www.youtube.com', 443, ssl=ssl_context)
    for vidID in vidIDs:
        ## Strip out the tuple returned
        vidID = vidID[0]
        message = 'GET /watch?v=%s HTTP/1.1\r\nHost: www.youtube.com\r\nConnection: keep-alive\r\n\r\n' % vidID
        data,shouldReconnect = await SendMessageToConn(reader, writer, message)
        
        if data is not None:
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
                    
                    
        if shouldReconnect:
            print('Connection possible closed, trying again', file=sys.stderr)
            writer.close()
            await writer.wait_closed()
            reader, writer = await asyncio.open_connection('www.youtube.com', 443, ssl=ssl_context)
                    
    writer.close()
    await writer.wait_closed()
        

db = sqlite3.connect('C:/Users/Benji/VideoDL/anno.db', timeout=60.0)        


def GetVideoIDs(count, offset):
    cur = db.execute('SELECT * FROM VideoAnnoDL ORDER BY videoID LIMIT %d OFFSET %d;' % (count, offset))
    return cur.fetchall()

async def RunTasks(count, offset):
    buff = GetVideoIDs(count, offset)

    TOTAL_COUNT = len(buff)
    
    print('Running related crawl batch of %d...' % len(buff), file=sys.stderr)
    
    RUNNER_COUNT = 16
    BATCH_PER_RUNNER = (TOTAL_COUNT + RUNNER_COUNT - 1) // RUNNER_COUNT
    
    tasks = ()
    
    for i in range(RUNNER_COUNT):
        start = i * BATCH_PER_RUNNER
        end = (i+1) * BATCH_PER_RUNNER
        tasks += ( ParseVideoIDsForRelated(buff[start:end]), )
    
    await asyncio.gather(*tasks)


if len(sys.argv) == 3:
    asyncio.run(RunTasks(int(sys.argv[1]),int(sys.argv[2])))
else:
    print('Please enter a count and offset as arguments',file=sys.stderr)

