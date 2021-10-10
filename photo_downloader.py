# tool for downloading random photos from various sites

import config
from core import *
from adjectives import *

class PhotoDownloader():

    # on init, set up a webdriver, ready to download from various sites
    def __init__(self):
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--remote-debugging-port=9222") # https://stackoverflow.com/a/56638103/13100363
        #options.add_argument("--headless")
        options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome("/usr/local/bin/chromedriver",options=options)
        self.driver.implicitly_wait(10)

    # save an image once the url is found
    def download_image(self,source_url):
        path = config.path_extension + "image.jpg"
        with requests.get(source_url, stream=True) as r:
            with open(path, "wb") as f:
                f.write(r.content)

    # choose a photo site and execute the function to download from it
    def download_from_random_site(self):
        sites = [                           # functions are objects, so we can name them
            self.flickr,                    # and treat them like this, then call below with ()
            self.stocksnap,
            self.unsplash
            #self.pixabay                   # remove for now; it's too slow
        ]
        choices(sites,weights=[0.1,0.45,0.45],k=1)[0]()     # calls the chosen function, weight against flickr

    # tailored routines to download from the individual sites; all quite similar
    def flickr(self):

        print("Searching flickr…")

        # build URL with preferences
        url = "https://www.flickr.com/search/?"
        url += ("text=" + choice(adjectives).replace(" ", "%20") + "&")
        url += "license=1%2C2%2C9%2C10&"        # modifications allowed

        self.driver.get(url)
        image_elements = self.driver.find_elements_by_class_name("overlay")

        # get the URLs of the specific image pages and choose one
        # if nothing is found, run again on another random adjective
        image_urls = []
        for element in image_elements:
            image_urls.append(element.get_attribute("href"))
        if image_urls == []:
            return self.download_from_random_site()     # maybe try another site in case this is broken (cannot repeat one site)
        else:
            image_url = choice(image_urls)

        # get the source URL of the image from its specific page + download
        self.driver.get(image_url + "sizes/l/")
        source_url = self.driver.find_element_by_id("allsizes-photo").find_element_by_tag_name("img").get_attribute("src")
        self.download_image(source_url)

    def stocksnap(self):

        print("Searching stocksnap…")

        url = "https://stocksnap.io/search/" + choice(adjectives).replace(" ", "%20")
        self.driver.get(url)
        
        image_elements = self.driver.find_elements_by_class_name("photo-grid-item")

        image_urls = []
        for element in image_elements:
            if element.get_attribute("class") == "photo-grid-item":      # exclude sponsored
                image_urls.append(element.find_element_by_tag_name("a").get_attribute("href"))
        if image_urls == []:
            return self.download_from_random_site()
        else:
            image_url = choice(image_urls)
        
        self.driver.get(image_url)
        source_url = self.driver.find_element_by_tag_name("figure").find_element_by_tag_name("img").get_attribute("src")
        self.download_image(source_url)
    
    def unsplash(self):

        print("Searching unsplash…")

        url = "https://unsplash.com/s/photos/" + choice(adjectives).replace(" ", "%20")
        self.driver.get(url)
        
        image_elements = self.driver.find_elements_by_class_name("oCCRx")

        image_urls = []
        for element in image_elements:
            if element.get_attribute("class") == "oCCRx":      # exclude ad images if no results
                image_urls.append(element.get_attribute("src"))

        if image_urls == []:
            return self.download_from_random_site()
        else:
            image_url = choice(image_urls)
        
        self.download_image(image_url)

    def pixabay(self):

        print("Searching pixabay…")

        url = "https://pixabay.com/images/search/" + choice(adjectives).replace(" ", "%20")
        self.driver.get(url)
        
        image_elements = self.driver.find_elements_by_class_name("container--3NC_b")

        image_urls = []
        for element in image_elements:
            image_urls.append(element.find_element_by_tag_name("a").get_attribute("href"))
        if image_urls == []:
            return self.download_from_random_site()
        else:
            image_url = choice(image_urls)
        
        self.driver.get(image_url)
        source_url = self.driver.find_element_by_tag_name("img").get_attribute("srcset").split(" ")[0]
        self.download_image(source_url)