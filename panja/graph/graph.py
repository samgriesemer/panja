import os
import inspect
import re
import json
from collections import defaultdict
from tqdm import tqdm

from ..note.article import Article
from ..utils import util

class Graph:
    def __init__(self, notepath, basepath=None, local=False, html=False):
        # update basepath if not supplied or relative
        if basepath is None:
            basepath = os.getcwd()
        else:
            if not os.path.isabs(basepath):
                basepath = os.path.join(os.getcwd(), basepath)

        self.notepath = notepath
        self.basepath = basepath
        self.local = local
        self.article_map = {}
        self.tag_map = defaultdict(set)
        self.lgraph = defaultdict(dict)
        self.bgraph = defaultdict(dict)
        self.init_tracker = set()

        # alt graph management

        for note in tqdm(util.directory_tree(notepath)):
            fullpath = os.path.join(notepath, note)
            name = '.'.join(note.split('.')[:-1])
            if note.split('.')[-1] == 'md':
                article = self.add_article(fullpath, name)
                if html and article.valid:
                    article.convert_html() 
                    self.init_tracker.add(name)

    def get_article_list(self):
        return list(self.article_map.values())

    def get_article_list_as_json(self):
        return json.dumps(self.lgraph)

    def get_link_graph(self):
        return self.lgraph

    def get_link_graph_edge_list(self):
        nodes = []
        edges = []
        for aname, links in self.lgraph.items():
            article = self.article_map[aname]
            data = {
                'name': article.name,
                'link': article.link,
                'valid': article.valid,
                'num_links': sum(self.bgraph[aname].values())
            }
            data.update(article.metadata)
            nodes.append(data)

            for target, val in links.items():
                if target in self.article_map:
                    edges.append({
                        'source': aname,
                        'target': target,
                        'value': val
                    })

        return {'nodes': nodes, 'links': edges}

    def get_note_subgraph(self, name):
        article = self.article_map[name]
        data = {
            'name': article.name,
            'link': article.link,
            'valid': article.valid,
            'num_links': sum( self.bgraph[name].values())
        }
        data.update(article.metadata)
        node_track = set([article.name])
        nodes = [data]
        edges = []

        for tname, count in [*self.lgraph[name].items(), *self.bgraph[name].items()]:
            if tname not in self.article_map: continue
            target = self.article_map[tname]
            if target.name not in node_track:
                data = {
                    'name': target.name,
                    'link': target.link,
                    'valid': target.valid,
                    'num_links': sum(self.bgraph[target.name].values())
                }
                data.update(target.metadata)
                nodes.append(data)
                node_track.add(target.name)
            
        for tname, count in self.lgraph[name].items():
            if tname not in self.article_map: continue
            edges.append({
                'source': name,
                'target': tname,
                'value': count
            })

        for tname, count in self.bgraph[name].items():
            if tname not in self.article_map: continue
            edges.append({
                'source': tname,
                'target': name,
                'value': count
            })

        return {'nodes': nodes, 'links': edges}

    def add_article(self, fullpath, name, verbose=False):
        article = Article(fullpath, name, self.basepath, self.local, verbose)
        if article.valid:
            self.article_map[name] = article
            self.process_links(article)
            self.process_tags(article)
        return article

    def process_links(self, article):
        links = re.findall(
            pattern=r'\[\[([^\]`]*)\]\]',
            string=article.content
        )
        
        lcounts = defaultdict(int)
        for link in links:
            l = util.title_to_fname(link)
            lcounts[l] += 1

        for link, count in lcounts.items():
            # index forward links
            self.lgraph[article.name][link] = count

            # index backlinks
            self.bgraph[link][article.name] = count
            
    def process_tags(self, article):
        if hasattr(article, 'tag_list'):
            for tag in article.tag_list:
                self.tag_map[tag].add(article)
