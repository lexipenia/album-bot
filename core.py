from sys import argv
from random import choice, choices, randint
from math import floor
import requests
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from PIL import Image, ImageFont, ImageDraw
import tweepy

import config
from photo_downloader import PhotoDownloader
from adjectives import *
from magazines import *
from fonts_list import *

# set environment variable for path extension within the config file
def setPathExtension():
    if "remote" in argv:                     
        config.path_extension = config.path_extensions["remote"]
    else:
        config.path_extension = config.path_extensions["local"]

# get the title of a random Wikipedia article as a band name
def generateBandName():

    print("Generating band name…")
    
    random_page = requests.get("https://en.wikipedia.org/wiki/Special:Random")
    soup = BeautifulSoup(random_page.content, "html.parser")
    title = soup.find(id="firstHeading").text

    # remove any bits in () and correct capitalization
    band_name = re.sub("\((.+)\)", "", title).strip().title().replace("\'S", "\'s")
    
    # control for stupidly long names
    if len(band_name) > 50:
        print("Name too long. Trying again.")
        return generateBandName()
    else:
        return band_name

# use the tail of a random quotation for the album name
def generateAlbumTitle():
    print("Generating album title…")
    quote = getRandomQuote()
    return extractPhrase(stripEndCharacters(quote))
    
# get the random quote for the album title
def getRandomQuote():

    # get all the <li> elements within a random Wikiquote page
    random_page = requests.get("https://en.wikiquote.org/wiki/Special:Random")
    soup = BeautifulSoup(random_page.content, "html.parser")
    article_body = soup.find(id="bodyContent")
    list_elements = article_body.find_all("li")

    # sort out the elements that are actually just quotes, not attributions or headers
    quotes = []
    for element in list_elements:
        if len(element.text) > 0:                   # avoid error if empty    
            if element.text[0] in "1234567890":     # skip numbered subheaders
                continue
            elif element.ul:  # where sub-list gives attribution           
                    element.ul.decompose()
                    quotes.append(element.text.replace("\\n", " ").strip())

    # make sure there was a result
    if quotes != []:
        return choice(quotes)
    else:
        print("No quotes found. Trying again…")
        return generateAlbumTitle()

# strip out unwanted characters at the end
def stripEndCharacters(text):
    output = text
    chracters = [".", "!", "\"", "\'","“","”","‘","’","(",")","[","]"]
    for char in chracters:
        output = output.replace(char, "")
    return output

# extract the final n words and format the quote
def extractPhrase(quote):
    tokenized_quote = quote.split(" ")
    length = randint(1,5)
    if length > len(tokenized_quote):
        return quote
    else:
        return " ".join(tokenized_quote[-length:]).title()

def generateAlbumReview():
    print("Generating review…")
    random_adjs = choices(adjectives,k=3)
    review = {
        "quote": "\"" + random_adjs[0].capitalize() + ", " + random_adjs[1] + ", " + random_adjs[2] + "\"",
        "magazine": choice(magazines),
        "rating": randint(1,10)
    }
    return review

# download a square image from flickr to use
def getImage():
    print("Downloading an image…")
    downloader = PhotoDownloader()
    downloader.download_from_random_site()
    downloader.driver.quit()        # ensure port closes; https://stackoverflow.com/a/67001770/13100363

# add the band name and album title to the image
def createAlbumCover(band,title):

    print("Adding text to image…")

    # set up image and choose a random font at 75pt
    image = Image.open(config.path_extension + "image.jpg")
    font = ImageFont.truetype(config.path_extension + "fonts/" + choice(fonts), 75, encoding="UTF-8")

    image = cropImageToSquare(image)
    
    # scale the image so that the longest text item just fits on, or width is 1000
    w, h = image.size
    length_band = font.getsize(band)[0]
    length_title = font.getsize(title)[0]
    max_width = max(length_band,length_title)
    big_image = False

    if max_width > 900:         # scale image all the way up to accomodate
        image = scaleImageWidth(image,max_width+100)
        big_image = True
    else:                       # scale image to 900
        image = scaleImageWidth(image,900)

    draw = ImageDraw.Draw(image)

    fill_colour = (0, 0, 0)
    stroke_colour = (0, 0, 0)

    # draw the image
    draw.multiline_text((10,10),band + "\n" + title,font=font,fill=fill_colour)

    # scale back down to 1000px before saving
    if big_image:
        image = scaleImageWidth(image,900)

    image.save(config.path_extension + "cover.jpg")

    print("Text added successfully!")

# crop an image to a square
def cropImageToSquare(image):

    # figure out if potrait or landscape orientation; just return if it's square
    w, h = image.size
    if w == h:
        return image
    elif w > h:
        landscape = True
    else:
        landscape = False

    # crop out the central square of the image
    if landscape:
        return image.crop(((w-h)/2,0,(w+h)/2,h))
    else:
        return image.crop((0,(h-w)/2,w,(h+w)/2))

# scale an image to a particular width
def scaleImageWidth(image,width):
    w, h = image.size
    scale_factor = width / w
    w, h = map(lambda x: int(floor(x * scale_factor)), (w, h))
    return image.resize((w,h),Image.ANTIALIAS)

# add the review + other information to the cover, create 1600 x 900 image
def createTwitterImage(band,title,review):
    pass