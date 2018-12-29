
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
function AddBorderStyles(annoBorders) {
	var css = "";
	for (var annoID in annoBorders) {
		
		var col = annoBorders[annoID];
		
		// 'table td:hover{ background-color: #00ff00 }';
		css += '#' + annoID + "{ border-style: solid; border-width: 1px; border-color: rgba(0,0,0,0); }" + " #" + annoID + ":hover { border-style: solid; border-width: 1px; border-color: " + col + "; cursor: pointer; }\n" 
		//css += '#' + annoID + ":hover { border-style: solid; border-width: 1px; border-color: " + col + "; }\n" 
		
		
	}

	var style = document.createElement('style');

	if (style.styleSheet) {
		style.styleSheet.cssText = css;
	} else {
		style.appendChild(document.createTextNode(css));
	}

	document.getElementsByTagName('head')[0].appendChild(style);
}

function AnnotationNavigate(linkData) {
	console.log("AnnotationNavigate:");
	
	if (linkData.url.startsWith("https://www.youtube.com/watch?")) {
		var query = linkData.url.split('?')[1];
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
			console.log("Navigate to: " + videoID);
			LoadUpVideo(videoID);
		}
	}
	
	console.log(linkData);
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
	
	for (var idx in annoData.annotations) {
		var anno = annoData.annotations[idx];

		if (anno.seg !== undefined) {			
			var annotationElem = document.createElement('div');
			
			console.log("anno id: " + anno.id + " (type = '" + anno.type + "')");
			annoIDToHTMLMap[anno.id] = annotationElem;
			
			
			annotationElem.classList.add('text_annotation');
			annotationElem.id = anno.id;

			annotationElem.style.width = (anno.seg.rect.w / 100.0 * videoWidth) + 'px';
			annotationElem.style.height = (anno.seg.rect.h / 100.0 * videoHeight) + 'px';

			background = GetBackgroundColourForAnnotation(anno);
			if (anno.type !== 'highlight') {
				annotationElem.style.background = background;
				
				if (anno.action !== undefined) {
					// Avoid closure-by-reference on action.link +_+
					(function() {
						var action = anno.action;
						if (action.type === 'link') {
							if (action.trigger === 'click') {
								foreground = GetForegroundColourForAnnotation(anno);
								borderStyle[anno.id] = foreground;
							}
							
							annotationElem.onclick = function() {
								AnnotationNavigate(action.link);
							};
						}
					})();
				}
			} else {
				annotationElem.style.background = 'rgba(0,0,0,0)';
				annotationElem.style.borderWidth = anno.highlightWidth + 'px';
				annotationElem.style.borderColor = 'rgba(255,255,255,' + anno.borderAlpha + ')';
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
				annotationElem.innerHTML = '##';
			}
			
			annotationElem.style.display = 'none';
			anno_render.appendChild(annotationElem);
		} else {
			console.log(anno);
		}
	}
	
	AddBorderStyles(borderStyle);
	
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
		console.log("window.bnsDisableAllAnnotations: " + window.bnsDisableAllAnnotations);
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
					if (currentTime >= anno.seg.startTime && currentTime <= anno.seg.endTime) {
						annotationElem.style.display = 'block';
					} else {
						annotationElem.style.display = 'none';
					}
				}
			}
		}
	}
}

// Used for local development, but similar loading function for XHR will come later
//function onFileInput() {
//	var x = document.getElementById("myFile");
//    if (x.files !== null && x.files !== undefined) {
//        if (x.files.length >= 0) {
//            for (var i = 0; i < x.files.length; i++) {
//                var reader = new FileReader();
//				reader.readAsText(x.files[0], "UTF-8");
//				reader.onload = function (evt) {
//					ParseAnnotationsForVideoIDIntoJSON(evt.target.result, function(annoData) {
//						var vidTime = document.getElementById('vid_time');
//						var vidTimeLabel = document.getElementById('vid_time_label');
//						
//						window.bnsCurrentVidTime = vidTime.value;
//						
//						BlockOutAnnotations(annoData);
//						
//						vidTime.oninput = function() {
//							window.bnsCurrentVidTime = vidTime.value;
//							vidTimeLabel.innerHTML = vidTime.value + ' seconds';
//							RenderAnnotations(annoData);
//						};
//					});
//				}
//				reader.onerror = function (evt) {
//					console.log("Splits file could not be parsed -- Is this a version 1.7.0 file? Is it XML?");
//				}
//            }
//        }
//    }
//}

// l2mcdS6ioo8
// iCnlAC4OM38

function LoadUpVideo(videoID) {
	
	var xhr = new XMLHttpRequest(),
		method = "GET",
		url = "https://developer.mozilla.org/";

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
	
	// TODO: Also set Youtube Embed URL
	PlayYTVideo(videoID);
}



window.onload = function() {
	LoadUpVideo('l2mcdS6ioo8')
};

function OnAnnotationEnableBox() {
	window.bnsDisableAllAnnotations = (document.getElementById('disable_anno_button').checked != true);
}

