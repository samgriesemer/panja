import os
from jinja2 import FileSystemLoader, Environment
import shutil
import pathlib

class Panja:
    '''Panja class, core implementation for handling site rendering'''

    def __init__(self, cdir, odir, adir=None, tdir=None):
        '''
        :param cdir: content
            directory, location of verbatim HTML files to copy directly or Jinja
            templates to render inheriting from theme templates. Other files may
            be placed in this directory, and will simply be copied to the
            output.

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

        self.global_context = {}

    def create_site(self):
        self.render_content()
        self.render_articles()

        # copy theme static files to output
        if self.tdir is not None:
            ipath = os.path.join(self.tdir, 'static')
            opath = os.path.join(self.odir, 'static')
            shutil.copytree(ipath, opath)

    def render_content(self, ext=['.html']):
        # set template context if exists
        loader = FileSystemLoader(self.cdir)
        if self.theme:
            loader = FileSystemLoader([self.ttdir, self.cdir])
        env = Environment(loader=loader)

        # render content templates
        for filepath in self.directory_tree(self.cdir):
            opath = os.path.join(self.odir, filepath)
            self.check_dir(opath)
            if pathlib.Path(filepath).suffix in ext:
                template = env.get_template(filepath)
                template.stream(self.global_context).dump(opath)
            else:
                self.copy_file(os.path.join(self.cdir, filepath), opath)

    def render_articles(self, ext=['.md']):
        loader = FileSystemLoader(self.ttdir)
        env = Environment(loader=loader)

        # render content templates
        for filepath in self.directory_tree(self.adir):
            opath = os.path.join(self.odir, filepath)
            self.check_dir(opath)
            if pathlib.Path(filepath).suffix in ext:
                article = Article(filepath)
                template = env.get_template('article.html')
                template.stream(self.global_context).dump(opath)
            else:
                self.copy_file(os.path.join(self.adir, filepath), opath)

    def copy_file(self, ipath, opath):
        shutil.copy2(ipath, opath)
        
    def directory_tree(self, path):
        '''Return list of paths for all non-hidden files __inside__ of `path`. '''
        paths = []
        for (dirpath, dirnames, filenames) in os.walk(path):
            paths += [os.path.relpath(os.path.join(dirpath, file), path) \
                      for file in filenames if not file.startswith('.')]
        return paths
    
    def check_dir(self, path):
        '''Check if `path` exists, creating the necessary directories if not'''
        outdir = os.path.dirname(path)
        if not os.path.exists(outdir):
            os.makedirs(outdir)

class Article:

    def __init__(self, path):
        pass
