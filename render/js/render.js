
function GetBackgroundColourForAnnotation(anno) {
	if (anno === undefined || anno.bgColor === undefined) {
		return 'rgba(0,0,0,0)';
	}
	
	var alpha = anno.bgAlpha;
	if (alpha === undefined) {
		alpha = 1.0;
	}
	
	if (alpha === 0) {
		return 'rgba(0,0,0,0)';
	}

	// Uggghh...may have chose wrong on that serialisation... -_-
	var bgColHex = anno.bgColor;
	var rgb = parseInt('0x' + bgColHex.substring(1));
	var r = (rgb >> 16) & 0xFF;
	var g = (rgb >> 8) & 0xFF;
	var b = rgb & 0xFF;
	
	return 'rgba(' + r + ',' + g + ',' + b + ',' + alpha + ')';	
}

// TODO: Some code dup w/ above
function GetForegroundColourForAnnotation(anno) {
	if (anno === undefined || anno.fgColor === undefined) {
		return 'rgba(0,0,0,0)';
	}
	
	var alpha = anno.fgAlpha;
	if (alpha === undefined) {
		alpha = 1.0;
	}
	
	if (alpha === 0) {
		return 'rgba(0,0,0,0)';
	}

	// Uggghh...may have chose wrong on that serialisation... -_-
	var fgColHex = anno.fgColor;
	var rgb = parseInt('0x' + fgColHex.substring(1));
	var r = (rgb >> 16) & 0xFF;
	var g = (rgb >> 8) & 0xFF;
	var b = rgb & 0xFF;
	
	return 'rgba(' + r + ',' + g + ',' + b + ',' + alpha + ')';	
}

// TODO: Better home for this...
var annoIDToHTMLMap = {};

// So we can't set :hover css stuff in JS directly, so we instead
// create new styles and put them in HEAD
// MARK(cleanup): Remove these on teardown
function AddBorderStyles(annoBorders, highlightCursorStyles) {
	var css = "";
	for (var annoID in annoBorders) {
		
		var col = annoBorders[annoID];
		
		// 'table td:hover{ background-color: #00ff00 }';
		css += '#' + annoID + "{ border-style: solid; border-width: 1px; border-color: rgba(0,0,0,0); }" + " #" + annoID + ":hover { border-style: solid; border-width: 1px; border-color: " + col + "; cursor: pointer; }\n" 
		//css += '#' + annoID + ":hover { border-style: solid; border-width: 1px; border-color: " + col + "; }\n" 
	}
	
	for (var annoID in highlightCursorStyles) {
		css += '#' + annoID + ":hover { cursor: pointer; }\n";
	}

	var style = document.createElement('style');

	if (style.styleSheet) {
		style.styleSheet.cssText = css;
	} else {
		style.appendChild(document.createTextNode(css));
	}

	document.getElementsByTagName('head')[0].appendChild(style);
}

// In form XhXXmXXs, or XXmXXs or XXs
// return number of seconds as Number
function ParseURLTimeCode(timecode) {
	var hours = 0;
	var minutes = 0;
	var seconds = 0;
	if (timecode.includes("h")) {
		var parts = timecode.split('h');
		hours = parseFloat(parts[0]);
		timecode = parts[1];
	}
	
	if (timecode.includes("m")) {
		var parts = timecode.split('m');
		minutes = parseFloat(parts[0]);
		timecode = parts[1];
	}
	
	if (timecode.includes("s")) {
		var parts = timecode.split('s');
		seconds = parseFloat(parts[0]);
	}
	
	return hours * 3600 + minutes * 60 + seconds;
}

function ParseTimeFromVideoURL(url) {
	var anchorParts = url.split('#');
	if (anchorParts.length == 2) {
		var anchorPart = anchorParts[1];
		if (anchorPart.startsWith('t=')) {
			return ParseURLTimeCode(anchorPart.substring(2));
		}
	}
	
	// TODO: Query param as well
	
	return null;
}

