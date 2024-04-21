import os
import requests

# This file contains the class and methods to handle individual issues

class Issue:
    metadata = {
        "title": "",
        "authors": []
    }

    def __init__(self, body, url):
        self.body = body
        self.root_url = url
        self.name = body.find('a').get('id')
        self.chapters = []

    # Cleans up the html for epub, note this removes images so recommended to call "extract_cover_image" first if the image needs extracting
    def clean_html(self):
        # Remove images
        table = self.body.find('table')
        if table:
            table.decompose()
        # Remove linkbacks
        linkbacks = self.body.find_all(class_="linkback")
        for linkback in linkbacks:
            linkback.decompose()
        # Remove dates
        dates = self.body.find_all(class_="updat")
        for date in dates:
            date.decompose()
        # Remove divider lines
        lines = self.body.find_all("hr")
        for line in lines:
            line.decompose()

    def write_to_html(self):
        os.makedirs(f"issues/{self.name}", exist_ok=True)
        with open(os.path.join(f"issues/{self.name}", "index.html"), "w", encoding="utf-8") as file:
            file.write(self.body.prettify())

    def parse_chapters(self):
        # Get links on the page, we can tell if they are links to chapters if they have text content
        link_tags = self.body.find_all('a')

        # Loop through the found a_tags
        for tag in link_tags:
            # Check if the tag has a non-empty string
            if tag.string:
                print(f"Text Content: {tag.string}")
                print(f"Link: {tag.get('href')}")

    def extract_cover_image(self):
        # Find the last slash in the URL
        url_path_index = self.root_url.rfind("/")
        # Remove everything after the last slash
        url_no_path = self.root_url[:url_path_index]
        # Pull cover images
        image_tag = self.body.find("img")
        if(image_tag is not None):
            print(f"Creating {self.name}")
            # Download image
            image_url = f"{url_no_path}/{image_tag['src']}"
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:     
                # Open the file in write mode and download the image
                os.makedirs(f"issues/{self.name}/cover_images", exist_ok=True)
                with open(os.path.join(f"issues/{self.name}/cover_images", image_url.split("/")[-1]), 'wb') as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
