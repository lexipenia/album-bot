#TODO: control for file format; also for non-English citations

import config
from core import *

def run():

    print("---\nRunning album-bot.py at",str(datetime.now()))
    setPathExtension()
    
    print("Generating band name…")
    band = generateBandName()
    print("Band name generated.")

    print("Generating album title…")
    title = generateAlbumTitle()
    print("Album name generated.")

    print("Generating review…")
    review = generateAlbumReview()
    print("Review generated.")

    print("Downloading an image…")
    getImage()
    print("Image downloaded.")

    print("Creating a cover…")
    createAlbumCover(band,title)
    print("Cover created.")

    print("Creating Twitter image with review…")
    createTwitterImage(review)
    print("Twitter image created successfully.")
    
    print("---\n\"" + title + "\" by " + band)
    print(review["quote"],"–",review["magazine"])

run()