function AnnotationNavigate(linkData) {
	if (linkData.url.startsWith("https://www.youtube.com/watch?")) {
		var query = linkData.url.split('?')[1].split('#')[0];
		var queryParts = query.split('&');
		var queryData = {};
		for (var idx in queryParts) {
			var part = queryParts[idx];
			var kv = part.split('=');
			if (kv.length === 2) {
				queryData[kv[0]] = kv[1];
			} else {
				console.log("Error parsing kv: '" + part + "'");
			}
		}
		
		var videoID = queryData['v'];
		if (videoID !== undefined) {
			
			var time = ParseTimeFromVideoURL(linkData.url);
			console.log("Navigate to: " + videoID + ' time: ' + time);
			
			LoadUpVideo(videoID, time);
		}
	}
}

function BlockOutAnnotations(annoData) {
	var anno_render = document.getElementById('anno_render');
	
	// Clear out children
	// TODO: Perf, and all that
	while (anno_render.firstChild) {
		anno_render.removeChild(anno_render.firstChild);
	}
	
	var videoWidth = anno_render.clientWidth;
	var videoHeight = anno_render.clientHeight;
	
	var annoIDMap = {};
	
	for (var idx in annoData.annotations) {
		var anno = annoData.annotations[idx];
		annoIDMap[anno.id] = anno;
	}
	
	var borderStyle = {};
	var highlightCursorStyles = {};
	
	for (var idx in annoData.annotations) {
		var anno = annoData.annotations[idx];

		if (anno.seg !== undefined) {			
			var annotationElem = document.createElement('div');
			
			annoIDToHTMLMap[anno.id] = annotationElem;
			
			
			annotationElem.classList.add('text_annotation');
			annotationElem.id = anno.id;

			annotationElem.style.width = (anno.seg.rect.w / 100.0 * videoWidth) + 'px';
			annotationElem.style.height = (anno.seg.rect.h / 100.0 * videoHeight) + 'px';

			background = GetBackgroundColourForAnnotation(anno);
			foreground = GetForegroundColourForAnnotation(anno);
			if (anno.type !== 'highlight') {
				annotationElem.style.background = background;
				annotationElem.style.color = foreground;
			} else {
				annotationElem.style.background = 'rgba(0,0,0,0)';
				annotationElem.style.borderWidth = anno.highlightWidth + 'px';
				annotationElem.style.borderColor = 'rgba(255,255,255,' + anno.borderAlpha + ')';
				annotationElem.style.borderStyle = 'solid';
			}
			
			if (anno.action !== undefined) {
				// Avoid closure-by-reference on action.link +_+
				(function(anno) {
					var action = anno.action;
					if (action.type === 'link') {
						if (action.trigger === 'click') {
							// We already apply border styling to highlights, and it's not on hover, it's always
							if (anno.type !== 'highlight') {
								borderStyle[anno.id] = foreground;
							} else {
								highlightCursorStyles[anno.id] = 1;
							}
						
							annotationElem.onclick = function() {
								AnnotationNavigate(action.link);
							};
						}
					}
				})(anno);
			}
			
			var x = anno.seg.rect.x;
			var y = anno.seg.rect.y;
			
			if (anno.seg.relativeTo !== undefined) {
				var parentAnno = annoIDMap[anno.seg.relativeTo];
				if (parentAnno === undefined || parentAnno === null) {
					console.log("Warning: Undefined reference to annotation '" + anno.seg.relativeTo + "'");
				} else {
					// TODO: More than one level of nesting?
					x += parentAnno.seg.rect.x;
					y += parentAnno.seg.rect.y;
				}
			}
			
			annotationElem.style.left = (x / 100.0 * videoWidth) + "px";
			annotationElem.style.top  = (y / 100.0 * videoHeight) + "px";
			
			// TODO: More responsize way of doing this? 
			annotationElem.style.fontSize = 4.8 * anno.textSize + 'px';

			if (anno.text !== undefined) {
				annotationElem.innerHTML = anno.text;
			} else {
				annotationElem.innerHTML = '';
			}
			
			annotationElem.style.display = 'none';
			anno_render.appendChild(annotationElem);
		} else {
			console.log(anno);
		}
	}
	
	AddBorderStyles(borderStyle, highlightCursorStyles);
	
	for (var idx in annoData.annotations) {
		// Arrrggghhhhh JavaScript why
		(function(idx) {
			var anno = annoData.annotations[idx];
			var annoHTMLElem = annoIDToHTMLMap[anno.id];

			if (anno.type === "text") {
				if (anno.seg !== undefined) {
					if (!anno.seg.timingShow) {
						var mouseOverID = anno.showOnMouseOver;
						if (mouseOverID !== undefined) {
							var mouseOverElem = annoIDToHTMLMap[mouseOverID];
							if (mouseOverElem !== undefined) {
								mouseOverElem.onmouseenter = function() {
									annoHTMLElem.style.display = 'block';
								};
								
								mouseOverElem.onmouseleave = function() {
									annoHTMLElem.style.display = 'none';
								};
							} else {
								 console.log("Error: Cannot find annotation w/ id '" + mouseOverID + "'");
							}
						}
					}
				}
			}
		})(idx);
	}
}

