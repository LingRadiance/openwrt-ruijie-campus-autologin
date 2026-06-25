# 锐捷校园网自动认证系统

# Ruijie Campus Autologin for OpenWrt

这是一个面向 OpenWrt 的锐捷/Dr.COM 校园网自动认证软件包，包含后台自动登录服务和 LuCI 前端页面。项目默认发布语言为中文，英文标题保留用于检索和兼容国际化命名。

## 功能特性

- 自动监听校园网认证状态。
- 未登录时自动使用配置的账号、密码和运营商后缀发起登录。
- 支持 Dr.COM `/drcom/login` JSONP 风格认证接口。
- 支持自动检测并填充常见认证参数。
- LuCI 页面已汉化，入口位于 `服务 -> Ruijie Campus Autologin`。
- LuCI 页面显示服务状态、登录状态、当前账号、更新时间和状态信息。
- 支持在 LuCI 页面中手动刷新状态、自动填充参数、注销登录。

## 软件包结构

- `package/ruijie-campus-autologin`：后台守护进程、init 脚本、UCI 配置、状态/注销/检测控制脚本。
- `package/luci-app-ruijie-campus-autologin`：LuCI 前端页面、菜单和 ACL 权限。

## 直接安装

在 GitHub Release 中下载 `.ipk` 文件，然后在 OpenWrt LuCI 的“系统 -> 软件包 -> 上传软件包”中上传安装，或通过命令行安装：

```sh
opkg install ruijie-campus-autologin_*.ipk
```

安装后刷新 LuCI 页面，进入：

```text
服务 -> Ruijie Campus Autologin
```

## 基础配置

可以在 LuCI 页面配置，也可以通过 SSH 使用 UCI：

```sh
uci set ruijie-campus-autologin.main.enabled='1'
uci set ruijie-campus-autologin.main.username='your_username'
uci set ruijie-campus-autologin.main.password='your_password'
uci set ruijie-campus-autologin.main.operator='cmcc'
uci commit ruijie-campus-autologin
/etc/init.d/ruijie-campus-autologin enable
/etc/init.d/ruijie-campus-autologin restart
```

运营商字段常用值：

- `cmcc`：中国移动，账号后追加 `@cmcc`
- `unicom`：中国联通，账号后追加 `@unicom`
- `telecom`：中国电信，账号后追加 `@dx`
- `none`：不追加后缀

如果账号中已经包含 `@`，脚本不会重复追加后缀。

## 自动填充参数

LuCI 页面中的“自动填充参数”按钮会访问认证首页，并尝试自动识别和填充：

- 登录接口路径
- 注销接口路径
- `0MKKey`
- 回调函数名
- 终端类型
- JS 版本
- 版本随机值
- `para`

该功能用于适配更多锐捷/Dr.COM 认证页面。自动检测不保证覆盖所有学校的定制认证系统，检测后建议先查看页面中的参数是否符合实际登录请求。

## 从源码构建

将本仓库放入 OpenWrt 源码树或 SDK 的 package feed 中，然后执行：

```sh
make menuconfig
make package/ruijie-campus-autologin/compile V=s
make package/luci-app-ruijie-campus-autologin/compile V=s
```

## 手动部署测试

后台服务：

```sh
install -m 755 package/ruijie-campus-autologin/files/ruijie-campus-autologin /usr/bin/
install -m 755 package/ruijie-campus-autologin/files/ruijie-campus-autologin-ctl /usr/bin/
install -m 755 package/ruijie-campus-autologin/files/ruijie-campus-autologin.init /etc/init.d/ruijie-campus-autologin
install -m 644 package/ruijie-campus-autologin/files/ruijie-campus-autologin.config /etc/config/ruijie-campus-autologin
```

LuCI 页面：

```sh
install -m 644 package/luci-app-ruijie-campus-autologin/root/usr/share/luci/menu.d/luci-app-ruijie-campus-autologin.json /usr/share/luci/menu.d/
install -m 644 package/luci-app-ruijie-campus-autologin/root/usr/share/rpcd/acl.d/luci-app-ruijie-campus-autologin.json /usr/share/rpcd/acl.d/
mkdir -p /www/luci-static/resources/view/services
install -m 644 package/luci-app-ruijie-campus-autologin/htdocs/luci-static/resources/view/services/ruijie-campus-autologin.js /www/luci-static/resources/view/services/
rm -rf /tmp/luci-indexcache /tmp/luci-modulecache
/etc/init.d/rpcd restart
/etc/init.d/uhttpd restart
```

## 许可证

MIT
