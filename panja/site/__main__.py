import os
from panja import Site

if __name__ == "__main__":
    searchpaths = [os.path.join(os.getcwd(), 'templates')]
    site = Site.make_site(searchpaths=searchpaths)
    site.render(use_reloader=True)
