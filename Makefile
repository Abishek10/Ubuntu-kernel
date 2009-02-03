# Modify as you see fit, note this is built into crda,
# so if you change it here you will have to change crda.c
REG_BIN?=/usr/lib/crda/regulatory.bin
REG_GIT?=git://git.kernel.org/pub/scm/linux/kernel/git/linville/wireless-regdb.git

PREFIX ?= /usr/
MANDIR ?= $(PREFIX)/share/man/

SBINDIR ?= /sbin/

# Use a custom CRDA_UDEV_LEVEL when callling make install to
# change your desired level for the udev regulatory.rules
CRDA_UDEV_LEVEL?=85
UDEV_LEVEL=$(CRDA_UDEV_LEVEL)-
# You can customize this if your distributions uses
# a different location.
UDEV_RULE_DIR?=/lib/udev/rules.d/

# Used locally to retrieve all pubkeys during build time
PUBKEY_DIR=pubkeys

CFLAGS += -Wall -g

all: $(REG_BIN) crda intersect verify

ifeq ($(USE_OPENSSL),1)
CFLAGS += -DUSE_OPENSSL `pkg-config --cflags openssl`
LDLIBS += `pkg-config --libs openssl`

reglib.o: keys-ssl.c

else
CFLAGS += -DUSE_GCRYPT
LDLIBS += -lgcrypt

reglib.o: keys-gcrypt.c

endif
MKDIR ?= mkdir -p
INSTALL ?= install

NL1FOUND := $(shell pkg-config --atleast-version=1 libnl-1 && echo Y)
NL2FOUND := $(shell pkg-config --atleast-version=2 libnl-2.0 && echo Y)

ifeq ($(NL1FOUND),Y)
NLLIBNAME = libnl-1
endif

ifeq ($(NL2FOUND),Y)
CFLAGS += -DCONFIG_LIBNL20
NLLIBS += -lnl-genl
NLLIBNAME = libnl-2.0
endif

ifeq ($(NLLIBNAME),)
$(error Cannot find development files for any supported version of libnl)
endif

NLLIBS += `pkg-config --libs $(NLLIBNAME)`
CFLAGS += `pkg-config --cflags $(NLLIBNAME)`

ifeq ($(V),1)
Q=
NQ=@true
else
Q=@
NQ=@echo
endif

$(REG_BIN):
	$(NQ) '  EXIST ' $(REG_BIN)
	$(NQ)
	$(NQ) ERROR: The file: $(REG_BIN) is missing. You need this in place in order
	$(NQ) to build CRDA. You can get it from:
	$(NQ)
	$(NQ) $(REG_GIT)
	$(NQ)
	$(NQ) "Once cloned (no need to build) cp regulatory.bin to $(REG_BIN)"
	$(NQ)
	$(Q) exit 1

keys-%.c: utils/key2pub.py $(wildcard $(PUBKEY_DIR)/*.pem)
	$(NQ) '  GEN ' $@
	$(Q)./utils/key2pub.py --$* $(wildcard $(PUBKEY_DIR)/*.pem) $@

%.o: %.c regdb.h
	$(NQ) '  CC  ' $@
	$(Q)$(CC) -c $(CPPFLAGS) $(CFLAGS) -o $@ $<

crda: reglib.o crda.o
	$(NQ) '  LD  ' $@
	$(Q)$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS) $(NLLIBS)

regdbdump: reglib.o regdbdump.o print-regdom.o
	$(NQ) '  LD  ' $@
	$(Q)$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

intersect: reglib.o intersect.o print-regdom.o
	$(NQ) '  LD  ' $@
	$(Q)$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

verify: $(REG_BIN) regdbdump
	$(NQ) '  CHK  $(REG_BIN)'
	$(Q)./regdbdump $(REG_BIN) >/dev/null

%.gz: %
	@$(NQ) ' GZIP' $<
	$(Q)gzip < $< > $@

install: crda crda.8.gz regdbdump.8.gz
	$(NQ) '  INSTALL  crda'
	$(Q)$(MKDIR) $(DESTDIR)/sbin
	$(Q)$(INSTALL) -m 755 -t $(DESTDIR)/$(SBINDIR) crda
	$(NQ) '  INSTALL  regdbdump'
	$(Q)$(INSTALL) -m 755 -t $(DESTDIR)/$(SBINDIR) regdbdump
	$(NQ) '  INSTALL  $(UDEV_LEVEL)regulatory.rules'
	$(Q)$(MKDIR) $(DESTDIR)/$(UDEV_RULE_DIR)/
	@# This removes the old rule you may have, we were not
	@# putting it in the right place.
	$(Q)rm -f $(DESTDIR)/etc/udev/rules.d/regulatory.rules
	$(Q)ln -sf regulatory.rules udev/$(UDEV_LEVEL)regulatory.rules
	$(Q)$(INSTALL) -m 644 -t \
		$(DESTDIR)/$(UDEV_RULE_DIR)/ \
		udev/$(UDEV_LEVEL)regulatory.rules
	$(NQ) '  INSTALL  crda.8.gz'
	$(Q)$(MKDIR) $(DESTDIR)$(MANDIR)/man8/
	$(Q)$(INSTALL) -m 644 -t $(DESTDIR)/$(MANDIR)/man8/ crda.8.gz
	$(NQ) '  INSTALL  regdbdump.8.gz'
	$(Q)$(INSTALL) -m 644 -t $(DESTDIR)/$(MANDIR)/man8/ regdbdump.8.gz

clean:
	$(Q)rm -f crda regdbdump intersect *.o *~ *.pyc keys-*.c *.gz \
	udev/$(UDEV_LEVEL)regulatory.rules
