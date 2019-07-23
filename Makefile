name    = dool
version = $(shell awk '/^Version: / {print $$2}' $(name).spec)

prefix     = /usr
sysconfdir = /etc
bindir     = $(prefix)/bin
datadir    = $(prefix)/share
mandir     = $(datadir)/man

.PHONY: all install docs clean

all: docs
	@echo "Nothing to be build."

docs:
	$(MAKE) -C docs docs

install:
#	-[ ! -f $(DESTDIR)$(sysconfdir)/dool.conf ] && install -D -m0644 dool.conf $(DESTDIR)$(sysconfdir)/dool.conf
	install -Dp -m0755 dool $(DESTDIR)$(bindir)/dool
	install -d  -m0755 $(DESTDIR)$(datadir)/dool/
	install -Dp -m0755 dool $(DESTDIR)$(datadir)/dool/dool.py
	install -Dp -m0644 plugins/dool_*.py $(DESTDIR)$(datadir)/dool/
#	install -d  -m0755 $(DESTDIR)$(datadir)/dool/examples/
#	install -Dp -m0755 examples/*.py $(DESTDIR)$(datadir)/dool/examples/
	install -Dp -m0644 docs/dool.1 $(DESTDIR)$(mandir)/man1/dool.1

docs-install:
	$(MAKE) -C docs install

clean:
	rm -f examples/*.pyc plugins/*.pyc
	$(MAKE) -C docs clean

test:
	./dool --version
	./dool -taf 1 5
	./dool -t --all-plugins 1 5

dist: clean
	$(MAKE) -C docs dist
#	svn up && svn list -R | pax -d -w -x ustar -s ,^,$(name)-$(version)/, | bzip2 >../$(name)-$(version).tar.bz2
#	svn st -v --xml | \
        xmlstarlet sel -t -m "/status/target/entry" -s A:T:U '@path' -i "wc-status[@revision]" -v "@path" -n | \
        pax -d -w -x ustar -s ,^,$(name)-$(version)/, | \
        bzip2 >../$(name)-$(version).tar.bz2
	git ls-files | pax -d -w -x ustar -s ,^,$(name)-$(version)/, | bzip2 >../$(name)-$(version).tar.bz2

rpm: dist
	rpmbuild -tb --clean --rmspec --define "_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm" --define "_rpmdir ../" ../$(name)-$(version).tar.bz2

srpm: dist
	rpmbuild -ts --clean --rmspec --define "_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm" --define "_srcrpmdir ../" ../$(name)-$(version).tar.bz2

snap:
	cd packaging/snap/; snapcraft
