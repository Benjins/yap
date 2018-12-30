  function UpdateYTPlayerURL() {
    var ytEmbed = document.getElementById('ytplayer');
	var newURL = ytEmbed.src + '&iv_load_policy=3';
	ytEmbed.src = newURL;
  }

  function PlayYTVideoDirect(vidID) {
	window.bnsYTPlayer = new YT.Player('ytplayer', {
      height: '360',
      width: '640',
      videoId: vidID,
	  enablejsapi: '1',
	  origin: window.location.hostname,
	  // TODO: ???
	  iv_load_policy: '3',
	  
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
  
  function PlayYTVideo(vidID) {
	if (YTAPIReady) {
	  if (window.bnsYTPlayer !== undefined) {
	    window.bnsYTPlayer.loadVideoById(vidID);
		// TODO: I guess this isn't needed?
		//UpdateYTPlayerURL();
	  } else {
		PlayYTVideoDirect(vidID);
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