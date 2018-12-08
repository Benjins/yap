
function GetXMLChildWithName(node, name, idx) {
	for (var i = 0; i < node.children.length; i++) {
		if (node.children[i].tagName == name) {
			idx--;
			if (idx < 0) {
				return node.children[i];
			}
		}
	}
	
	return null;
}

function GetAllXMLChildrenWithName(node, name) {
	var children = [];
	for (var i = 0; i < node.children.length; i++) {
		if (node.children[i].tagName == name) {
			children.push(node.children[i]);
		}
	}

	return children;
}

/*
			
	

*/

/*

*/

function IsRectSegment(segElem) {
    var rectRegion = GetXMLChildWithName(GetXMLChildWithName(segElem, 'movingRegion', 0), 'rectRegion', 0);
    return rectRegion !== null;
}

function IsAnchoredSegment(segElem) {
	var anchoredRegion = GetXMLChildWithName(GetXMLChildWithName(segElem, 'movingRegion', 0), 'anchoredRegion', 0);
    return anchoredRegion !== null;
}

// t="0:00:00.0"
function ParseTimeCode(timeCode) {
    var parts = timeCode.split(':');
    if (parts.length === 3){
        return parseFloat(parts[0]) * 3600 + parseFloat(parts[1]) * 60 + parseFloat(parts[2]);
    } else if(parts.length === 2) {
        return parseFloat(parts[0]) * 60 + parseFloat(parts[1]);
    } else {
        return parseFloat(parts[0]);
	}
}

// Returns (x, y, w, h, t0, t1)
// Assumes that the x,y,w,h in each region are the same...seems to be the case most/all of the time?
function ParseRectSegment(segElem) {
    var rectRegions = GetAllXMLChildrenWithName(GetXMLChildWithName(segElem, 'movingRegion', 0), 'rectRegion');

    var x = parseFloat(rectRegions[0].attributes.x.value);
    var y = parseFloat(rectRegions[0].attributes.y.value);
    var w = parseFloat(rectRegions[0].attributes.w.value);
    var h = parseFloat(rectRegions[0].attributes.h.value);

    var t0 = rectRegions[0].attributes.t.value;
    var t1 = rectRegions[1].attributes.t.value;
    // TODO: Better way of representing this...
    if (t0 === 'never' || t1 === 'never') {
        t0 = 0;
        t1 = 0;
	} else {
        t0 = ParseTimeCode(t0);
        t1 = ParseTimeCode(t1);
	}
    return [x, y, w, h, t0, t1];
}

// Returns (x, y, w, h, sx, sy, t0, t1)
// TODO: d as well?
function ParseAnchoredSegment(segElem) {
    var rectRegions = GetAllXMLChildrenWithName(GetXMLChildWithName(segElem, 'movingRegion', 0), 'anchoredRegion');
	//segElem.find('movingRegion').findall('anchoredRegion')

    var x = parseFloat(rectRegions[0].attributes.x.value);
    var y = parseFloat(rectRegions[0].attributes.y.value);
    var w = parseFloat(rectRegions[0].attributes.w.value);
    var h = parseFloat(rectRegions[0].attributes.h.value);
    
    var sx = parseFloat(rectRegions[0].attributes.sx.value);
    var sy = parseFloat(rectRegions[0].attributes.sy.value);
    
	var t0 = rectRegions[0].attributes.t.value;
    var t1 = rectRegions[1].attributes.t.value;

    if (t0 === 'never' || t1 === 'never') {
        t0 = 0;
        t1 = 0;
	} else {
        t0 = ParseTimeCode(t0);
        t1 = ParseTimeCode(t1);
	}
    return [x, y, w, h, sx, sy, t0, t1];
}

