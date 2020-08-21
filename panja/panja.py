import os
import shutil
import pathlib
from jinja2 import FileSystemLoader, Environment

import util
from article import Article

class Panja:
    '''Panja class, core implementation for handling site rendering'''

    def __init__(self, cdir, odir, adir=None, tdir=None):
        '''
        :param cdir:
            content directory, location of verbatim HTML files to copy directly or Jinja
            templates to render inheriting from theme templates. Other files may be placed
            in this directory, and will simply be copied to the output.

        :param odir:
            output directory, location of processed output files for the final
            site.  The content directory's structure will be matched in the
            output, and articles are placed according to the article map.

        :param adir:
            article directory, location of Markdown files to be converted to
            HTML using Pandoc, and placed inside the `article` Jinja template

        :param tdir:
            theme directory, location of base Jinja templates and global static
            files for the site. Follows Pelican-like theme structure, where
            templates are placed under `templates/` and static under `static/`.
            Panja does not make any assumption about the naming for any template
            file except `article.html`, which is used to render Markdown files
            that cannot specify independently which Jinja template to inherit
            from.
        '''
        self.cdir = cdir
        self.odir = odir
        self.adir = adir
        self.tdir = tdir

        if self.tdir is not None:
            self.ttdir = os.path.join(self.tdir, 'templates')
            self.theme = True
        else:
            self.ttdir = None
            self.theme = False

        # compute global context variables for templates
        self.process_articles()
        self.global_context = {
            'article_list': self.articles
        }

    def create_site(self):
        self.render_content()
        
        # copy theme static files to output
        if self.tdir is not None:
            ipath = os.path.join(self.tdir, 'static')
            opath = os.path.join(self.odir, 'static')
            shutil.copytree(ipath, opath)

        if self.adir is not None:
            self.render_articles()

    def render_content(self, ext=['.html']):
        # set template context if exists
        loader = FileSystemLoader(self.cdir)
        if self.theme:
            loader = FileSystemLoader([self.ttdir, self.cdir])
        env = Environment(loader=loader)

        # render content templates
        for filepath in util.directory_tree(self.cdir):
            opath = os.path.join(self.odir, filepath)
            util.check_dir(opath)
            if pathlib.Path(filepath).suffix in ext:
                template = env.get_template(filepath)
                template.stream(self.global_context).dump(opath)
            else:
                util.copy_file(os.path.join(self.cdir, filepath), opath)

    def render_articles(self, ext=['.md']):
        loader = FileSystemLoader(self.ttdir)
        env = Environment(loader=loader)

        for article in self.articles:
            if not article.valid: continue
            opath = os.path.join(self.odir, article.relpath)
            opath = opath.split('.')
            opath[-1] = 'html'
            opath = '.'.join(opath)
            
            template = env.get_template('article.html')
            context = {'article': article}
            context.update(self.global_context)
            template.stream(context).dump(opath)

    def process_articles(self, ext=['.md']):
        self.articles = []
        for relpath in util.directory_tree(self.adir):
            fullpath = os.path.join(self.adir, relpath)

            opath = os.path.join(self.odir, relpath)
            util.check_dir(opath)

            if pathlib.Path(relpath).suffix in ext:
                self.articles.append(Article(fullpath, relpath))
            else:
                shutil.copy2(fullpath, opath)