// Turn on and off annotations based on what the current time is
// TODO: Get time from YT video instead
function RenderAnnotations(annoData, currentTime) {
	if (window.bnsPrevRenderedTime === undefined || window.bnsPrevRenderedTime !== currentTime) {	
		window.bnsPrevRenderedTime = currentTime;
		var anno_render = document.getElementById('anno_render');
		
		var videoWidth = anno_render.clientWidth;
		var videoHeight = anno_render.clientHeight;
		for (var idx in annoData.annotations) {
			var anno = annoData.annotations[idx];
			if (anno.seg !== undefined) {
				annotationElem = annoIDToHTMLMap[anno.id];
				
				if (window.bnsDisableAllAnnotations) {
					annotationElem.style.display = 'none';
					continue;
				}
				
				if (anno.seg.timingShow) {
					if (currentTime > anno.seg.startTime && currentTime <= anno.seg.endTime) {
						annotationElem.style.display = 'block';
					} else {
						annotationElem.style.display = 'none';
					}
				}
			}
		}
	}
}

// Barack, Paper, Scissor Level 1 Start: l2mcdS6ioo8
// Interactive shooter: iCnlAC4OM38

function LoadUpVideo(videoID, time) {
	
	if (window.bnsCurrentVidID === undefined || window.bnsCurrentVidID !== videoID) {
		var xhr = new XMLHttpRequest();

		xhr.open("GET", "/anno/" + videoID);
		xhr.onreadystatechange = function () {
		  if(xhr.readyState === 4 && xhr.status === 200) {
			ParseAnnotationsForVideoIDIntoJSON(xhr.responseText, function(annoData) {
					console.log(annoData);
					var vidTime = document.getElementById('vid_time');
					var vidTimeLabel = document.getElementById('vid_time_label');
					
					BlockOutAnnotations(annoData);
					
					setInterval(function() {					
						var currentTime = 0;
						if (window.bnsYTPlayer !== null && window.bnsYTPlayer !== undefined && window.bnsYTPlayer.getCurrentTime !== undefined) {
							currentTime = window.bnsYTPlayer.getCurrentTime();
						}

						RenderAnnotations(annoData, currentTime);
					}, 100);
				});
		  }
		};
		xhr.send();
	}
	
	// This checks if the videoID in  the URL is different internally, so shouldn't cause spurious loading
	PlayYTVideo(videoID, time);
	
	window.bnsCurrentVidID = videoID;
	
	// TODO: Also set Youtube Embed URL
	
}



window.onload = function() {
	LoadUpVideo('iCnlAC4OM38', null)
};

function OnAnnotationEnableBox() {
	window.bnsDisableAllAnnotations = (document.getElementById('disable_anno_button').checked != true);
}

