# Ruijie Campus Autologin for OpenWrt

OpenWrt package and LuCI app for Ruijie/Dr.COM campus network auto login.

## Features

- Watches campus network login state.
- Logs in automatically with configured account, password, and operator suffix.
- Supports Dr.COM `/drcom/login` JSONP-style login.
- Provides a LuCI page under `Services`.
- Shows service/login status in LuCI.
- Supports logout from LuCI.
- Can auto-detect and fill common portal parameters.

## Packages

- `package/ruijie-campus-autologin`: daemon, init script, UCI config, control script
- `package/luci-app-ruijie-campus-autologin`: LuCI frontend

## Build

Copy this repository into an OpenWrt source tree or SDK package feed, then run:

```sh
make menuconfig
make package/ruijie-campus-autologin/compile V=s
make package/luci-app-ruijie-campus-autologin/compile V=s
```

## Manual Install For Testing

```sh
install -m 755 package/ruijie-campus-autologin/files/ruijie-campus-autologin /usr/bin/
install -m 755 package/ruijie-campus-autologin/files/ruijie-campus-autologin-ctl /usr/bin/
install -m 755 package/ruijie-campus-autologin/files/ruijie-campus-autologin.init /etc/init.d/ruijie-campus-autologin
install -m 644 package/ruijie-campus-autologin/files/ruijie-campus-autologin.config /etc/config/ruijie-campus-autologin
```

For LuCI:

```sh
install -m 644 package/luci-app-ruijie-campus-autologin/root/usr/share/luci/menu.d/luci-app-ruijie-campus-autologin.json /usr/share/luci/menu.d/
install -m 644 package/luci-app-ruijie-campus-autologin/root/usr/share/rpcd/acl.d/luci-app-ruijie-campus-autologin.json /usr/share/rpcd/acl.d/
mkdir -p /www/luci-static/resources/view/services
install -m 644 package/luci-app-ruijie-campus-autologin/htdocs/luci-static/resources/view/services/ruijie-campus-autologin.js /www/luci-static/resources/view/services/
rm -rf /tmp/luci-indexcache /tmp/luci-modulecache
/etc/init.d/rpcd restart
/etc/init.d/uhttpd restart
```

## Configuration

Edit `/etc/config/ruijie-campus-autologin` or use LuCI:

```sh
uci set ruijie-campus-autologin.main.enabled='1'
uci set ruijie-campus-autologin.main.username='your_username'
uci set ruijie-campus-autologin.main.password='your_password'
uci set ruijie-campus-autologin.main.operator='cmcc'
uci commit ruijie-campus-autologin
/etc/init.d/ruijie-campus-autologin enable
/etc/init.d/ruijie-campus-autologin restart
```

## License

MIT
