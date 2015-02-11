import json
import urllib.request
import threading

API_URL = "http://node-hnapi.herokuapp.com"
MARKDOWN_URL = "http://fuckyeahmarkdown.com/go/?read=1&u="

def config_proxy(http_proxy):
    if http_proxy is None or http_proxy is '':
        return
    proxies = {
        'http' : http_proxy
    }
    opener = urllib.request.build_opener(urllib.request.ProxyHandler(proxies))
    urllib.request.install_opener(opener)

class HackerNewsApiCall(threading.Thread):
    def __init__(self, timeout=5):
        self.result = None
        self.timeout = timeout
        self.err = None
        threading.Thread.__init__(self)

    def run(self):
        try:
            news1 = json.loads(urllib.request.urlopen(API_URL+"/news", timeout=self.timeout).read().decode())
            news2 = json.loads(urllib.request.urlopen(API_URL+"/news2", timeout=self.timeout).read().decode())
            self.result = news1 + news2
            return
        except:
            self.err = 'Failed to fetch hacker news'
            self.result = False

class ArticleExtract(threading.Thread):
    def __init__(self, url, timeout=10):
        self.result = None
        self.url = url
        self.timeout = timeout
        self.err = None
        threading.Thread.__init__(self)

    def run(self):
        try:
            markd_article = urllib.request.urlopen(MARKDOWN_URL+self.url, timeout=self.timeout).read().decode()
            self.result = markd_article
            return
        except:
            self.err = 'Failed to fetch the article'
            self.result = False