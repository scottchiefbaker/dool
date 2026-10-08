name    = dool
version = $(shell perl -nE 'if (/__version__ = .*?([\.\d]+)/) { print $$1; }' dool)

prefix     = /usr
sysconfdir = /etc
bindir     = $(prefix)/bin
datadir    = $(prefix)/share
mandir     = $(datadir)/man
tmpdir     = /var/tmp

.PHONY: all install docs clean test smoketest unit-test lint

LINT_FILES = dool install.py $(wildcard plugins/*.py tests/*.py packaging/*.py)

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
	rm -f $(tmpdir)/dool-$(version)*.*

test: unit-test

smoketest:
	./dool --version
	./dool -taf 1 5
	./dool -t --all-plugins 1 5

unit-test:
	python3 tests/run_tests.py

# Stdlib-only: compile every source file with warnings as errors. Catches syntax
# errors, TabError (mixed tabs/spaces), and invalid escape sequences. Does not
# check unused imports or style.
lint:
	python3 -W error -c 'import sys, pathlib; [compile(pathlib.Path(f).read_text(encoding="utf-8"), f, "exec") for f in sys.argv[1:]]; print(len(sys.argv) - 1, "files compile cleanly")' $(LINT_FILES)

dist: clean
	$(MAKE) -C docs dist
	git ls-files | tar --files-from=- -cvpaf $(tmpdir)/dool-$(version).tar.gz

	@echo
	@echo -e "\033[1;38;5;15mBuilt:\033[0m"
	@ls --color --human -l $(tmpdir)/dool-$(version).tar.gz

tardist: dist

rpm:
	cd packaging/rpm/; ./build.sh; cd - > /dev/null

srpm: dist
	rpmbuild -ts --clean --rmspec --define "_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm" --define "_srcrpmdir ../" ../$(name)-$(version).tar.bz2

release: dist deb rpm
	@echo
	@echo
	@echo -e "\033[1;38;5;15mBuilt packages:\033[0m"
	@ls --color --human -l $(tmpdir)/dool-$(version)*.*

snap:
	cd packaging/snap/; snapcraft

deb:
	$(MAKE) install DESTDIR=packaging/debian/build
	cd packaging/debian/; ./build.sh ; cd - > /dev/null

display_config:
	@echo Displaying config
	@echo "Version: $(version)"
