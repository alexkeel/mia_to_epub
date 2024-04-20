import os
import requests

# This file contains the class and methods to handle individual issues

class Issue:
    def __init__(self, body, url):
        self.body = body
        self.root_url = url
        self.name = body.find('a').get('id')

    def write_to_html(self):
        os.makedirs(f"issues/{self.name}", exist_ok=True)
        with open(os.path.join(f"issues/{self.name}", "index.html"), "w") as file:
            file.write(self.body.prettify())
        self.extract_cover_image()

    def extract_cover_image(self):
        # Find the last slash in the URL
        url_path_index = self.root_url.rfind("/")
        # Remove everything after the last slash
        url_no_path = self.root_url[:url_path_index]
        # Pull cover images
        image_tag = self.body.find("img")
        if(image_tag is not None):
            print(self.name)
            # Download image
            image_url = f"{url_no_path}/{image_tag['src']}"
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:     
                # Open the file in write mode and download the image
                os.makedirs(f"issues/{self.name}/cover_images", exist_ok=True)
                with open(os.path.join(f"issues/{self.name}/cover_images", image_url.split("/")[-1]), 'wb') as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)