function ParseActionElem(actionElem) {
    var action = {};
    if (actionElem.attributes.trigger.value === 'click') {
        action['trigger'] = 'click';
	}
    
    if (actionElem.attributes.type.value === 'openUrl') {
        action['type'] = 'link';
        var urlElem = GetXMLChildWithName(actionElem, 'url', 0);
        var link = {};
        if (urlElem.attributes.target != undefined && urlElem.attributes.target.value === 'current') {
            link['sameTab'] = true;
		} else {
            link['sameTab'] = false;
		}
        
        link['url'] = urlElem.attributes.value.value;
        
        action['link'] = link;
        
        return action;
	}

    return null;
}
    
function ParseSegmentElem(segmentElem) {
    if (IsAnchoredSegment(segmentElem)) {
		var ret = ParseAnchoredSegment(segmentElem);
        var x = ret[0], y = ret[1], w = ret[2], h = ret[3], sx = ret[4], sy = ret[5], t0 = ret[6], t1 = ret[7];
        var seg = {};
        seg['type'] = 'anchor';
        seg['rect'] = {'x': x, 'y': y, 'w': w, 'h': h};
        
        seg['sx'] = sx;
        seg['sy'] = sy;
        
        var relativeTo = segmentElem.attributes.spaceRelative;
        if (relativeTo!== null && relativeTo !== undefined) {
            seg['relativeTo'] = relativeTo.value;
		}
        
        if (t0 === 0 && t1 === 0) {
            seg['timingShow'] = false;
        } else {
            seg['timingShow'] = true;
            seg['startTime'] = t0;
            seg['endTime'] = t1;
		}
        
        return seg;
    } else if(IsRectSegment(segmentElem)) {
        var ret = ParseRectSegment(segmentElem);
        var x = ret[0], y = ret[1], w = ret[2], h = ret[3], t0 = ret[4], t1 = ret[5];
        var seg = {};
        seg['type'] = 'rect';
        seg['rect'] = {'x': x, 'y': y, 'w': w, 'h': h};
        
        var relativeTo = segmentElem.attributes.spaceRelative;
        if (relativeTo!== null && relativeTo !== undefined) {
            seg['relativeTo'] = relativeTo.value;
		}
        
        if (t0 === 0 && t1 === 0) {
            seg['timingShow'] = false;
        } else {
            seg['timingShow'] = true;
            seg['startTime'] = t0;
            seg['endTime'] = t1;
		}
        
        return seg;
	} else {
        console.log("Error: Incorrect segment element (doesn't have rect or anchored regions)");
        return null;
	}
}

function ParseTextAnnotationElement(annoElem, annoJS) {
	var textElem = GetXMLChildWithName(annoElem, 'TEXT', 0);
	var segmentElem = GetXMLChildWithName(annoElem, 'segment', 0);
	var appearanceElem = GetXMLChildWithName(annoElem, 'appearance', 0);
	
	if (segmentElem === null || appearanceElem === null) {
		console.log("Error: Text annotation w/o one of text or segment or appearancechild elements")
		return;
	} else {
		annoJS['type'] = 'text';
		
		var text = (textElem === null) ? "" : textElem.textContent;
		//console.log("  Text annotation w/ text: '" + text + "'");
		
		annoJS['text'] = text;
		
		var seg = ParseSegmentElem(segmentElem);
		if (seg !== null) {
			annoJS['seg'] = seg;
		}
		
		var action = GetXMLChildWithName(annoElem, 'action', 0);
		if (action !== null) {
			var actionJS = ParseActionElem(action);
			if (actionJS !== null) {
				annoJS['action'] = actionJS;
			}
		}

		var trigger = GetXMLChildWithName(annoElem, 'trigger', 0);
		if (trigger !== null) {
			var cond = GetXMLChildWithName(trigger, 'condition', 0);
			if (cond !== null) {
				var ref = cond.attributes.ref;
				var state = cond.attributes.state.value;
				// TODO: Other possible conditions?
				if (state === 'rollOver' && ref !== undefined) {
					annoJS['showOnMouseOver'] = ref.value;
				}
			}
		}
		
		var textSubtype = annoElem.attributes.style.value;
		
		if (textSubtype === 'popup') {
			annoJS['bgAlpha'] = parseFloat(appearanceElem.attributes.bgAlpha.value);
			annoJS['textSize'] = parseFloat(appearanceElem.attributes.textSize.value);
			annoJS['bgColor'] = '#' + parseInt(appearanceElem.attributes.bgColor.value).toString(16);
			annoJS['fgColor'] = '#' + parseInt(appearanceElem.attributes.fgColor.value).toString(16);
		} else if (textSubtype === 'highlightText') {
			annoJS['bgAlpha'] = parseFloat(appearanceElem.attributes.bgAlpha.value);
			annoJS['textSize'] = parseFloat(appearanceElem.attributes.textSize.value);
			annoJS['highlightFontColor'] = '#' + parseInt(appearanceElem.attributes.highlightFontColor.value).toString(16);
		} else if (textSubtype === 'speech') {
			annoJS['bgAlpha'] = parseFloat(appearanceElem.attributes.bgAlpha.value);
			annoJS['bgColor'] = '#' + parseInt(appearanceElem.attributes.bgColor.value).toString(16);
			annoJS['fgColor'] = '#' + parseInt(appearanceElem.attributes.fgColor.value).toString(16);
		} else if (textSubtype === 'anchored') {
			annoJS['bgColor'] = '#' + parseInt(appearanceElem.attributes.bgColor.value).toString(16);
			annoJS['fgColor'] = '#' + parseInt(appearanceElem.attributes.fgColor.value).toString(16);
			annoJS['textSize'] = parseFloat(appearanceElem.attributes.textSize.value);
		} else {
			console.log("  Unknown format for text annotation: '" + textSubtype + "'...");
		}
	}
}

