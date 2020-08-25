from panja import Panja
import util

from tqdm import tqdm
import os

OPTIONS = {
    'global_context': {
        'sitename': 'samgriesemer'
    },
    'content': ['test/pages', 'test/notes'],
    'theme': 'test/theme',
    'output': 'test/output',
    'filters': [
        ('*.md', render_article)
    ]
}

def render_article(self, env, article_path, article_map):
    article = article_map[article_path]
    if not article.valid: return

    opath = os.path.join(self.odir, article.relpath)
    opath = opath.split('.')
    opath[-1] = 'html'
    opath = '.'.join(opath)
    
    template = env.get_template('article.html')
    context = {'article': article}
    context.update(self.global_context)
    template.stream(context).dump(opath)

if __name__ == '__main__':
    # custom articles, perhaps to be wrapped up by a graph object at some point
    # so all articles can be handled at once and operated on globally
    articles = []
    article_map = {}
    for relpath in tqdm(util.directory_tree('test/notes')):
        fullpath = os.path.join(self.adir, relpath)
        opath = os.path.join(self.odir, relpath)
        util.check_dir(opath)

        if pathlib.Path(relpath).suffix == '.md':
            article = Article(fullpath, relpath)
            articles.append(article)
            article_map[relpath] = article

    site = Panja(**OPTIONS)
    site.create_site()
