################################################################################
#
# sc3336-t23
#
################################################################################

SC3336_T23_SITE_METHOD = local
SC3336_T23_SITE = $(SC3336_T23_PKGDIR)/src
SC3336_T23_LICENSE = GPL-2.0+
SC3336_T23_DEPENDENCIES = ingenic-opensdk

SC3336_T23_MODULE_MAKE_OPTS = \
	ISP_INCLUDE=$(INGENIC_OPENSDK_DIR)/kernel/isp/$(OPENIPC_SOC_MODEL)/include \
	INSTALL_MOD_DIR=ingenic

define SC3336_T23_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0644 $(SC3336_T23_PKGDIR)/files/sc3336.yaml \
		$(TARGET_DIR)/etc/sensor/sc3336.yaml
	$(INSTALL) -D -m 0644 $(SC3336_T23_PKGDIR)/files/sc3336-t23.bin \
		$(TARGET_DIR)/etc/sensor/sc3336-t23.bin
	$(INSTALL) -D -m 0644 $(SC3336_T23_PKGDIR)/files/sensor_sc3336_t23.conf \
		$(TARGET_DIR)/etc/modprobe.d/sensor_sc3336_t23.conf
endef

$(eval $(kernel-module))
$(eval $(generic-package))
