SPECFILE            = $(shell find -maxdepth 1 -type f -name *.spec)
SPECFILE_NAME       = $(shell awk '$$1 == "Name:"     { print $$2 }' $(SPECFILE) )
SPECFILE_VERSION    = $(shell awk '$$1 == "Version:"  { print $$2 }' $(SPECFILE) )
SPECFILE_RELEASE    = $(shell awk '$$1 == "Release:"  { print $$2 }' $(SPECFILE) )
TARFILE             = $(SPECFILE_NAME)-$(SPECFILE_VERSION).tar.gz
DIST               ?= $(shell rpm --eval %{dist})

sources:
	tar -zcf $(TARFILE) --exclude-vcs --transform 's,^,$(SPECFILE_NAME)-$(SPECFILE_VERSION)/,' ansible src tests LICENSE README.md conf_example.yaml *py

clean:
	rm -rf build/ $(TARFILE)

srpm: sources
	rpmbuild -bs --define 'dist $(DIST)' --define "_topdir $(PWD)/build" --define '_sourcedir $(PWD)' $(SPECFILE)

rpm: sources
	rpmbuild -bb --define 'dist $(DIST)' --define "_topdir $(PWD)/build" --define '_sourcedir $(PWD)' $(SPECFILE)
