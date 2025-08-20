# Granblue Fantasy Thumbnail Maker Remake  
* Tool to generate thumbnails for Granblue Fantasy videos.  
### Requirements  
* Tested on Python 3.13 and higher.  
* [pyperclip](https://pypi.org/project/pyperclip/) to read/write the clipboard.  
* [Pillow](https://pillow.readthedocs.io/en/stable/) for image processing.  
* [aiohttp](https://docs.aiohttp.org/en/stable/) for network requests.  
* `pip install -r requirements.txt` to install all the modules.  
### Notes  
* This project is a rework of [GBFTM](https://github.com/MizaGBF/GBFTM).  
* It's compatible with [GBFPIB](https://github.com/MizaGBF/GBFPIB) version 12.0 or above.  
* Party data must be imported using the GBFPIB bookmark.  
### Templates  
Templates can be set in `template.json`.  
Possible types are:  
* `background`: Force the Background selection prompt to generate a background image.  
* `boss`: Similar to `background` but only generate the boss (No background image).  
* `party`: Check the clipboard for GBFPIB data to draw the party.  
* `autoinput`: Force the Auto Setting selection prompt.  
* `nminput`: Force the Unite and Fight / Dread Barrage / Records of the tens Fight/Nightmare icon selection prompt.  
* `textinput`: Force the Text input prompt.  
* `asset`: To display an asset. Filename must be set under the `asset` key.  
  
Additionaly, all elements (except `background` and `boss`) can have the following values set:
* `position`: An array of two integer, X and Y offset relative to the anchor.  
* `anchor`: Default position of the element. Default is `topleft`.  
* `size`: Float, size multiplier.  
  
For `party`:
* `noskin`: Boolean, set to True to not display skins.  
* `mainsummon`: Boolean, set to True to only display the main summon used.  
  
For `textinput`:
* `fontcolor`: Array of 3 or 4 integers (RGB or RGBA values), color of the text (Default is white)  
* `outlinecolor`: Array of 3 or 4 integers (RGB or RGBA values), color of the text outline (Default is red)  
* `fontsize`: Integer, text size (Default is 120)  
* `outlinesize`: Integer, size of the text outline (Default is 10)  
* `bold`: Boolean, set to True to draw bold text  
* `italic`: Boolean, set to True to draw italic text  
* `ljust`: Integer, to left align string lines   
* `rjust`: Integer, to right align string lines (Applied after `ljust`, if set)   
  
### Bosses  
Bosses can be set in `boss.json`.  
You can use the command line menu to set one or set it manually in the file.  
The format is an array of the following: `[Boss ID (appear sprite sheet), Background file name, Boss ID (icon)]`.  
You can find IDs using [GBFAL](https://mizagbf.github.io/GBFAL/).  
Alternatively, get the bookmark from the main menu to retrieve a boss data and directly paste it: It will automatically be processed as a valid boss.  