import urllib3
from bs4 import BeautifulSoup
from index import Index

http = urllib3.PoolManager()

isj_index_url = "https://www.marxists.org/history/etol/newspape/isj/index.html"

index_request = http.request('GET', isj_index_url) 

souped_index = BeautifulSoup(index_request.data, 'html5lib')

parsed_index = Index(souped_index, isj_index_url)

parsed_index.parse_issues()