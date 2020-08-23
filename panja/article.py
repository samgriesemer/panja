import re
import pypandoc as pp

class Article:
    '''
    Article object for operating on Markdown files. The class takes care of a lot of
    desired features automatically, stripping metadata out of YAML block,
    performing custom text transformations (like wiki links to Markdown style
    links), and converting the resulting text to HTML. This class is admittedly
    a bit sloppy and specific to my own needs at the moment.
    '''
    def __init__(self, fullpath, relpath, local=False):
        self.fullpath = fullpath
        self.relpath = relpath
        self.url = '.'.join(relpath.split('.')[:-1])
        self.metadata = {}
        self.content = ''
        self.html = ''
        self.valid = True

        self.process_metadata()
        self.__dict__.update(self.metadata)

        # stop processing early if public and other
        if not local and (self.metadata.get('type') == 'journal' or
                          self.metadata.get('visibility') == 'private'):
            self.valid = False

        if not self.valid: return

        self.transform_links()
        self.process_backlinks()
        self.convert_html()

    def process_metadata(self):
        with open(self.fullpath, 'r') as f:
            ft = f.read()
            mt = re.match('---\n(.*?)\n---', ft, flags=re.DOTALL)

            if mt is None:
                self.valid = False
                print(self.relpath + ' has invalid metadata')
                return
            
            metadata = {}
            for line in mt.group(1).split('\n'):
                split = [line.split(':')[0], ':'.join(line.split(':')[1:])]
                attr, val = map(str.strip, split)
                metadata[attr.lower()] = val

        self.metadata = metadata

    def transform_links(self):
        with open(self.fullpath, 'r+') as f:
            ft = f.read()
            nt = re.sub(
                pattern=r'\[\[([^\]]*)\]\]',
                repl=self.title_to_link,
                string=ft
            )
            self.content = nt

    def process_backlinks(self):
        pass

    def convert_html(self):
        filters = ['./node-pandoc-katex/pandoc-katex.js']
        pdoc_args = [
            '--section-divs',
            '--template=blank_template.html'
        ]
       
        # conditional args
        if self.metadata.get('toc') != 'false':
            pdoc_args.append('--toc')

        self.html = pp.convert_text(self.content,
                                    to='html5',
                                    format='md',
                                    extra_args=pdoc_args)
                                    #filters=filters)

    def title_to_link(self, match):
        '''Return Markdown-style link from file title'''
        title = match.group(1)
        return '['+title+']('+title.replace(' ', '_')+')'