function ParseHighlightAnnotationElement(annoElem, annoJS) {
    annoJS['type'] = 'highlight';
    
    var segmentElem = GetXMLChildWithName(annoElem, 'segment', 0);
    var appearanceElem = GetXMLChildWithName(annoElem, 'appearance', 0);

    var action = GetXMLChildWithName(annoElem, 'action', 0);
    if (action !== null) {
        var actionJS = ParseActionElem(action);
        if (actionJS !== null) {
            annoJS['action'] = actionJS;
		}
	}

    var seg = ParseSegmentElem(segmentElem);
    
    if (seg !== null) {
        annoJS['seg'] = seg;
	}

    annoJS['bgColor'] = '#' + parseInt(appearanceElem.attributes.bgColor.value).toString(16);
    annoJS['borderAlpha'] = parseFloat(appearanceElem.attributes.borderAlpha.value);
    annoJS['highlightWidth'] = parseInt(appearanceElem.attributes.highlightWidth.value);
}

function ParseAnnotationElement(annoElem) {
	var annoJS = {};
	annoJS['id'] = annoElem.attributes.id.value;
	
	var annoType = annoElem.attributes.type.value;
	if (annoType == 'text') {
		ParseTextAnnotationElement(annoElem, annoJS);
		return annoJS;
	} else if (annoType == 'highlight') {
		ParseHighlightAnnotationElement(annoElem, annoJS);
		return annoJS;
	} else {
		console.log("Skipping parsing annotation of type '" + annoType + "'");
	}
	
	return null;
}

function ParseAnnotationsForVideoIDIntoJSON(str, cb) {
	var parser = new DOMParser();
	var xmlDoc = parser.parseFromString(str, "text/xml");

	var doc = GetXMLChildWithName(xmlDoc, 'document', 0);
	var annotationsElem = GetXMLChildWithName(doc, 'annotations', 0);
	//console.log(annotationsElem);
	var annotationElements = GetAllXMLChildrenWithName(annotationsElem, 'annotation');

	var annoData = {};
	annoData['annotations'] = [];
	
	for (var idx in annotationElements) {
		var anno = ParseAnnotationElement(annotationElements[idx]);
		if (anno !== null) {
			annoData['annotations'].push(anno);
		}
	}
	
	console.log(annoData);
	
	cb(annoData);
}
