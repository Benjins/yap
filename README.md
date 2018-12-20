## YAP - Youtube Annotation Preservation
---------------

YouTube has decided to outlaw ~fun~annotations on their platform. This project consists of tools for people to ensure that their hard work is not lost.

There are three main parts to this project:

 - _anno.py:_ A python script ~that builds off of [youtube-dl](https://rg3.github.io/youtube-dl/)~ to download annotations ~and metadata~, but not the video files or any other data for videos. It also parses out any links to other videos in those annotations, and downloads them. This is useful for interactive videos based on annotations, which may have dozens of videos linking to each other in a tree/graph like fashion.
 - _render/:_ HTML/Javascript that can render the annotations on top of a YouTube embed. Used to ensure that annotations are downloaded properly.
 - _crawl\_user.py_: Another python script for finding all the public video URLS of a particular uploader.
 
There are some other resources that may be useful:

 - [Youtube-Video-Annotations-Player](https://github.com/ttsiodras/Youtube-Video-Annotations-Player)
 - [Convert annotation text to SRT](https://github.com/germanger/youtubeannotations-to-srt)
 - [Convert annotation text to ASS](https://github.com/nirbheek/youtube-ass)
 
Some examples of videos that use annotations in various ways:
 - [Musical Picture Frames - Joe Penna](https://www.youtube.com/watch?v=zxYXg5vhqjw)
 - [The last Annotations On Youtube](https://www.youtube.com/watch?v=6pv2qxbiabc)
 - [The last annotations On YouTube (another video with the same name...)](https://www.youtube.com/watch?v=M2ryDEyyrXE)
 - [Interactive Youtube Shooter Game! | Vixolent](https://www.youtube.com/watch?v=iCnlAC4OM38)
 - [Sonic (Annotation Art)](https://www.youtube.com/watch?v=NsPoyMzsVOU)
 
TODO for rendering layer:

 - have youtube embed aligned to annotations
 - general outgoing links
 - YouTube links stay on page, but change video/annotations
 - YouTube links for the current video just jump the timestamp 
 - font size issues
 - highlight annotation borders
 - text colour
 - pause type annotations
 - speech bubbles w/ proper anchors
 - make title/label stuff are rendering properly
 