import json
from collections import defaultdict
from datetime import datetime

from . import filedata
from . import utils

class ArticleGraph:
    def __init__(self):
        '''
        ArticleGraph class

        - Articles are indexed by their name
        '''
        self.article_map = {}

        # adjacency list indexes
        self.fgraph = defaultdict(dict)
        self.bgraph = defaultdict(dict)

        # global metadata indexes
        self.tag_map = defaultdict(set)
        self.tag_fgraph = defaultdict(lambda: defaultdict(int))
        self.series_map = defaultdict(set)
        self.bl_map = defaultdict(lambda: defaultdict(list))
        self.bl_head = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    def get_article(self, name):
        return self.article_map.get(name) 

    def get_article_list(self):
        return list(self.article_map.values())

    def get_article_list_as_json(self):
        return json.dumps(self.fgraph)

    def get_adj_list(self):
        return self.fgraph

    def get_tag_list(self, name):
        return list(self.tag_map.get(name, []))

    def get_series_list(self, name):
        return list(self.series_map.get(name, []))

    def get_series_text_list(self, name):
        slist = []
        for series in self.get_series_list(name):
            stext = self.get_article(series).metadata.get('series','')
            slist.append(stext)
        return slist

    def get_series_obj_list(self, name):
        return [self.article_map[s] for s in self.get_series_list(name)]

    def get_backlinks(self, name):
        return self.bl_map.get(name, {})

    def get_headlinks(self, name):
        return self.bl_head.get(name, {})

    def get_edge_list(self):
        nodes = []
        edges = []
        for aname, links in self.fgraph.items():
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

    def get_tag_edge_list(self):
        nodes = []
        edges = []
        for tname, pairs in self.tag_fgraph.items():
            data = {
                'name': tname,
                'link': tname,
                'title': tname,
                'num_links': len(self.tag_map[tname])
            }
            nodes.append(data)

            for target, val in pairs.items():
                edges.append({
                    'source': tname,
                    'target': target,
                    'value': val
                })

        return {'nodes': nodes, 'links': edges}

    def get_subgraph(self, name):
        article = self.article_map[name]
        data = {
            'name': article.name,
            'link': article.link,
            'valid': article.valid,
            'num_links': sum(self.bgraph[name].values())
        }
        data.update(article.metadata)
        node_track = set([article.name])
        nodes = [data]
        edges = []

        for tname, count in [*self.fgraph[name].items(), *self.bgraph[name].items()]:
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
            
        for tname, count in self.fgraph[name].items():
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

    def add_article(self, article):
        # reset indexes if article previously processed
        if article.name in self.article_map:
            cur_article = self.article_map[article.name]
            self.fgraph[article.name] = {}
            for name in cur_article.links:
                self.bgraph[name].pop(article.name, None)
                self.bl_map[name].pop(article.name, None)
                for struct_dict in self.bl_head[name].values():
                    struct_dict.pop(article.name, None)

            for tag in cur_article.metadata.get('tag_links', []):
                self.tag_map[tag].remove(article.name)

            for ref in cur_article.metadata.get('series_links', []):
                self.series_map[ref].remove(article.name)
        
        self.article_map[article.name] = article
        self.process_links(article)
        self.process_tags(article)
        self.process_series(article)
        self.process_backlinks(article)
        self.process_data(article)

    def process_links(self, article):
        for link, count in article.links.items():
            self.fgraph[article.name][link] = count
            self.bgraph[link][article.name] = count
            
    def process_tags(self, article):
        if 'tag_links' in article.metadata:
            tag_links = list(article.metadata['tag_links'].keys())
            for i, tag in enumerate(tag_links):
                self.tag_map[tag].add(article.name)
                for pair in (tag_links[:i]+tag_links[i+1:]):
                    self.tag_fgraph[tag][pair] += 1

    def process_series(self, article):
        if 'series_links' in article.metadata:
            self.series_map[article.name].add(article.name)
            for ref in article.metadata['series_links']:
                self.series_map[ref].add(article.name)

    def process_backlinks(self, article):
        for name, data in article.linkdata.items():
            self.bl_map[name][article.name] += data

            for link in data:
                self.bl_head[name][link['header']][article.name] += [link]

    def process_data(self, article):
        if not (article.metadata.get('type') == 'journal' and 
                article.metadata.get('filedata')):
            return

        date = datetime.strptime(article.name, '%Y-%m-%d')
        datestr = date.isoformat()
        triples = [(datestr,)+e for e in
                   filedata.dict2keys(article.metadata['filedata'])]
        print('Inserting journal data for {}'.format(article.name))
        filedata.bulk_insert(triples)

    def global_series(self):
        def series2md(series):
            s = []
            def list_level(sub,lvl):
                if not sub: return ''
                for k,v in sub.items():
                    s.append(level_display(k,lvl))
                    list_level(v,lvl+1)
                return s
                        
            def level_display(link,lvl):
                return ' '*(4*lvl)+'{} {}'.format('-*+'[min(lvl,2)], link)
                
            return list_level(series,0)

        def stitch_series(hooks):
            cmap = {}
            nmap = set()
            def complete_hook(sub):
                for k,v in sub.items():
                    if k in hooks and k not in cmap:
                        tgt = hooks[k]
                    elif k not in hooks:
                        tgt = v
                    else: continue
                    complete_hook(tgt)
                    cmap[k] = {ck:cmap[ck] for ck in tgt}
                    nmap.update(list(tgt.keys()))
            complete_hook(hooks)
            return {k:v for k,v in cmap.items() if k not in nmap}

        hooks = {
            '[[{}]]'.format(utils.fname_to_title(art.name)): art.metadata['series_structure']
            for art in list(self.article_map.values())
            if 'series_structure' in art.metadata
        }
        gseries = stitch_series(hooks)
        return series2md(gseries)
