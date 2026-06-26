#!/bin/sh

CONFIG_NAME="ruijie-campus-autologin"
SERVICE_NAME="ruijie-campus-autologin"
SESSION_DIR="/tmp/ruijie-campus-autologin-webui"

. /lib/functions.sh

url_decode() {
	local data="${1//+/ }"
	printf '%b' "${data//%/\\x}"
}

html_escape() {
	sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g; s/"/\&quot;/g'
}

read_post() {
	[ "$REQUEST_METHOD" = "POST" ] || return 0
	[ -n "$CONTENT_LENGTH" ] || return 0
	dd bs=1 count="$CONTENT_LENGTH" 2>/dev/null
}

form_get() {
	local key="$1" pair name value
	printf '%s' "$FORM_DATA" | tr '&' '\n' | while IFS= read -r pair; do
		name="${pair%%=*}"
		value="${pair#*=}"
		[ "$name" = "$key" ] && {
			url_decode "$value"
			break
		}
	done
}

load_config() {
	config_load "$CONFIG_NAME"
	config_get_bool enabled main enabled 0
	config_get portal_url main portal_url "http://192.168.16.3/"
	config_get username main username ""
	config_get password main password ""
	config_get operator main operator "cmcc"
	config_get webui_username main webui_username "admin"
	config_get webui_password main webui_password ""
	config_get webui_session_ttl main webui_session_ttl "3600"
}

cookie_value() {
	printf '%s' "$HTTP_COOKIE" | tr ';' '\n' | sed 's/^ *//' | sed -n "s/^$1=//p" | head -n 1
}

new_token() {
	dd if=/dev/urandom bs=16 count=1 2>/dev/null | hexdump -ve '1/1 "%02x"'
}

session_valid() {
	local token file now exp

	token="$(cookie_value ruijie_session)"
	[ -n "$token" ] || return 1
	case "$token" in *[!0-9a-fA-F]*) return 1 ;; esac
	file="$SESSION_DIR/$token"
	[ -f "$file" ] || return 1
	now="$(date +%s)"
	exp="$(cat "$file" 2>/dev/null)"
	[ "$now" -lt "$exp" ] 2>/dev/null
}

send_headers() {
	echo "Content-Type: text/html; charset=utf-8"
	[ -n "$1" ] && echo "$1"
	echo
}

render_login() {
	send_headers
	cat <<-EOF
	<!doctype html><html><head><meta charset="utf-8"><title>锐捷校园网自动认证系统</title>
	<style>body{font-family:sans-serif;max-width:520px;margin:60px auto;padding:0 16px}label{display:block;margin-top:12px}input{width:100%;padding:8px}button{margin-top:16px;padding:8px 16px}</style></head>
	<body><h1>锐捷校园网自动认证系统</h1><form method="post">
	<input type="hidden" name="action" value="login">
	<label>用户名<input name="webui_user" value="admin"></label>
	<label>密码<input name="webui_pass" type="password"></label>
	<button type="submit">登录</button>
	</form></body></html>
EOF
}

