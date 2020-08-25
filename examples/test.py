import staticjinja

import os
from tqdm import tqdm

from panja.article import Article
from panja import util

# Note: contexts can be used without rules; you could just defined the dict to be passed
# to the template and have the site object handle everything else like normal. Actual new
# rules change the way the compilation occurs, in my case ensuring I write an HTML file
# instead of a Markdown one. Here using both contexts and rules doesn't really matter, all
# can be done in the rule.

# tindex.html context
def process_articles(site, template):
    # custom articles, perhaps to be wrapped up by a graph object at some point
    # so all articles can be handled at once and operated on globally
    articles = []
    article_base = os.path.join(site.basepath, 'notes')

    for relpath in tqdm(util.directory_tree(article_base)):
        fullpath = os.path.join(article_base, relpath)

        if relpath.split('.')[-1] == 'md':
            article = Article(fullpath, relpath)
            articles.append(article)
    return {'article_list': articles}

# .*.md compilation rule
def render_article(site, template, **kwargs):
    article = Article(template.filename, template.name)
    article.prepare()

    if not article.valid: return

    opath = os.path.join(site.outpath, template.name)
    opath = opath.split('.')
    opath[-1] = 'html'
    opath = '.'.join(opath)
    
    template = site.env.get_template('_article.html')
    context = {'article': article}
    template.stream(context).dump(opath)


site = staticjinja.make_site(
    searchpaths=[
        'theme',
        'pages',
        'notes'
    ],
    outpath='output',
    staticpaths=[
        'static/',
        'docs/',
        'images/',
        'projects/dashboard/',
        'projects/evolution-art/',
        'projects/evolution/',
        'projects/halton/',
        'projects/mcttt/',
        'projects/nn/',
        'projects/time-graph/',
    ],
    basepath='staticjinja/test',
    contexts=[
        ('tindex.html', process_articles)
    ],
    rules=[
        ('.*.md', render_article),
    ]
)
site.render(use_reloader=True)
