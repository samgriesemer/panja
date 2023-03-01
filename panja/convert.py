import subprocess
from pathlib import Path

def md2pdf(func):
    def wrapper(filename, outfile=None):
        if not outfile:
            outfile = str(Path(filename).with_suffix('.pdf'))

        cmd_lst = func()
        cmd_lst = [el for line in cmd_lst for el in line.split(' ')]

        cmd_lst.append(filename)
        cmd_lst.append('-o')
        cmd_lst.append(outfile)

        try:
            subprocess.check_output(cmd_lst)
        except subprocess.CalledProcessError as e:
            print('Error build target via convert')
            return False

        return outfile

    return wrapper

@md2pdf
def article_pdf():
    return [
        'pandoc',
        '-N',
        '-C',
        '--highlight-style kate',
        '--template=/home/smgr/Documents/projects/templates/latex/pandoc/article_template.tex',
        '--variable csquotes',
        '--variable geometry=margin=0.7in',
        '-M link-citations',
        '-M link-bibliography',
        '--bibliography=/home/smgr/Documents/notes/docs/bb-global.bib',
        '--pdf-engine=xelatex',
        '-f markdown+rebase_relative_paths',
        '-t latex',
    ]

@md2pdf
def twocol_pdf():
    return [
        'pandoc',
        '-N',
        '-C',
        '--highlight-style kate',
        '--template=/home/smgr/Documents/projects/templates/latex/pandoc/article_template.tex',
        '--variable csquotes',
        '--variable geometry=margin=0.7in',
        '--variable classoption=twocolumn',
        '-M link-citations',
        '-M link-bibliography',
        '--bibliography=/home/smgr/Documents/notes/docs/bb-global.bib',
        '--pdf-engine=xelatex',
        '-f markdown+rebase_relative_paths',
        '-t latex',
    ]

@md2pdf
def beamer_pdf():
    return [
        'pandoc',
        '-N',
        '-C',
        '--highlight-style tango',
        '--dpi=300',
        '--listings',
        '--top-level-division=section',
        '--slide-level=3',
        '--toc-depth=5',
        '--template=/home/smgr/Documents/projects/templates/latex/pandoc/beamer_test/default_mod.latex',
        '-H /home/smgr/Documents/projects/templates/latex/pandoc/beamer_test/preamble.tex',
        '--bibliography=/home/smgr/Documents/notes/docs/docsyncbib.bib',
        '--csl=/home/smgr/Documents/projects/templates/latex/pandoc/acm-sig-proceedings-long-author-list.csl',
        '--pdf-engine=xelatex',
        '-f markdown+rebase_relative_paths',
        '-t beamer',
    ]

@md2pdf
def nips_pdf():
    return [
        'pandoc',
        '-N',
        '-C',
        '--highlight-style kate',
        '--template=/home/smgr/Documents/projects/templates/latex/pandoc/nips/nips_template.tex',
        '--variable csquotes',
        '-M link-citations',
        '-M link-bibliography',
        '--bibliography=/home/smgr/Documents/notes/docs/bb-global.bib',
        '--pdf-engine=xelatex',
        '-f markdown+rebase_relative_paths',
        '-t latex',
    ]

alias_map = {
    'article': article_pdf,
    'twocol' : twocol_pdf,
    'nips'   : nips_pdf,
    'beamer' : beamer_pdf,
}
