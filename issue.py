import os
import requests
import urllib3
import pypub
from article import Article
from bs4 import BeautifulSoup

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
        self.http = urllib3.PoolManager()

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

    def parse_metadata(self):
        # Get title
        self.metadata["title"] = self.body.find("h5").text
        # Get authors
        em_tags = self.body.find_all('em')
        authors = []
        for tag in em_tags:
            # get the preceding text
            tag_text = tag.text

            if tag_text.startswith('by '):
                # strip 'by '
                authors.append(tag_text[3:])
            elif tag_text.startswith('from '):
                # strip 'from '
                authors.append(tag_text[5:])

        authors = set(authors)
        self.metadata["authors"] = authors

    def parse_chapters(self):
        # Clean the html before parsing
        self.clean_html()
        # Get links on the page, we can tell if they are links to chapters if they have text content
        link_tags = self.body.find_all('a')
        # Loop through the found a_tags
        for tag in link_tags:
            # Check if the tag has a non-empty string
            if tag.string:
                print(f"Parsing chapter {tag.string}")
                article = self.http.request('GET', self.format_link(tag.get('href'))) 
                souped_article = BeautifulSoup(article.data, 'html5lib')
                self.chapters.append(Article(souped_article, self.format_link(tag.get('href')), tag.string, self.name, self.http))

    def extract_cover_image(self):
        # Find the last slash in the URL
        url_path_index = self.root_url.rfind("/")
        # Remove everything after the last slash
        url_no_path = self.root_url[:url_path_index]
        # Pull cover images
        image_tag = self.body.find("img")
        if(image_tag is not None):
            print(f"Extracting cover image of {self.name}")
            # Download image
            image_url = f"{url_no_path}/{image_tag['src']}"
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:     
                # Open the file in write mode and download the image
                os.makedirs(f"issues/{self.name}/cover_images", exist_ok=True)
                with open(os.path.join(f"issues/{self.name}/cover_images", image_url.split("/")[-1]), 'wb') as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)

    # Takes a link relative to a chapter and format it to its absolute path
    def format_link(self, chapter_link):
        # Count occurrences of relative path "up"
        prev_dir_count = chapter_link.count("../")
        # Remove occurrences
        non_relative_path = chapter_link.replace("../", "")
        # Remove path elements from root url
        path_elements = self.root_url.split("/")
        root_dir = path_elements[:-prev_dir_count - 1]

        return '/'.join(root_dir) + "/" + non_relative_path
    
    def parse(self):
        self.parse_metadata()
        #self.extract_cover_image()
        self.parse_chapters()
        for chapter in self.chapters:
            chapter.parse()
            chapter.write_to_html()

    def compile_to_epub(self):
        epub = pypub.Epub(self.name, creator=",".join(self.metadata['authors']))
        for chapter in self.chapters:
            epub.add_chapter(pypub.create_chapter_from_html(str.encode(chapter.get_content_as_html()), title=chapter.title))
        os.makedirs(f"issues/epub/", exist_ok=True)
        epub.create(f"issues/epub/{self.name}")