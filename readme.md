# Granblue Fantasy Thumbnail Maker Remake  
* Tool to generate thumbnails for Granblue Fantasy videos.  
### Requirements  
* Tested on Python 3.11 and higher.  
* [pyperclip](https://pypi.org/project/pyperclip/) to read/write the clipboard.  
* [Pillow](https://pillow.readthedocs.io/en/stable/) for image processing.  
* [httpx](hhttps://github.com/encode/httpx) for network requests.  
* `pip install -r requirements.txt` to install all the modules.  
### Notes  
* This project is a rework of [GBFTM](https://github.com/MizaGBF/GBFTM).  
* It's compatible with [GBFPIB](https://github.com/MizaGBF/GBFPIB) version 9.0 or above.  
* Party data must be imported using the GBFPIB bookmark.  
### Templates  
Templates can be set in `template.json`.  
### Bosses  
Bosses can be set in `boss.json`.  
You can use the command line menu to set one or set it manually in the file.  
The format is an array of the following: `[Boss ID (appear sprite sheet), Background file name, Boss ID (icon)]`.  
You can find ID using [GBFAL](https://mizagbf.github.io/GBFAL/).  