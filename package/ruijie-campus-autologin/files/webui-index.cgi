#!/bin/sh

CONFIG_NAME="ruijie-campus-autologin"
SERVICE_NAME="ruijie-campus-autologin"
SESSION_DIR="/tmp/ruijie-campus-autologin-webui"

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
	printf '%s\n' "$FORM_DATA" | tr '&' '\n' | while IFS= read -r pair; do
		name="${pair%%=*}"
		value="${pair#*=}"
		[ "$name" = "$key" ] && {
			url_decode "$value"
			break
		}
	done
}

load_config() {
	enabled="$(uci -q get "$CONFIG_NAME.main.enabled")"
	portal_url="$(uci -q get "$CONFIG_NAME.main.portal_url")"
	username="$(uci -q get "$CONFIG_NAME.main.username")"
	operator="$(uci -q get "$CONFIG_NAME.main.operator")"
	webui_username="$(uci -q get "$CONFIG_NAME.main.webui_username")"
	webui_password="$(uci -q get "$CONFIG_NAME.main.webui_password")"
	webui_session_ttl="$(uci -q get "$CONFIG_NAME.main.webui_session_ttl")"

	[ "$enabled" = "1" ] || enabled=0
	[ -n "$portal_url" ] || portal_url="http://192.168.16.3/"
	[ -n "$operator" ] || operator="cmcc"
	[ -n "$webui_username" ] || webui_username="admin"
	[ -n "$webui_session_ttl" ] || webui_session_ttl="3600"
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

redirect_to_main() {
	echo "Status: 303 See Other"
	echo "Location: /cgi-bin/index.cgi"
	[ -n "$1" ] && echo "$1"
	echo
}

base_head() {
	cat <<-'EOF'
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width,initial-scale=1">
	<style>
	:root{--bg:#f6f7f9;--surface:#fff;--text:#17202a;--muted:#637083;--line:#d9dee7;--primary:#1769e0;--primary-weak:#e8f1ff;--ok:#16794c;--warn:#aa5b00;--danger:#b3261e;--shadow:0 10px 26px rgba(22,32,42,.08)}
	*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.shell{max-width:1060px;margin:0 auto;padding:28px 18px 38px}.topbar{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:18px}.brand h1{margin:0;font-size:24px;font-weight:700}.brand p{margin:3px 0 0;color:var(--muted)}.badge{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--line);border-radius:999px;background:var(--surface);padding:7px 11px;color:var(--muted)}.dot{width:9px;height:9px;border-radius:50%;background:var(--warn)}.dot.online{background:var(--ok)}.grid{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(260px,.8fr);gap:16px}.panel{background:var(--surface);border:1px solid var(--line);border-radius:8px;box-shadow:var(--shadow);padding:18px;transition:border-color .18s ease,box-shadow .18s ease,transform .18s ease}.panel:hover{border-color:#b9c7db;box-shadow:0 14px 34px rgba(22,32,42,.12);transform:translateY(-1px)}.panel h2{margin:0 0 14px;font-size:16px}.field{display:block;margin:0 0 13px}.field span{display:block;margin-bottom:6px;color:var(--muted);font-weight:600}input[type=text],input[type=password]{width:100%;height:40px;border:1px solid var(--line);border-radius:8px;background:#fff;padding:8px 10px;color:var(--text);outline:none;transition:border-color .15s ease,box-shadow .15s ease,background .15s ease}input[type=text]:hover,input[type=password]:hover{border-color:#aebbd0}input[type=text]:focus,input[type=password]:focus{border-color:var(--primary);box-shadow:0 0 0 3px rgba(23,105,224,.16)}.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}.switch{display:flex;align-items:center;justify-content:space-between;gap:12px;border:1px solid var(--line);border-radius:8px;padding:12px 13px;margin-bottom:14px;background:#fbfcfe}.switch input{position:absolute;opacity:0}.track{width:46px;height:26px;border-radius:999px;background:#c6ceda;position:relative;transition:background .18s ease}.track:after{content:"";position:absolute;top:3px;left:3px;width:20px;height:20px;border-radius:50%;background:#fff;box-shadow:0 2px 5px rgba(0,0,0,.2);transition:transform .18s ease}.switch input:checked+.track{background:var(--primary)}.switch input:checked+.track:after{transform:translateX(20px)}.options{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:6px 0 14px}.option{display:block;cursor:pointer}.option input{position:absolute;opacity:0}.option-card{display:block;border:1px solid var(--line);border-radius:8px;padding:11px 12px;background:#fff;transition:border-color .15s ease,background .15s ease,box-shadow .15s ease,transform .15s ease}.option-card strong{display:block}.option-card small{color:var(--muted)}.option:hover .option-card{border-color:#9fb2cc;transform:translateY(-1px)}.option input:checked+.option-card{border-color:var(--primary);background:var(--primary-weak);box-shadow:0 0 0 3px rgba(23,105,224,.12)}.actions{display:flex;flex-wrap:wrap;gap:10px}.btn{height:39px;border:1px solid transparent;border-radius:8px;padding:0 14px;background:var(--primary);color:#fff;font-weight:700;cursor:pointer;transition:background .15s ease,border-color .15s ease,box-shadow .15s ease,transform .15s ease}.btn:hover{background:#0f57bf;box-shadow:0 8px 18px rgba(23,105,224,.22);transform:translateY(-1px)}.btn:active{transform:translateY(0)}.btn.secondary{background:#fff;color:var(--text);border-color:var(--line)}.btn.secondary:hover{background:#f2f5f9;box-shadow:none}.btn.danger{background:#fff;color:var(--danger);border-color:#efc9c5}.btn.danger:hover{background:#fff4f2}.status{margin:0;white-space:pre-wrap;word-break:break-word;background:#111827;color:#e5edf8;border-radius:8px;padding:13px;max-height:300px;overflow:auto}.message{border:1px solid #f1c2bd;background:#fff6f5;color:var(--danger);border-radius:8px;padding:10px 12px;margin:0 0 14px}.login{max-width:440px;margin:9vh auto}.login .panel{padding:24px}.muted{color:var(--muted)}@media(max-width:780px){.topbar{align-items:flex-start;flex-direction:column}.grid,.row,.options{grid-template-columns:1fr}.shell{padding-top:20px}}
	</style>
	EOF
}

operator_checked() {
	[ "$operator" = "$1" ] && printf 'checked'
}

render_login() {
	local safe_message safe_webui_username

	safe_webui_username="$(printf '%s' "$webui_username" | html_escape)"
	[ -n "$1" ] && safe_message="$(printf '%s' "$1" | html_escape)"

	send_headers
	cat <<-EOF
	<!doctype html><html lang="zh-CN"><head><title>锐捷校园网自动认证系统</title>
	$(base_head)
	</head><body><main class="shell login">
	<section class="panel">
	<div class="brand"><h1>锐捷校园网自动认证系统</h1><p>请输入 WebUI 访问凭据</p></div>
	${safe_message:+<p class="message">$safe_message</p>}
	<form method="post" action="/cgi-bin/index.cgi">
	<input type="hidden" name="action" value="login">
	<label class="field"><span>用户名</span><input type="text" name="webui_user" value="$safe_webui_username" autocomplete="username"></label>
	<label class="field"><span>密码</span><input type="password" name="webui_pass" autocomplete="current-password"></label>
	<button class="btn" type="submit">登录</button>
	</form>
	</section>
	</main></body></html>
EOF
}

render_main() {
	local raw_status status_json safe_portal safe_username safe_operator enabled_checked status_dot status_text

	raw_status="$(/usr/bin/ruijie-campus-autologin-ctl status 2>/dev/null)"
	status_json="$(printf '%s' "$raw_status" | html_escape)"
	safe_portal="$(printf '%s' "$portal_url" | html_escape)"
	safe_username="$(printf '%s' "$username" | html_escape)"
	safe_operator="$(printf '%s' "$operator" | html_escape)"
	[ "$enabled" = "1" ] && enabled_checked="checked" || enabled_checked=""
	case "$raw_status" in
		*"\"state\":\"online\""*) status_dot="online"; status_text="在线" ;;
		*) status_dot=""; status_text="未确认" ;;
	esac

	send_headers
	cat <<-EOF
	<!doctype html><html lang="zh-CN"><head><title>锐捷校园网自动认证系统</title>
	$(base_head)
	</head><body><main class="shell">
	<header class="topbar">
	<div class="brand"><h1>锐捷校园网自动认证系统</h1><p>独立 WebUI</p></div>
	<div class="badge"><span class="dot $status_dot"></span><span>$status_text</span></div>
	</header>
	<div class="grid">
	<section class="panel">
	<h2>登录配置</h2>
	<form method="post" action="/cgi-bin/index.cgi">
	<input type="hidden" name="action" value="save">
	<label class="switch"><span><strong>自动登录</strong><br><span class="muted">服务会持续监听认证状态并自动重连</span></span><input type="checkbox" name="enabled" value="1" $enabled_checked><span class="track"></span></label>
	<label class="field"><span>认证地址</span><input type="text" name="portal_url" value="$safe_portal"></label>
	<div class="row">
	<label class="field"><span>账号</span><input type="text" name="username" value="$safe_username"></label>
	<label class="field"><span>密码</span><input type="password" name="password" value="" placeholder="留空则不修改"></label>
	</div>
	<div class="field"><span>运营商</span>
	<div class="options">
	<label class="option"><input type="radio" name="operator" value="cmcc" $(operator_checked cmcc)><span class="option-card"><strong>中国移动</strong><small>@cmcc</small></span></label>
	<label class="option"><input type="radio" name="operator" value="unicom" $(operator_checked unicom)><span class="option-card"><strong>中国联通</strong><small>@unicom</small></span></label>
	<label class="option"><input type="radio" name="operator" value="telecom" $(operator_checked telecom)><span class="option-card"><strong>中国电信</strong><small>@dx</small></span></label>
	<label class="option"><input type="radio" name="operator" value="none" $(operator_checked none)><span class="option-card"><strong>不追加</strong><small>原始账号</small></span></label>
	</div></div>
	<button class="btn" type="submit">保存配置</button>
	</form>
	</section>
	<aside>
	<section class="panel">
	<h2>状态</h2>
	<pre class="status">$status_json</pre>
	</section>
	<section class="panel">
	<h2>操作</h2>
	<div class="actions">
	<form method="post" action="/cgi-bin/index.cgi"><input type="hidden" name="action" value="toggle"><button class="btn secondary" type="submit">切换自动登录</button></form>
	<form method="post" action="/cgi-bin/index.cgi"><input type="hidden" name="action" value="logout"><button class="btn secondary" type="submit">注销校园网</button></form>
	<form method="post" action="/cgi-bin/index.cgi"><input type="hidden" name="action" value="exit"><button class="btn danger" type="submit">退出 WebUI</button></form>
	</div>
	</section>
	</aside>
	</div>
	</main></body></html>
EOF
}

FORM_DATA="$(read_post)"
load_config
mkdir -p "$SESSION_DIR"

action="$(form_get action)"

if [ "$action" = "login" ]; then
	login_user="$(form_get webui_user)"
	login_pass="$(form_get webui_pass)"
	if [ -z "$webui_password" ]; then
		render_login "WebUI 密码尚未设置，请先在 LuCI 中设置 WebUI 密码。"
		exit 0
	fi
	if [ "$login_user" = "$webui_username" ] && [ "$login_pass" = "$webui_password" ]; then
		token="$(new_token)"
		exp=$(( $(date +%s) + webui_session_ttl ))
		echo "$exp" > "$SESSION_DIR/$token"
		redirect_to_main "Set-Cookie: ruijie_session=$token; Path=/; HttpOnly; SameSite=Strict"
		exit 0
	fi
	render_login "用户名或密码错误。"
	exit 0
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
		redirect_to_main "Set-Cookie: ruijie_session=deleted; Path=/; Max-Age=0"
		exit 0
		;;
esac

render_main
