The YouTube Annotation Format
================

_NOTE:_ None of the information in this document was obtained by looking at the source code of the YouTube watch page. It is simply a matter of looking at the annotation files and the corresponding rendered video pages and figuring out what different aspects of it mean, or by referencing publicly available online tutorials.

Annotations files looks something like:

```
<document>
<annotations>
	<annotation ...>...</annotation>
	.
	.
	.
</annotations>
</document>
```

## The Basics

The annotation element can have a few attributes:
	
- _id_: An id for the annotation, unique within the file, though doesn't seem like enough bits to be globally unique
- _type_: A broad category for the annotation. There are:
	    - _text_
		- _highlight_ (there are several things called highlight, it may get confusing)
- _style_: A sub-category for text-type annotations. These are the categories most people are familiar within
	    - _anchored_: Speech bubbles
		- _highlightText_: Text that shows up on mouse over of another annotation (such as a highlight)
		- _label_: An annotation that has a box, and text that shows up on mouse over (but it looks different than highlightText, and is a single annotation)
		- _popup_: A basic coloured square with some text that shows up
		- _title_: Another primarily text-based annotation (??? This one seems redundant to me)

## Segments and Positioning
		
A child of any visible annotations is the `<segment>` element. The segment contains both positional information, and timing information. A segment consists of a single child `<movingRegion>` element. The movingRegion element has an attribute `type` that can be either `anchored` or `rect`. Anchored are used for anchored-style annotations (speech bubbles).

An anchored-type movingRegion element will have two `<anchoredRegion>` child elements. A rect-type movingRegion will have two `<rectRegion>` child elements. Both anchoredRegion and rectRegion have the following attributes:

- `x`, `y` for position relative to upper-left corner of video (percentage, so in range [0, 100])
- `w`, `h` for width and height, also in percentage of video frame.
- `t` the time that this rect is for, in format `[H:]MM:SS.sss` ([hours :] minutes : seconds with decimal), or the string `'never'`.

anchoredRegion elements also have the attributes `sx` and `sy`, which control where the tip of the speech bubble is placed. Currently, it's unclear how the bubble itself is rendered.

An example rect-type movingRegion would be as follows:

```
<movingRegion type="rect">
	<rectRegion x="33.33333" y="0.000" w="33.33333" h="100.00" t="0:02:03.25"/>
	<rectRegion x="33.33333" y="0.000" w="33.33333" h="100.00" t="0:02:17.0"/>
</movingRegion>
```

This annotation would encompass the horizontal middle third of the screen, and show up at 2 minutes, 3.25 seconds and go away at 2 minutes, 17 seconds.

While it may be possible that annotations can be animated, I have not seen any examples so it's unclear if this is valid.

An annotation with the time set to 'never' will not show up based on time, but may be made visible by other things, like mousing over another annotation.
	
Note that the "video frame" _appears_ to be	solely the rendered video. I.e, for a video with a non-standard aspect ratio that ends up being letterboxed, the letterboxing/black bars do not count as part of the video frame.

## Text

This is rather straightforward. Certain annotations can have a `<TEXT>` child element. The text within that tag is the text of the annotation.

## Appearance

An annotation also has a child `<appearance>` element. This element has several possible attributes, most of which are optional depending on the annotation type.

 TODO: Explain all of these

 - _bgAlpha_
 - _bgColor_
 - _fgColor_
 - _highlightWidth_
 - _borderAlpha_
 - _textSize_
 - _highlightFontColor_
 - _effects_
 - _fontWeight_
