# Code partially adapted from
# https://github.com/jgm/pandocfilters/blob/master/examples/tikz.py

import os
import re
import shutil
import sys
from subprocess import call, DEVNULL
from tempfile import mkdtemp
from pathlib import Path

from pandocfilters import toJSONFilter, Para, Image, get_filename4code, get_extension

PREAMBLE = '/home/smgr/Documents/projects/templates/latex/standard/preamble.sty'

def standalone2pdf(instr, outfile, preamble=None, extra_files=None):
    '''
    Future: support local data directory for tikz/pgf plots from tabular data
    '''
    tmpdir = mkdtemp()
    olddir = os.getcwd()

    if preamble is not None:
        shutil.copy(preamble, tmpdir)
            
    if extra_files is not None:
        for file in extra_files:
            shutil.copy(file, tmpdir)

    os.chdir(tmpdir)
    
    with open('stal.tex', 'w') as f:
        f.write("""\\documentclass{standalone}
                 \\usepackage{preamble}
                 \\begin{document}
                 """)
        f.write(instr)
        f.write("\n\\end{document}\n")

    rcode = call(["pdflatex", 'stal.tex'], stdout=DEVNULL)
    os.chdir(olddir)

    shutil.copyfile(tmpdir + '/stal.pdf', outfile)
    shutil.rmtree(tmpdir)
    return rcode

def pdf2svg(infile, outfile=None, remove_pdf=False):
    if outfile is None:
        outfile = Path(infile).with_suffix('.svg')

    rcode = call(['pdf2svg', infile, outfile], stdout=DEVNULL)
    if remove_pdf: Path(infile).unlink()

    return rcode

def pdftex2svg(tex_file, pdf_file, outfile):
    '''
    infile is .pdf_tex file
    outfile is .svg file, if specified; otherwise defaults to infile name
            w/ .svg extension
    '''
    print('pdftex2svg: in {}, pdf {}'.format(tex_file, pdf_file))
    #outpdf = Path(tex_file).with_suffix('.pdf')
    outpdf = Path(tex_file).with_suffix('.pdf.tmp').name
    print('pdftex2svg: out pdf {}'.format(outpdf))
    standalone2pdf('\\input{'+Path(tex_file).name+'}', outpdf, PREAMBLE,
                   extra_files=[tex_file, pdf_file])
    print('pdftex2svg: standalone conversion to {}'.format(outfile))
    pdf2svg(outpdf, outfile)

def tikz2svg(tikz_src, outfile):
    '''
    outfile is .svg file
    '''
    outpdf = Path(outfile).with_suffix('.pdf')
    standalone2pdf(tikz_src, outpdf, PREAMBLE)
    pdf2svg(outpdf, outfile, remove_pdf=True)
