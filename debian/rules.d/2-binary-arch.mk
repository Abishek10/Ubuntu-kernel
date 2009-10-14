# We don't want make removing intermediary stamps
.SECONDARY :

build-arch: $(addprefix build-modules-,$(flavours))

# Prepare the out-of-tree build directory

printenv:
	@echo "confdir    : $(confdir)"
	@echo "stampdir   : $(stampdir)"

COMPAT_KDIR=/lib/modules/$(release)-$(abinum)-$(target_flavour)
make_compat = make $(conc_level) KLIB=$(COMPAT_KDIR) MADWIFI=
ifneq ($(LOCAL_ENV_CC),)
make_compat += CC=$(LOCAL_ENV_CC) DISTCC_HOSTS=$(LOCAL_ENV_DISTCC_HOSTS)
endif

prepare-%: $(stampdir)/stamp-prepare-%
	@# Empty for make to be happy
$(stampdir)/stamp-prepare-%: target_flavour = $*
$(stampdir)/stamp-prepare-%: $(confdir)/$(arch)
	@echo "Preparing $*..."
	install -d $(builddir)/build-$*
	cd updates; tar cf - * | tar -C $(builddir)/build-$* -xf -
	mv $(builddir)/build-$*/MUNGE-CW $(builddir)/build-$*/compat-wireless-2.6
	cd $(builddir)/build-$*/compat-wireless-2.6 && ./MUNGE-CW
	cd $(builddir)/build-$*/alsa-driver && ./configure --with-kernel=$(COMPAT_KDIR)/build
	cat $^ > $(builddir)/build-$*/.config
	# XXX: generate real config
	touch $(builddir)/build-$*/ubuntu-config.h
	touch $(builddir)/build-$*/ubuntu-build
	touch $@

# Do the actual build, including image and modules
build-modules-%: $(stampdir)/stamp-build-%
	@# Empty for make to be happy
$(stampdir)/stamp-build-%: target_flavour = $*
$(stampdir)/stamp-build-%: build_arch_t = $(call custom_override,build_arch,$*)
$(stampdir)/stamp-build-%: $(stampdir)/stamp-prepare-%
	@echo "Building $*..."
	cd $(builddir)/build-$*/compat-wireless-2.6 && $(make_compat)
	cd $(builddir)/build-$*/alsa-driver && make $(conc_level)
	$(kmake) $(conc_level) modules
	@touch $@

# Install the finished build
install-%: cwpkgdir = $(CURDIR)/debian/linux-backports-modules-$(release)-$(abinum)-$*
install-%: cwmoddir = $(cwpkgdir)/lib/modules/$(release)-$(abinum)-$*
install-%: cspkgdir = $(CURDIR)/debian/linux-backports-modules-alsa-$(release)-$(abinum)-$*
install-%: csmoddir = $(cspkgdir)/lib/modules/$(release)-$(abinum)-$*
install-%: firmdir = $(cwpkgdir)/lib/firmware/$(release)-$(abinum)-$*
install-%: lbmbasehdrpkg = linux-headers-lbm-$(release)$(debnum)
install-%: lbmhdrpkg = $(lbmbasehdrpkg)-$*
install-%: hdrdir = $(CURDIR)/debian/$(lbmhdrpkg)/usr/src/$(lbmhdrpkg)
install-%: target_flavour = $*
install-%: $(stampdir)/stamp-build-%
	dh_testdir
	dh_testroot
	dh_clean -k -plinux-backports-modules-$(release)-$(abinum)-$*

	install -d $(firmdir)
	#
	# This firmware file name has to be consistent with IWL4965_UCODE_API in iwl4965-base.c
	#
	cp firmware/iwlwifi/*4965*/*.ucode $(firmdir)/lbm-iwlwifi-4965-2.ucode
	cp firmware/iwlwifi/*3945*/*.ucode $(firmdir)/lbm-iwlwifi-3945-2.ucode
	cp firmware/iwlwifi/*5000*/*.ucode $(firmdir)/lbm-iwlwifi-5000-1.ucode
	cp firmware/iwlwifi/*5150*/*.ucode $(firmdir)/lbm-iwlwifi-5150-1.ucode

	#
	# Build the compat wireless packages.
	#
	install -d $(cwmoddir)/updates/cw
	find $(builddir)/build-$*/compat-wireless-2.6 -type f -name '*.ko' | while read f ; do cp -v $${f} $(cwmoddir)/updates/cw/`basename $${f}`; done

ifeq ($(no_image_strip),)
	find $(cwpkgdir)/ -type f -name \*.ko -print | xargs -r strip --strip-debug
endif

	install -d $(cwpkgdir)/DEBIAN
	for script in postinst postrm; do					\
	  sed -e 's/@@KVER@@/$(release)-$(abinum)-$*/g'				\
	       debian/control-scripts/$$script > $(cwpkgdir)/DEBIAN/$$script;	\
	  chmod 755 $(cwpkgdir)/DEBIAN/$$script;					\
	done

	dh_testdir
	dh_testroot
	dh_installchangelogs -p$(lbmhdrpkg)
	dh_installdocs -p$(lbmhdrpkg)
	dh_compress -p$(lbmhdrpkg)
	dh_fixperms -p$(lbmhdrpkg)
	dh_installdeb -p$(lbmhdrpkg)
	dh_gencontrol -p$(lbmhdrpkg)
	dh_md5sums -p$(lbmhdrpkg)
	dh_builddeb -p$(lbmhdrpkg)

	#
	# Build the ALSA snapshot packages.
	#
	install -d $(csmoddir)/updates/alsa
	find $(builddir)/build-$*/alsa-driver -type f -name '*.ko' | while read f ; do cp -v $${f} $(csmoddir)/updates/alsa/`basename $${f}`; done

ifeq ($(no_image_strip),)
	find $(cspkgdir)/ -type f -name \*.ko -print | xargs -r strip --strip-debug
endif

	install -d $(cspkgdir)/DEBIAN
	for script in postinst postrm; do					\
	  sed -e 's/@@KVER@@/$(release)-$(abinum)-$*/g'				\
	       debian/control-scripts/$$script > $(cspkgdir)/DEBIAN/$$script;	\
	  chmod 755 $(cspkgdir)/DEBIAN/$$script;					\
	done

	# The flavour specific headers package
	if [ -z "$(filter $(no_alsa_flavours),$(target_flavour))" ] && grep 'CONFIG_ALSA=m' $(builddir)/build-$*/.config > /dev/null ; then \
		install -d $(hdrdir)/sound; \
		cp `find $(builddir)/build-$*/sound/alsa-kernel/include -type f` $(hdrdir)/sound; \
	fi

binary-modules-%: pkgimg = linux-backports-modules-$(release)-$(abinum)-$*
binary-modules-%: alsaimg = linux-backports-modules-alsa-$(release)-$(abinum)-$*
binary-modules-%: install-%
	dh_testdir
	dh_testroot

	for i in $(pkgimg) $(alsaimg) ; do \
	dh_installchangelogs -p$$i; \
	dh_installdocs -p$$i; \
	dh_compress -p$$i; \
	dh_fixperms -p$$i; \
	dh_installdeb -p$$i; \
	dh_gencontrol -p$$i; \
	dh_md5sums -p$$i; \
	dh_builddeb -p$$i -- -Zbzip2 -z9; \
	done

binary-debs: $(addprefix binary-modules-,$(flavours))
binary-arch: binary-debs binary-udebs
