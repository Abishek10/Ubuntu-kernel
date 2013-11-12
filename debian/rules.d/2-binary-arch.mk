# We don't want make removing intermediary stamps
.SECONDARY :

build-arch: $(addprefix build-modules-,$(flavours))

# Prepare the out-of-tree build directory

printenv:
	@echo "confdir           =  $(confdir)"
	@echo "stampdir          = $(stampdir)"
	@echo "release           = $(release)"
	@echo "revisions         = $(revisions)"
	@echo "revision          = $(revision)"
	@echo "prev_revisions    = $(prev_revisions)"
	@echo "prev_revision     = $(prev_revision)"
	@echo "abinum            = $(abinum)"
	@echo "flavours          = $(flavours)"

COMPAT_KDIR=/lib/modules/$(release)-$(abinum)-$(target_flavour)
NET_BUILD_KERNEL=$(release)-$(abinum)-$(target_flavour)
make_cw_defconfig = make defconfig-wifi
make_compat = make $(conc_level)
make_compat += KLIB=$(COMPAT_KDIR) KLIB_BUILD=$(COMPAT_KDIR)/build
make_compat += MADWIFI=
make_compat += OLD_IWL=

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
ifneq ($(CWDIRS),)
	#
	# compat-wireless preparation
	#
	# Gross hackery to make the compat firmware class unique to this ABI
	#
	for i in $(CWDIRS); do \
		cw_dir=$(builddir)/build-$*/$$i; \
		if [ -e $${cw_dir}/compat/scripts/compat_firmware_install ] ; then fw_install_file=compat/scripts/compat_firmware_install; elif [ -e $${cw_dir}/scripts/backport_firmware_install.sh ] ; then fw_install_file=scripts/backport_firmware_install.sh; fi; \
		if [ -e $${cw_dir}/udev/ubuntu/50-compat_firmware.rules ] ; then fw_rules_file=udev/ubuntu/50-compat_firmware.rules; elif [ -e $${cw_dir}/udev/50-compat_firmware.rules ] ; then fw_rules_file=udev/50-compat_firmware.rules; fi; \
		sed -i 's/compat_firmware/compat_firmware_'$(abinum)_$(target_flavour)'/g' \
			$${cw_dir}/compat/compat_firmware_class.c \
			$${cw_dir}/$${fw_install_file} \
			$${cw_dir}/$${fw_rules_file}; \
		mv -v $${cw_dir}/$${fw_rules_file} $${cw_dir}/udev/ubuntu/50-compat_firmware_$(abinum)_$(target_flavour).rules; \
		mv -v $${cw_dir}/udev/ubuntu/compat_firmware.sh $${cw_dir}/udev/ubuntu/compat_firmware_$(abinum)_$(target_flavour).sh; \
	done
endif

ifeq ($(do_hv),true)
	# Extract the files we will need to rebuild from the source tarball
	# for the latest build.
	(cd $(builddir)/build-$* && \
		tar xvf /usr/src/linux-source-$(release)/linux-source-$(release).tar.bz2 \
		linux-source-$(release)/drivers/hid/hid-hyperv.c \
		linux-source-$(release)/drivers/net/hyperv/netvsc_drv.c \
		linux-source-$(release)/drivers/net/hyperv/rndis_filter.c \
		linux-source-$(release)/drivers/net/hyperv/netvsc.c \
		linux-source-$(release)/drivers/net/hyperv/hyperv_net.h \
		linux-source-$(release)/drivers/scsi/storvsc_drv.c; \
		find linux-source-$(release) -type f -print | \
		while read f; do \
			fd=`echo "$$f" | sed -e "s/linux-source-$(release)/hv/"`; \
			echo cp -p "$$f" "$$fd"; \
			cp -p "$$f" "$$fd"; \
		done; \
	)
