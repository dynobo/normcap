import sys

import pyocr
import pyocr.builders
from PIL import Image

tools = pyocr.get_available_tools()
if len(tools) == 0:
    print("No OCR tool found")
    sys.exit(1)
# The tools are returned in the recommended order of usage
tool = tools[0]
print("Will use tool '%s'" % (tool.get_name()))
# Ex: Will use tool 'libtesseract'

langs = tool.get_available_languages()
print("Available languages: %s" % ", ".join(langs))
lang = langs[0]
print("Will use lang '%s'" % (lang))
# Ex: Will use lang 'fra'
# Note that languages are NOT sorted in any way. Please refer
# to the system locale settings for the default language
# to use.


line_and_word_boxes = tool.image_to_string(
    Image.open("temp.png"), lang="deu", builder=pyocr.builders.LineBoxBuilder()
)

for lb in line_and_word_boxes:
    print(lb.word_boxes)
    print(lb.content)
    print(lb.position)
