from sys import argv
from datetime import datetime
from random import choice, choices, randint
from math import floor
from statistics import mean, stdev
import requests
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from PIL import Image, ImageFont, ImageDraw
import tweepy

import config
from api_keys import *
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
        return getRandomQuote()

# strip out unwanted characters at the end
def stripEndCharacters(text):
    output = text
    chracters = [".", "!", "\"", "\'","“","”","‘","’","(",")","[","]"]
    for char in chracters:
        output = output.replace(char, "")
    return output

# extract the final n words and format the quote
def extractPhrase(quote):
    tokenized_quote = re.sub("[\s]{2,}"," ",quote).split(" ")   # regex control for multiple spaces
    length = randint(1,5)
    if length > len(tokenized_quote):
        return quote
    else:
        return " ".join(tokenized_quote[-length:]).title()

def generateAlbumReview():
    random_adjs = choices(adjectives,k=3)
    review = {
        "adjectives": random_adjs,
        "quote": "\"" + random_adjs[0].capitalize() + ", " + random_adjs[1] + ", " + random_adjs[2] + "\"",
        "magazine": choice(magazines),
    }
    return review

# download a square image from flickr to use
def getImage():
    downloader = PhotoDownloader()
    downloader.download_from_random_site()
    downloader.driver.quit()        # ensure port closes; https://stackoverflow.com/a/67001770/13100363

# add the band name and album title to the image
def createAlbumCover(band,title):

    # set up image and crop to square
    image = Image.open(config.path_extension + "image.jpg")
    image = cropImageToSquare(image)

    # choose a random font of size 75, calculate size of text area
    font = ImageFont.truetype(config.path_extension + "fonts/" + choice(fonts), 75, encoding="UTF-8")
    size_band = font.getsize(band)
    size_title = font.getsize(title)
    size_text = (max(size_band[0],size_title[0]),(size_band[1]+size_title[1]))

    #scale to size so that the longest text item just fits on, or width is 900
    max_width = size_text[0]
    big_image = False
    if max_width > 800:         # scale image all the way up to accommodate
        image = scaleImageWidth(image,max_width+100)
        big_image = True
    else:                       # scale image to 900
        image = scaleImageWidth(image,900)

    # variable for offset of text from corner + specify start points for width and height loops
    corner_offset = 30
    w,h = image.size
    image_areas = {
        "TL": (corner_offset,corner_offset),
        "TR": ((w - corner_offset - size_text[0]),corner_offset),
        "BL": (corner_offset,(h - corner_offset - size_text[1])),
        "BR": ((w - corner_offset - size_text[0]),(h - corner_offset - size_text[1]))
    }

    # analyze the image to find out where is best for text + whether to use black or white
    # will get a tuple of form ("TR",123) showing chosen corner + average b/w pixel value
    chosen_corner = analyzeImage(image,size_text,image_areas)

    # set text colour to black if the chosen corner is on average brighter, otherwise white
    if chosen_corner[1] < 128:
        fill_colour = (255,255,255)
    else:
        fill_colour = (0,0,0)

    # add the text to the image, choosing left/right alignment appropriately
    draw = ImageDraw.Draw(image)
    if chosen_corner[0] == "TR" or chosen_corner[0] == "BR":
        draw.multiline_text(image_areas[chosen_corner[0]],band + "\n" + title,font=font,fill=fill_colour,align="right")
    else:
        draw.multiline_text(image_areas[chosen_corner[0]],band + "\n" + title,font=font,fill=fill_colour)

    # scale back down to 900px (if necessary) before saving
    if big_image:
        image = scaleImageWidth(image,900)
    image.save(config.path_extension + "cover.jpg")

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

# test four image areas (TL,TR,BL,BR) that are the size of the text area and offset from the main corners.
# determine: (a) which corner has the least variation between light and dark; (b) if the corner is more light or dark
def analyzeImage(image,size_text,image_areas):

    pixels = image.load()

    # for each area record the average b/w pixel value (light/dark) + standard deviation of these values
    areas = {}
    for area, start_coords in image_areas.items():
        b_w_values = []     # value of each b_w_pixel
        for pixel_w in range(start_coords[0],start_coords[0] + size_text[0] + 1):
            for pixel_h in range(start_coords[1],start_coords[1] + size_text[1] + 1):
                r,g,b = pixels[pixel_w,pixel_h]
                b_w_pixel = mean([r,g,b])
                b_w_values.append(b_w_pixel)
        areas[area] = (stdev(b_w_values),mean(b_w_values))
    
    # return the most uniform area (lowest stdev) and its b/w pixel average
    most_uniform = (min(areas, key = lambda value : areas[value][0]))
    return (most_uniform,areas[most_uniform][1])

# add the review + other information to the cover, create 1600 x 900 image
def createTwitterImage(review):
    
    # set up black image and add existing cover
    final = Image.new("RGB",(1600,900))
    cover = Image.open(config.path_extension + "cover.jpg")
    final.paste(cover)

    # use Goudy for all reviews; 50 will fit on the largest adjective: "naked as the day you were born"
    font = ImageFont.truetype(config.path_extension + "fonts/Goudy Old Style Regular.ttf", 50, encoding="UTF-8")

    draw = ImageDraw.Draw(final)

    # add each adjective, centered, in an appropriate place, with punctuation
    # "align=center" is broken, hence having to calculate separately for each adjective
    size_adj = font.getsize(review["adjectives"][0])
    text_start = (700-size_adj[0])/2 + 900
    draw.text((text_start,200),text=review["adjectives"][0].capitalize() + ",",font=font,fill=(255,255,255))
    
    size_adj = font.getsize(review["adjectives"][1])
    text_start = (700-size_adj[0])/2 + 900
    draw.text((text_start,300),text=review["adjectives"][1] + ",",font=font,fill=(255,255,255))

    size_adj = font.getsize(review["adjectives"][2])
    text_start = (700-size_adj[0])/2 + 900
    draw.text((text_start,400),text=review["adjectives"][2] + ".",font=font,fill=(255,255,255))

    # add magazine, change font to ITALIC version
    font = ImageFont.truetype(config.path_extension + "fonts/Goudy Old Style ITALIC.ttf", 50, encoding="UTF-8")
    string_magazine = "— " + review["magazine"]
    length_magazine = font.getsize(string_magazine)
    text_start = (700-length_magazine[0])/2 + 900
    draw.multiline_text((text_start,550),text=string_magazine,font=font,fill=(255,255,255))

    # add stars, centered
    rating = randint(1,10)
    stars = Image.open(config.path_extension + "stars/" + str(rating) + ".png")
    final.paste(stars,(int(floor(1250-stars.width/2)),700))

    final.save(config.path_extension + "final.jpg")

# post everything to twitter
def postTweet(band,title):

    text = "“" + title + "” by " + band

    # authenticate and set up the Twitter bot
    try:
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        twitter = tweepy.API(auth)
    except Exception as e:
        print("Error authenticating with Twitter:",e)

    # upload the image
    try:
        review_image = twitter.media_upload(config.path_extension + "final.jpg")
    except Exception as e:
        print("Error uploading image:",e)

    # post the tweet with text
    try:
        twitter.update_status(status=text,media_ids=[review_image.media_id])
    except Exception as e:
        print("Error posting tweet:",e)