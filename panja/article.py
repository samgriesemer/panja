import pypandoc

class Article:
    def __init__(self, path):
        pass

    output = pypandoc.convert_file('somefile.md', 'rst')