endif

	cat $(confdir)/$(arch) > $(builddir)/build-$*/.config
	# XXX: generate real config
	touch $(builddir)/build-$*/ubuntu-config.h
	touch $(builddir)/build-$*/ubuntu-build
	touch $@

# Do the actual build, including image and modules
build-modules-%: $(stampdir)/stamp-build-%
	@# Empty for make to be happy
$(stampdir)/stamp-build-%: target_flavour = $*
$(stampdir)/stamp-build-%: build_arch_t = $(call custom_override,build_arch,$*)
$(stampdir)/stamp-build-%: prepare-%
	@echo "Building $*..."
ifneq ($(CWDIRS),)
	for i in $(CWDIRS); do \
		for j in $(NEWER_CWDIRS); do \
			if [ $$i == $$j ]; then cd $(builddir)/build-$*/$$i && $(make_cw_defconfig); fi; \
		done; \
		cd $(builddir)/build-$*/$$i && $(make_compat); \
	done
endif
ifeq ($(do_net),true)
	BUILD_KERNEL=$(NET_BUILD_KERNEL) $(kmake) $(conc_level) M=$(builddir)/build-$(target_flavour)/net modules
endif
ifeq ($(do_hv),true)
	BUILD_KERNEL=$(NET_BUILD_KERNEL) $(kmake) $(conc_level) M=$(builddir)/build-$(target_flavour)/hv modules

	ln -s ../../drivers/hv/include/linux/hyperv.h $(builddir)/build-$*/hv/tools/hv/hyperv.h
	make -C $(builddir)/build-$*/hv/tools/hv CROSS_COMPILE=$(CROSS_COMPILE)
endif
	touch $@

# Install the finished build
install-%: csmoddir = $(cspkgdir)/lib/modules/$(release)-$(abinum)-$*
install-%: netpkgdir = $(CURDIR)/debian/linux-backports-modules-net-$(release)-$(abinum)-$*
install-%: netmoddir = $(netpkgdir)/lib/modules/$(release)-$(abinum)-$*
install-%: hvpkgdir = $(CURDIR)/debian/linux-backports-modules-hv-$(release)-$(abinum)-$*
install-%: hvmoddir = $(hvpkgdir)/lib/modules/$(release)-$(abinum)-$*
install-%: lbmbasehdrpkg = linux-headers-lbm-$(release)$(debnum)
install-%: lbmhdrpkg = $(lbmbasehdrpkg)-$*
install-%: hdrdir = $(CURDIR)/debian/$(lbmhdrpkg)/usr/src/$(lbmhdrpkg)
install-%: target_flavour = $*
install-%: build_arch_t = $(call custom_override,build_arch,$*)
install-%: build-modules-%
	dh_testdir
	dh_testroot

ifneq ($(CWDIRS),)
	for i in $(CWDIRS); do \
		cw=$$i; \
		cwpkgdir=$(CURDIR)/debian/linux-backports-modules-$${cw}-$(release)-$(abinum)-$(target_flavour); \
		cwblddir=$(builddir)/build-$(target_flavour)/$${cw}; \
		cwmoddir=$${cwpkgdir}/lib/modules/$(release)-$(abinum)-$(target_flavour)/updates; \
		dstfirmdir=$${cwpkgdir}/lib/firmware/updates/$(release)-$(abinum)-$(target_flavour); \
		srcfirmdir=$(CURDIR)/updates/$${cw}-firmware; \
\
		dh_clean -k -plinux-backports-modules-$${cw}-$(release)-$(abinum)-$(target_flavour); \
\
		install -d $${cwmoddir}/$${cw}; \
		find $(builddir)/build-$(target_flavour)/$${cw} -type f -name '*.ko' | \
		while read f ; do \
			cp -v $${f} $${cwmoddir}/$${cw}/`basename $${f}`; \
		done; \
\
		find $${cwpkgdir}/ -type f -name \*.ko -print | xargs -r strip --strip-debug; \
