################################################################################
#
# tmi8152-motor
#
################################################################################

TMI8152_MOTOR_VERSION = 4d5a666b77bc2af57cd00af20a088107c60d017e
TMI8152_MOTOR_SITE = $(call github,sstepansky,tmi8152-spi-dev,$(TMI8152_MOTOR_VERSION))
TMI8152_MOTOR_LICENSE = GPL-2.0
TMI8152_MOTOR_LICENSE_FILES = LICENSE

TMI8152_MOTOR_MODULE_MAKE_OPTS = KSRC=$(LINUX_DIR)

define TMI8152_MOTOR_LINUX_CONFIG_FIXUPS
	$(call KCONFIG_ENABLE_OPT,CONFIG_SPI)
	$(call KCONFIG_ENABLE_OPT,CONFIG_SPI_MASTER)
	$(call KCONFIG_ENABLE_OPT,CONFIG_JZ_SPI)
	$(call KCONFIG_ENABLE_OPT,CONFIG_JZ_SPI0)
	$(call KCONFIG_ENABLE_OPT,CONFIG_JZ_SPI0_PB)
	$(call KCONFIG_ENABLE_OPT,CONFIG_JZ_SPI0_PB_1)
endef

define TMI8152_MOTOR_BUILD_CMDS
	$(TARGET_CC) $(TARGET_CFLAGS) -Wall -Os -s \
		$(TMI8152_MOTOR_PKGDIR)/src/tmi-ptz.c -o $(@D)/tmi-ptz
endef

# Installs tmi8152_spi_dev.ko and motor.ko to /lib/modules/<ver>/extra (the
# kernel-module infra). openingenic also builds an ingenic/motor.ko; the
# device profile excludes that one and loads extra/motor.ko by path.
define TMI8152_MOTOR_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/tmi-ptz $(TARGET_DIR)/usr/bin/tmi-ptz
endef

$(eval $(kernel-module))
$(eval $(generic-package))
