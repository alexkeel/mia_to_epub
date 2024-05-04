import os
import re
from bs4 import BeautifulSoup, NavigableString

'''
    Stores content and meta data of an article, treated as two types.
    Those treated as books (with chapters and ToC) and those treated
    as only articles (without chapters)
'''


class Article:
    title = ""
    authors = []
    chapters = []
    is_book = False

    def __init__(self, body, link, title, issue, http):
        self.body = body
        self.link = link.split("#")[0]
        print(self.link)
        self.issue = issue
        self.title = title
        self.http = http

    def parse(self):
        self.body = self.clean_html(self.body)
        # Check if this is to be treated as a book (does it have chapters)
        link_list = self.body.find(class_="link")

        if link_list is not None:
            print(f"{self.title} is probably in book form")
            main_body = self.body.find('body')
            main_body.contents = []
            # Get links on the page, we can tell if they are
            # links to chapters if they have text content
            link_tags = link_list.find_all('a')
            # Loop through the found a_tags
            for tag in link_tags:
                # Check if the tag has a non-empty string
                if tag.string:
                    if "#" in self.format_link(tag.get('href')):
                        # Contains a table of contents but also a body,
                        # standard method of parsing will duplicate
                        split_link = tag.get('href').split("#")
                        actual_link = split_link[0]
                        anchor_id = split_link[1]
                        # TODO This shouldn't run each time if the link is the same
                        if actual_link != "":
                            article = self.http.request('GET', self.format_link(actual_link))
                        else:
                            article = self.http.request('GET', self.link)
                        souped_article = BeautifulSoup(article.data, 'html5lib')
                        # Get the anchor tag
                        anchor_tag = souped_article.find(id=anchor_id)
                        # Get the content between this tag to the next tag
                        tags_in_between = []
                        for sibling in anchor_tag.parent.next_siblings:
                            if isinstance(sibling, NavigableString):
                                continue  # Ignore string siblings
                            if "link" in sibling.get('class', []):
                                break
                            tags_in_between.append(sibling)

                        new_content = ''.join(str(tag) for tag in tags_in_between)
                        # Parse the string with BeautifulSoup
                        souped_article = BeautifulSoup(new_content, 'html5lib')
                    else:
                        article = self.http.request('GET', self.format_link(tag.get('href')))
                        souped_article = BeautifulSoup(article.data, 'html5lib')

                    self.chapters.append(self.clean_html(souped_article))

            self.create_toc()
            for chapter in self.chapters:
                if chapter.body is not None:
                    chapter_body = self.clean_chapter(chapter.body)
                    main_body = self.body.find('body')
                    main_body.append(chapter_body)
                else:
                    print(chapter)

    def create_toc(self):
        toc = BeautifulSoup('<html><body></body></html>', 'html5lib')
        toc_body = toc.find('body')
        toc_big = toc.new_tag('big')
        for chapter in self.chapters:
            title = chapter.find("h3")
            if title is not None:
                # We give the title an ID to navigate to
                title['id'] = re.sub(r'\s+', '-', title.text.lower().replace(' ', '-'))
                # We create the link itself
                toc_entry = self.body.new_tag("a", href=f"#{title['id']}")
                toc_entry.string = title.text
                toc_big.append(toc_entry)
                toc_big.append(toc.new_tag('br'))
                toc_body.append(toc_big)
        self.chapters.insert(0, toc)

    # Takes a link relative to a chapter and format it to its absolute path
    # (TODO This should probably be in a utils class as its repeated in issue)
    def format_link(self, chapter_link):
        # Count occurrences of relative path "up"
        prev_dir_count = chapter_link.count("../")
        # Remove occurrences
        non_relative_path = chapter_link.replace("../", "")
        # Remove path elements from root url
        path_elements = self.link.split("/")
        root_dir = path_elements[:-prev_dir_count - 1]

        return '/'.join(root_dir) + "/" + non_relative_path

    def clean_chapter(self, chapter):
        # Remove first h2 (author name)
        h2 = chapter.find("h2")
        if h2 is not None:
            h2.decompose()

        # Remove first h1 (article title)
        h1 = chapter.find("h1")
        if h1 is not None:
            h1.decompose()

        # Find the tag that contains the text "Top of the page"
        link_tags = chapter.find_all(_class="link_")
        for link_tag in link_tags:
            child = link_tag.find(lambda t: t.get('href') == "#top")
            if child:
                link_tag.decompose()

        return chapter

    # Cleans up the html for epub
    def clean_html(self, html):
        # Remove linkbacks
        linkbacks = html.find_all(class_="linkback")
        for linkback in linkbacks:
            linkback.decompose()
        # Remove infobox
        info_boxes = html.find_all(class_="info")
        for info in info_boxes:
            info.decompose()
        # Remove from box
        from_boxes = html.find_all(class_="from")
        for from_box in from_boxes:
            from_box.decompose()
        # Remove infobox
        top_link = html.find(class_="toplink")
        if top_link is not None:
            top_link.decompose()
        # Remove dates
        dates = html.find_all(class_="updat")
        for date in dates:
            date.decompose()
        # Remove first h4 (journal title)
        journal_title = html.find("h4")
        if journal_title is not None:
            journal_title.decompose()
        # Remove divider lines
        lines = html.find_all("hr")
        for line in lines:
            line.decompose()
        # Find the tag that contains the text "Top of the page"
        link_tags = html.find_all(class_="link")
        for link_tag in link_tags:
            child = link_tag.find(lambda t: t.text and ("Top of page" in t.text or "Top of the page" in t.text))
            if child:
                link_tag.decompose()

        return html

    def write_to_html(self):
        # TODO we are running this twice if it is in book form
        self.body = self.clean_html(self.body)
        file_name = self.title.lower()  # Convert to lower case
        file_name = file_name.replace(' ', '_')  # Replace spaces with underscores
        file_name = re.sub(r'\W', '', file_name)  # Remove all special characters
        print(f"Writing chapter {file_name} to file")
        os.makedirs(f"issues/{self.issue}", exist_ok=True)
        with open(os.path.join(f"issues/{self.issue}", f"{file_name}.html"), "w", encoding="utf-8") as file:
            file.write(self.body.prettify())

    def get_content_as_html(self):
        return self.body.prettify()
