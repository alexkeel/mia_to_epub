from bs4 import BeautifulSoup, Tag
from .issue import Issue

# This file contains the tools to parse and process a list of ISJ issues


class Index:
    def __init__(self, page, url):
        self.root_page = page
        self.url = url
        self.current_section = []
        self.sections = []
        self.issues = []

    def parse_issues(self):
        # Get body content
        self.body = self.root_page.find('body')
        # Attempt to get each issues from the index
        # Dont write anything until an initial anchor has been found
        begin_writing = False
        for tag in self.body:
            if isinstance(tag, Tag):  # Only process Tag objects
                if tag.name == 'a':
                    begin_writing = True
                    if self.current_section:  # If there's already a section started, finish it
                        self.sections.append(BeautifulSoup(''.join(str(t) for t in self.current_section), 'html5lib'))
                        self.current_section = []  # Start a new section
                if begin_writing:
                    self.current_section.append(tag)

        if self.current_section:
            self.sections.append(BeautifulSoup(''.join(str(t) for t in self.current_section), 'html5lib'))

        for section in self.sections:
            issue = Issue(section, self.url)
            self.issues.append(issue)

        for issue in self.issues:
            issue.parse()
            issue.compile_to_epub()
