LOG		:= meta-source/debian/changelog
META_VERSION	:= $(shell head -1 $(LOG)|sed 's/.*(\(.*\)).*/\1/')

all: source

source: clean
	ln -s meta-source linux-meta-$(META_VERSION)
	cd linux-meta-$(META_VERSION); \
	dpkg-buildpackage -S -sa -rfakeroot -I -i

binary: clean
	ln -s meta-source linux-meta-$(META_VERSION)
	cd linux-meta-$(META_VERSION); \
	debuild -b -aarmel

clean:
	cd meta-source && fakeroot debian/rules clean
	rm -f linux-meta-$(META_VERSION)
	rm -f *.dsc *.changes *.gz *.deb *.build *.upload

