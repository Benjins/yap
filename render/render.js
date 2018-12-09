
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

// TODO: Better home for this...
var annoIDToHTMLMap = {};

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
	
	for (var idx in annoData.annotations) {
		var anno = annoData.annotations[idx];

		if (anno.seg !== undefined) {			
			var annotationElem = document.createElement('div');
			
			console.log("anno id: " + anno.id);
			annoIDToHTMLMap[anno.id] = annotationElem;
			
			annotationElem.classList.add('text_annotation');

			annotationElem.style.width = (anno.seg.rect.w / 100.0 * videoWidth) + 'px';
			annotationElem.style.height = (anno.seg.rect.h / 100.0 * videoHeight) + 'px';

			background = GetBackgroundColourForAnnotation(anno);
			if (anno.type !== 'highlight') {
				annotationElem.style.background = background;
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
function RenderAnnotations(annoData) {
	var anno_render = document.getElementById('anno_render');
	
	var videoWidth = anno_render.clientWidth;
	var videoHeight = anno_render.clientHeight;
	
	for (var idx in annoData.annotations) {
		var anno = annoData.annotations[idx];

		if (anno.seg !== undefined) {
			annotationElem = annoIDToHTMLMap[anno.id];
			
			if (anno.seg.timingShow) {
				if (window.bnsCurrentVidTime >= anno.seg.startTime && window.bnsCurrentVidTime <= anno.seg.endTime) {
					annotationElem.style.display = 'block';
				} else {
					annotationElem.style.display = 'none';
				}
			}
		}
	}
}

// Used for local development, but similar loading function for XHR will come later
function onFileInput() {
	var x = document.getElementById("myFile");
    if (x.files !== null && x.files !== undefined) {
        if (x.files.length >= 0) {
            for (var i = 0; i < x.files.length; i++) {
                var reader = new FileReader();
				reader.readAsText(x.files[0], "UTF-8");
				reader.onload = function (evt) {
					ParseAnnotationsForVideoIDIntoJSON(evt.target.result, function(annoData) {
						var vidTime = document.getElementById('vid_time');
						var vidTimeLabel = document.getElementById('vid_time_label');
						
						window.bnsCurrentVidTime = vidTime.value;
						
						BlockOutAnnotations(annoData);
						
						vidTime.oninput = function() {
							window.bnsCurrentVidTime = vidTime.value;
							vidTimeLabel.innerHTML = vidTime.value + ' seconds';
							RenderAnnotations(annoData);
						};
					});
				}
				reader.onerror = function (evt) {
					console.log("Splits file could not be parsed -- Is this a version 1.7.0 file? Is it XML?");
				}
            }
        }
    }
}