\
		install -d $${cwpkgdir}/DEBIAN; \
		for script in postinst postrm; do                                       \
			sed -e 's/@@KVER@@/$(release)-$(abinum)-$(target_flavour)/g'                            \
				debian/control-scripts/$$script > $${cwpkgdir}/DEBIAN/$$script; \
			chmod 755 $${cwpkgdir}/DEBIAN/$$script;                                 \
		done; \
		install -d $${cwpkgdir}/lib/udev; \
		install --mode=0755 $${cwblddir}/udev/ubuntu/compat_firmware_$(abinum)_$(target_flavour).sh $${cwpkgdir}/lib/udev; \
		install -d $${cwpkgdir}/lib/udev/rules.d; \
		install --mode=0644 $${cwblddir}/udev/ubuntu/50-compat_firmware_$(abinum)_$(target_flavour).rules $${cwpkgdir}/lib/udev/rules.d; \
\
		install -d $${dstfirmdir}; \
		echo $${srcfirmdir} $${dstfirmdir}; \
		if [ -d $${srcfirmdir} ] ; then cp -rv $${srcfirmdir}/* $${dstfirmdir}; fi; \
	done
endif

ifeq ($(do_net),true)
	#
	# Build the network package.
	#
	install -d $(netmoddir)/updates/net
	find $(builddir)/build-$*/net -type f -name '*.ko' | \
	while read f ; do \
		cp -v $${f} $(netmoddir)/updates/net/`basename $${f}`; \
	done

	find $(netpkgdir)/ -type f -name \*.ko -print | xargs -r strip --strip-debug

	install -d $(netpkgdir)/DEBIAN
	for script in postinst postrm; do					\
	  sed -e 's/@@KVER@@/$(release)-$(abinum)-$*/g'				\
	       debian/control-scripts/$$script > $(netpkgdir)/DEBIAN/$$script;	\
	  chmod 755 $(netpkgdir)/DEBIAN/$$script;					\
	done
endif

ifeq ($(do_hv),true)
	#
	# Build the hv package.
	#
	BUILD_KERNEL=$(NET_BUILD_KERNEL) $(kmake) INSTALL_MOD_PATH=$(hvpkgdir) INSTALL_MOD_DIR=updates $(conc_level) M=$(builddir)/build-$(target_flavour)/hv modules_install

	install -d $(hvpkgdir)/usr/sbin
	install -s -m755 $(builddir)/build-$*/hv/tools/hv/hv_kvp_daemon \
	       $(hvpkgdir)/usr/sbin/hv_kvp_daemon_$(release)-$(abinum)-$(target_flavour)

	find $(hvpkgdir)/ -type f -name \*.ko -print | xargs -r strip --strip-debug

	install -d $(hvpkgdir)/DEBIAN
	for script in postinst postrm; do					\
	  sed -e 's/@@KVER@@/$(release)-$(abinum)-$*/g'				\
	       debian/control-scripts/$$script > $(hvpkgdir)/DEBIAN/$$script;	\
	  chmod 755 $(hvpkgdir)/DEBIAN/$$script;				\
	done
endif

	#
	# The flavour specific headers package
	#
	install -d $(hdrdir)/include
ifeq ($(do_net),true)
	tar -C $(builddir)/build-$*/net -chf - include | tar -C $(hdrdir) -xf -
endif
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

cw_pkg_list_pre = $(addprefix linux-backports-modules-,$(CWDIRS))
cw_pkg_list_suf = $(addsuffix -$(release)-$(abinum)-$*,$(cw_pkg_list_pre))

packages-true =
packages-true += $(cw_pkg_list_suf)
packages-$(do_net) += linux-backports-modules-net-$(release)-$(abinum)-$*
packages-$(do_hv) += linux-backports-modules-hv-$(release)-$(abinum)-$*

binary-modules-%: install-%
	dh_testdir
	dh_testroot

	for i in $(packages-true) ; do \
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
