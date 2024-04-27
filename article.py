import os
import re

# Stores content and meta data of an article, treated as two types. Those treated as books (with chapters and ToC) and those treated as only articles (without chapters)

class Article:
    title = ""
    authors = []

    def __init__(self, body, link, title, issue):
        self.body = body
        self.link = link
        self.issue = issue
        self.title = title

    def parse(self):
        pass

    # Cleans up the html for epub
    def clean_html(self):
        # Remove linkbacks
        linkbacks = self.body.find_all(class_="linkback")
        for linkback in linkbacks:
            linkback.decompose()
        # Remove infobox
        info_boxes = self.body.find_all(class_="info")
        for info in info_boxes:
            info.decompose()           
        # Remove from box
        from_boxes = self.body.find_all(class_="from")
        for from_box in from_boxes:
            from_box.decompose()   
        # Remove infobox
        top_link = self.body.find(class_="toplink")
        if top_link != None:
            top_link.decompose()               
        # Remove dates
        dates = self.body.find_all(class_="updat")
        for date in dates:
            date.decompose()
        # Remove first h4 (journal title)
        journal_title = self.body.find("h4")
        if journal_title != None:
            journal_title.decompose()
        # Remove divider lines
        lines = self.body.find_all("hr")
        for line in lines:
            line.decompose()

    def write_to_html(self):
        self.clean_html()
        file_name = self.title.lower()  # Convert to lower case
        file_name = file_name.replace(' ', '_')  # Replace spaces with underscores
        file_name = re.sub(r'\W', '', file_name)  # Remove all special characters
        print(f"Writing chapter {file_name} to file")
        os.makedirs(f"issues/{self.issue}", exist_ok=True)
        with open(os.path.join(f"issues/{self.issue}", f"{file_name}.html"), "w", encoding="utf-8") as file:
            file.write(self.body.prettify())