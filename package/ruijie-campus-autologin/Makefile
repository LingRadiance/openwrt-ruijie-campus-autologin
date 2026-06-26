include $(TOPDIR)/rules.mk

PKG_NAME:=ruijie-campus-autologin
PKG_VERSION:=1.1.0
PKG_RELEASE:=1

PKG_MAINTAINER:=ruijie-campus-autologin
PKG_LICENSE:=MIT

include $(INCLUDE_DIR)/package.mk

define Package/ruijie-campus-autologin
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Ruijie campus network auto login daemon
  DEPENDS:=+curl +uhttpd
endef

define Package/ruijie-campus-autologin/description
  A small procd daemon for OpenWrt that monitors Ruijie/Dr.COM campus
  network login state and automatically logs in with configured credentials.
endef

define Build/Compile
endef

define Package/ruijie-campus-autologin/conffiles
/etc/config/ruijie-campus-autologin
endef

define Package/ruijie-campus-autologin/install
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_BIN) ./files/ruijie-campus-autologin $(1)/usr/bin/ruijie-campus-autologin
	$(INSTALL_BIN) ./files/ruijie-campus-autologin-ctl $(1)/usr/bin/ruijie-campus-autologin-ctl
	$(INSTALL_BIN) ./files/ruijie-campus-autologin-remote $(1)/usr/bin/ruijie-campus-autologin-remote
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/ruijie-campus-autologin.init $(1)/etc/init.d/ruijie-campus-autologin
	$(INSTALL_BIN) ./files/ruijie-campus-autologin-webui.init $(1)/etc/init.d/ruijie-campus-autologin-webui
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_CONF) ./files/ruijie-campus-autologin.config $(1)/etc/config/ruijie-campus-autologin
	$(INSTALL_DIR) $(1)/usr/share/ruijie-campus-autologin/webui/cgi-bin
	$(INSTALL_DATA) ./files/webui-index.html $(1)/usr/share/ruijie-campus-autologin/webui/index.html
	$(INSTALL_BIN) ./files/webui-index.cgi $(1)/usr/share/ruijie-campus-autologin/webui/cgi-bin/index.cgi
endef

$(eval $(call BuildPackage,ruijie-campus-autologin))
