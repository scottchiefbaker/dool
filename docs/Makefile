prefix = /usr
datadir = $(prefix)/share
mandir = $(datadir)/man

template = dagit.ott

adoctargets = $(shell echo *.adoc)
htmltargets = $(patsubst %.adoc, %.html, $(adoctargets))

all:

dist: docs

docs: dool.1 $(htmltargets)

install: dool.1
	install -Dp -m0644 dool.1 $(DESTDIR)$(mandir)/man1/dool.1

clean:
	rm -f dool.1 *.html *.xml

%.1.html: %.1.adoc
	asciidoc -d manpage $<

%.html: %.adoc
	asciidoc $<

%.1.xml: %.1.adoc
	asciidoc -b docbook -d manpage $<

%.1: %.1.xml
	@xmlto man $<

%.xml: %.adoc
	asciidoc -b docbook -d article -o $@ $<

%.htm: %.adoc
	asciidoc -s -b html4 -d article -o $@ $<

%.xhtml: %.adoc
	asciidoc -s -b xhtml11 -d article -o $@ $<

%.tmp.odt: %.xml
#»··-make -C /home/dag/home-made/docbook2odf/ dag-cv
	docbook2odf -f --params generate.meta=0 -o $@ $<

%.odt: $(template) %.tmp.odt
	unoconv -f odt -t $(template) -o $@ $<
