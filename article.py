# Stores content and meta data of an article, treated as two types. Those treated as books (with chapters and ToC) and those treated as only articles (without chapters)

class Article:
    title = ""
    authors = []

    def __init__(self, body, link):
        self.body = body
        self.link = link

    def parse(self):
        pass