render_main() {
	local status_json safe_portal safe_username safe_operator enabled_checked

	status_json="$(/usr/bin/ruijie-campus-autologin-ctl status 2>/dev/null)"
	safe_portal="$(printf '%s' "$portal_url" | html_escape)"
	safe_username="$(printf '%s' "$username" | html_escape)"
	safe_operator="$(printf '%s' "$operator" | html_escape)"
	[ "$enabled" = "1" ] && enabled_checked="checked" || enabled_checked=""

	send_headers
	cat <<-EOF
	<!doctype html><html><head><meta charset="utf-8"><title>锐捷校园网自动认证系统</title>
	<style>body{font-family:sans-serif;max-width:760px;margin:32px auto;padding:0 16px}label{display:block;margin-top:12px}input,select{width:100%;padding:8px}.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}.card{border:1px solid #ddd;border-radius:8px;padding:16px;margin:16px 0}button{margin-top:16px;padding:8px 16px}</style></head>
	<body><h1>锐捷校园网自动认证系统</h1>
	<div class="card"><h2>状态</h2><pre>$status_json</pre></div>
	<form method="post" class="card">
	<input type="hidden" name="action" value="save">
	<label><input type="checkbox" name="enabled" value="1" $enabled_checked style="width:auto"> 开启自动登录</label>
	<label>认证地址<input name="portal_url" value="$safe_portal"></label>
	<div class="row"><label>账号<input name="username" value="$safe_username"></label><label>密码<input name="password" type="password" value=""></label></div>
	<label>运营商<select name="operator">
	<option value="cmcc">中国移动 (@cmcc)</option><option value="unicom">中国联通 (@unicom)</option><option value="telecom">中国电信 (@dx)</option><option value="none">不追加后缀</option>
	</select></label>
	<p>当前运营商：$safe_operator</p>
	<button type="submit">保存配置</button>
	</form>
	<form method="post"><input type="hidden" name="action" value="toggle"><button type="submit">开启/关闭自动登录</button></form>
	<form method="post"><input type="hidden" name="action" value="logout"><button type="submit">注销登录</button></form>
	<form method="post"><input type="hidden" name="action" value="exit"><button type="submit">退出</button></form>
	</body></html>
EOF
}

FORM_DATA="$(read_post)"
load_config
mkdir -p "$SESSION_DIR"

action="$(form_get action)"

if [ "$action" = "login" ]; then
	login_user="$(form_get webui_user)"
	login_pass="$(form_get webui_pass)"
	if [ -n "$webui_password" ] && [ "$login_user" = "$webui_username" ] && [ "$login_pass" = "$webui_password" ]; then
		token="$(new_token)"
		exp=$(( $(date +%s) + webui_session_ttl ))
		echo "$exp" > "$SESSION_DIR/$token"
		send_headers "Set-Cookie: ruijie_session=$token; Path=/; HttpOnly; SameSite=Strict"
		echo '<meta http-equiv="refresh" content="0; url=/cgi-bin/index.cgi">'
		exit 0
	fi
fi

if ! session_valid; then
	render_login
	exit 0
fi

case "$action" in
	save)
		new_enabled="$(form_get enabled)"
		new_portal="$(form_get portal_url)"
		new_username="$(form_get username)"
		new_password="$(form_get password)"
		new_operator="$(form_get operator)"
		[ "$new_enabled" = "1" ] && uci set "$CONFIG_NAME.main.enabled=1" || uci set "$CONFIG_NAME.main.enabled=0"
		[ -n "$new_portal" ] && uci set "$CONFIG_NAME.main.portal_url=$new_portal"
		uci set "$CONFIG_NAME.main.username=$new_username"
		[ -n "$new_password" ] && uci set "$CONFIG_NAME.main.password=$new_password"
		uci set "$CONFIG_NAME.main.operator=$new_operator"
		uci commit "$CONFIG_NAME"
		/etc/init.d/$SERVICE_NAME restart >/dev/null 2>&1 || true
		load_config
		;;
	toggle)
		if [ "$enabled" = "1" ]; then
			uci set "$CONFIG_NAME.main.enabled=0"
			uci commit "$CONFIG_NAME"
			/etc/init.d/$SERVICE_NAME stop >/dev/null 2>&1 || true
		else
			uci set "$CONFIG_NAME.main.enabled=1"
			uci commit "$CONFIG_NAME"
			/etc/init.d/$SERVICE_NAME restart >/dev/null 2>&1 || true
		fi
		load_config
		;;
	logout)
		/usr/bin/ruijie-campus-autologin-ctl logout >/dev/null 2>&1 || true
		;;
	exit)
		rm -f "$SESSION_DIR/$(cookie_value ruijie_session)"
		send_headers "Set-Cookie: ruijie_session=deleted; Path=/; Max-Age=0"
		echo '<meta http-equiv="refresh" content="0; url=/cgi-bin/index.cgi">'
		exit 0
		;;
esac

render_main
