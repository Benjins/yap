  function UpdateYTPlayerURL() {
    var ytEmbed = document.getElementById('ytplayer');
	var newURL = ytEmbed.src + '&iv_load_policy=3';
	ytEmbed.src = newURL;
  }

  function PlayYTVideoDirect(vidID, time) {
	window.bnsYTPlayer = new YT.Player('ytplayer', {
      height: '360',
      width: '640',
      videoId: vidID,
	  enablejsapi: '1',
	  origin: window.location.hostname,
	  // TODO: ???
	  iv_load_policy: '3',
	  
	  // TODO: Start seconds here too
	  
	  // TODO: Figure out which of these options are useful
	  controls: '0',
	  modestbranding:'1'
    });
	UpdateYTPlayerURL();
  }

  var vidIDQueued = null;
  var YTAPIReady = false;
  function onYouTubePlayerAPIReady() {
    if (!YTAPIReady) {
	
	  if (vidIDQueued !== null) {
		PlayYTVideoDirect(vidIDQueued);
	  }
	
	  YTAPIReady = true;
	}
  }
  
  function PlayYTVideo(vidID, time) {
	if (YTAPIReady) {
	  if (window.bnsYTPlayer !== undefined) {
		var startSeconds = (time !== null) ? time : 0;
		
		var currVideoURL = window.bnsYTPlayer.getVideoUrl();
		
		// We're seeking to a time in this video,
		// use seek instead of reloading the whole video
		if (currVideoURL.includes(vidID)) {
			window.bnsYTPlayer.seekTo(startSeconds);
		} else {
			window.bnsYTPlayer.loadVideoById(vidID, startSeconds);
		}
	  } else {
		PlayYTVideoDirect(vidID, time);
	  }
	} else {
	  vidIDQueued = vidID;
	}
  }
  
  // Load the IFrame Player API code asynchronously.
  var tag = document.createElement('script');
  tag.src = "https://www.youtube.com/player_api";
  var firstScriptTag = document.getElementsByTagName('script')[0];
  firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);