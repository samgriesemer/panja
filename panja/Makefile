PY?=python3
PANJA?=panja

BASEPATH=$(CURDIR)
SEARCHPATHS={}
OUDIR={}
STATICPATHS={}

help:
	@echo 'Makefile for panja static site			'
	@echo '											'
	@echo 'Usage:									'
	@echo '    make html							'
	@echo '    make regenerate						'

html:
	$(PANJA) --opts

clean:
	[ ! -d $(OUTDIR) ] || rm -rf $(OUTDIR)

regenerate:
	$(PANJA) --opts
