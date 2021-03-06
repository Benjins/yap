## YAP - Youtube Annotation Preservation
---------------

## NOTE: Youtube has removed access to all annotations as of January 15. Any downloads will result in an XML file w/o legacy annotations.

YouTube has decided to outlaw ~fun~annotations on their platform. This project consists of tools for people to ensure that their hard work is not lost.

Here are the main parts to this project:

 - _anno.py:_ A python script ~that builds off of [youtube-dl](https://rg3.github.io/youtube-dl/)~ to download annotations ~and metadata~, but not the video files or any other data for videos. It also parses out any links to other videos in those annotations, and downloads them. This is useful for interactive videos based on annotations, which may have dozens of videos linking to each other in a tree/graph like fashion.
 - _render/:_ HTML/Javascript that can render the annotations on top of a YouTube embed. Used to ensure that annotations are downloaded properly.
 - _experimental/_: Some experimental scripts that won't work out of the box, but that I've found to be much more efficient, as they use asynchronous IO (the `dl_annotations.py` script pipes into the `write_to_db.py` script). 
 - _crawl\_user.py_: A python script for finding all the public video URLS of a particular uploader (OR playlist...naming, I know).
 - _crawl\_related.py_: A python script that given a set of youtube videos, produces their related videos from the sidebar.
 - _crawl\_search.py_: A python script that will deliver the videos that youtube returns in its search query for the given terms.
 
See [here](https://benjins.com/yap) for a live demo of some recovered annotations re-rendered over their source videos.
 
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

 - [?] have youtube embed aligned to annotations
 - [ ] aspect ratio correction for annotations over embed
 - [x] Figure out some way to embed video w/o annotations by default (or just wait until Jan. 15, 2019 lol)
 - [ ] general outgoing links
 - [X] YouTube links stay on page, but change video/annotations
 - [X] YouTube links for the current video just jump the timestamp
 - [ ] font size issues
 - [?] highlight annotation borders
 - [X] text colour
 - [ ] pause type annotations
 - [ ] speech bubbles w/ proper anchors
 - [ ] make title/label stuff are rendering properly
 - [ ] make close button per annotation
 - [ ] make anchor icon show up on hover for highlight annotations
 - [ ] alpha changes for hover for some annotations
 