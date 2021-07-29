import config
from core import *

def run():
    setPathExtension()
    band = generateBandName()
    title = generateAlbumTitle()
    review = generateAlbumReview()
    getImage()
    createAlbumCover(band,title)
    print("\"" + title + "\" by " + band)
    print(review["quote"],"–",review["magazine"])

run()
#createAlbumCover("band","title")