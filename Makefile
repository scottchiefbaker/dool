name    = dool
version = $(shell perl -nE 'if (/__version__ = .*?([\.\d]+)/) { print $$1; }' dool)

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
	install -Dp -m0755 dool $(DESTDIR)$(bindir)/dool
	install -d  -m0755 $(DESTDIR)$(datadir)/dool/
	install -Dp -m0755 dool $(DESTDIR)$(datadir)/dool/dool.py
	install -Dp -m0644 plugins/dool_*.py $(DESTDIR)$(datadir)/dool/
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
	git ls-files | tar --files-from=- -cvpaf /tmp/dool-$(version).tar.gz

	@echo
	@echo -e "\033[1;38;5;15mBuilt:\033[0m"
	@ls --color --human -l /tmp/dool-$(version).tar.gz

tardist: dist

rpm:
	cd packaging/rpm/; ./build.sh; cd - > /dev/null

srpm: dist
	rpmbuild -ts --clean --rmspec --define "_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm" --define "_srcrpmdir ../" ../$(name)-$(version).tar.bz2

snap:
	cd packaging/snap/; snapcraft

deb:
	cd packaging/debian/; ./build.sh ; cd - > /dev/null

display_config:
	@echo Displaying config
	@echo "Version: $(version)"
