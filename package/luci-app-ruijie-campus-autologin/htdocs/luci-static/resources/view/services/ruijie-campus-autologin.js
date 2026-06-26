'use strict';
'require view';
'require form';
'require uci';
'require fs';
'require poll';
'require ui';

function parseJSON(text) {
	try {
		return JSON.parse(text || '{}');
	} catch (e) {
		return {};
	}
}

function renderStatus(data) {
	var stateMap = {
		online: '已登录',
		offline: '未登录',
		error: '错误',
		checking: '检查中',
		logging_in: '登录中',
		login_failed: '登录失败',
		cooling_down: '冷却等待',
		disabled: '服务未启用',
		waiting_config: '等待配置',
		logged_out: '已发送注销',
		unknown: '未知'
	};

	return E('div', { 'class': 'cbi-section' }, [
		E('h3', {}, _('登录状态')),
		E('div', { 'class': 'table' }, [
			E('div', { 'class': 'tr' }, [
				E('div', { 'class': 'td left', 'style': 'width: 25%' }, _('服务状态')),
				E('div', { 'class': 'td left' }, data.running ? '运行中' : '未运行')
			]),
			E('div', { 'class': 'tr' }, [
				E('div', { 'class': 'td left' }, _('登录状态')),
				E('div', { 'class': 'td left' }, stateMap[data.state] || data.state || '未知')
			]),
			E('div', { 'class': 'tr' }, [
				E('div', { 'class': 'td left' }, _('当前账号')),
				E('div', { 'class': 'td left' }, data.account || '-')
			]),
			E('div', { 'class': 'tr' }, [
				E('div', { 'class': 'td left' }, _('更新时间')),
				E('div', { 'class': 'td left' }, data.updated || '-')
			]),
			E('div', { 'class': 'tr' }, [
				E('div', { 'class': 'td left' }, _('状态信息')),
				E('div', { 'class': 'td left' }, data.message || '-')
			]),
			E('div', { 'class': 'tr' }, [
				E('div', { 'class': 'td left' }, _('检测失败次数')),
				E('div', { 'class': 'td left' }, String(data.check_fail_count || 0))
			]),
			E('div', { 'class': 'tr' }, [
				E('div', { 'class': 'td left' }, _('登录失败次数')),
				E('div', { 'class': 'td left' }, String(data.login_fail_count || 0))
			]),
			E('div', { 'class': 'tr' }, [
				E('div', { 'class': 'td left' }, _('登录成功次数')),
				E('div', { 'class': 'td left' }, String(data.login_success_count || 0))
			])
		])
	]);
}

return view.extend({
	load: function() {
		return Promise.all([
			uci.load('ruijie-campus-autologin'),
			fs.exec_direct('/usr/bin/ruijie-campus-autologin-ctl', [ 'status' ]).catch(function() { return '{}'; }),
			fs.exec_direct('/usr/bin/ruijie-campus-autologin-ctl', [ 'version' ]).catch(function() { return '{}'; })
		]);
	},

	refreshStatus: function(node) {
		return fs.exec_direct('/usr/bin/ruijie-campus-autologin-ctl', [ 'status' ]).then(function(res) {
			node.innerHTML = '';
			node.appendChild(renderStatus(parseJSON(res)));
		});
	},

	render: function(data) {
		var m, s, o, statusNode, versionData, statusWrap;

		statusNode = E('div', {}, renderStatus(parseJSON(data[1])));
		versionData = parseJSON(data[2]);

		m = new form.Map('ruijie-campus-autologin', _('锐捷校园网自动认证系统'));

		s = m.section(form.NamedSection, 'main', 'login', _('配置'));
		s.anonymous = true;
		s.tab('general', _('常规设置'));
		s.tab('advanced', _('高级设置'));
		s.tab('version', _('版本设置'));

		o = s.taboption('general', form.Flag, 'enabled', _('开启自动登录'));
		o.default = o.disabled;

		o = s.taboption('general', form.Value, 'portal_url', _('认证地址'));
		o.default = 'http://192.168.16.3/';
		o.placeholder = 'http://192.168.16.3/';

		o = s.taboption('general', form.Value, 'username', _('账号'));
		o.rmempty = false;

		o = s.taboption('general', form.Value, 'password', _('密码'));
		o.password = true;
		o.rmempty = false;

		o = s.taboption('general', form.ListValue, 'operator', _('运营商'));
		o.value('cmcc', _('中国移动 (@cmcc)'));
		o.value('unicom', _('中国联通 (@unicom)'));
		o.value('telecom', _('中国电信 (@dx)'));
		o.value('none', _('不追加后缀'));
		o.value('campus', _('校园用户'));
		o.value('teacher', _('教师登录'));
		o.value('continuing', _('继续教育学院'));
		o.default = 'cmcc';

		o = s.taboption('general', form.Flag, 'webui_enabled', _('开启独立 WebUI'));
		o.default = o.disabled;

		o = s.taboption('general', form.Value, 'webui_port', _('独立 WebUI 端口'));
		o.datatype = 'port';
		o.default = '9099';

		o = s.taboption('general', form.Flag, 'webui_listen_lan', _('WebUI 面向 LAN 开放'));
		o.default = o.enabled;

		o = s.taboption('general', form.Flag, 'webui_listen_wan', _('WebUI 面向 WAN 开放'));
		o.default = o.disabled;

		o = s.taboption('general', form.Value, 'webui_username', _('WebUI 用户名'));
		o.default = 'admin';

		o = s.taboption('general', form.Value, 'webui_password', _('WebUI 密码'));
		o.password = true;
		o.rmempty = true;
		o.description = _('开启独立 WebUI 前必须设置密码。该 WebUI 可修改登录配置并开启或关闭自动登录。');

		o = s.taboption('advanced', form.Value, 'login_path', _('登录接口路径'));
		o.default = '/drcom/login';

		o = s.taboption('advanced', form.Value, 'logout_path', _('注销接口路径'));
		o.default = '/drcom/logout';

		o = s.taboption('advanced', form.Value, 'check_interval', _('状态检查间隔（秒）'));
		o.datatype = 'uinteger';
		o.default = '15';

		o = s.taboption('advanced', form.Value, 'login_retry_interval', _('登录重试间隔（秒）'));
		o.datatype = 'uinteger';
		o.default = '60';

		o = s.taboption('advanced', form.Value, 'login_failure_limit', _('连续登录失败阈值（次）'));
		o.datatype = 'uinteger';
		o.default = '3';
		o.description = _('达到该次数后进入冷却等待，0 表示不启用。');

		o = s.taboption('advanced', form.Value, 'failure_cooldown', _('失败冷却时间（秒）'));
		o.datatype = 'uinteger';
		o.default = '300';

		o = s.taboption('advanced', form.Value, 'probe_url', _('外网探测地址'));
		o.placeholder = 'http://connectivitycheck.gstatic.com/generate_204';
		o.rmempty = true;

		o = s.taboption('advanced', form.Value, 'probe_expect_code', _('外网探测期望 HTTP 状态码'));
		o.datatype = 'uinteger';
		o.default = '204';

		o = s.taboption('advanced', form.Value, 'connect_timeout', _('连接超时（秒）'));
		o.datatype = 'uinteger';
		o.default = '5';

		o = s.taboption('advanced', form.Value, 'max_time', _('请求超时（秒）'));
		o.datatype = 'uinteger';
		o.default = '10';

		o = s.taboption('advanced', form.Value, 'mkkey', _('0MKKey'));
		o.default = '123456';

		o = s.taboption('advanced', form.Value, 'callback', _('回调函数名'));
		o.default = 'dr1003';

		o = s.taboption('advanced', form.Value, 'terminal_type', _('终端类型'));
		o.default = '1';

		o = s.taboption('advanced', form.Value, 'js_version', _('JS 版本'));
		o.default = '4.1.3';

		o = s.taboption('advanced', form.Value, 'v', _('版本随机值'));
		o.default = '7651';

		o = s.taboption('advanced', form.Value, 'para', _('para'));
		o.default = '00';

		o = s.taboption('advanced', form.DynamicList, 'remote_command', _('允许的远程关闭指令'));
		o.placeholder = 'stop-autologin';
		o.description = _('当路由器 WAN 口已开启 SSH 时，可在校园内网执行：ssh root@路由器WAN地址 "ruijie-campus-autologin-remote 指令"。');

		o = s.taboption('advanced', form.Button, '_autodetect', _('自动填充参数'));
		o.inputstyle = 'apply';
		o.inputtitle = _('自动填充参数');
		o.onclick = function() {
			return fs.exec_direct('/usr/bin/ruijie-campus-autologin-ctl', [ 'autodetect' ]).then(function(res) {
				var ret = parseJSON(res);
				ui.addNotification(null, E('p', ret.ok ? _('已自动填充登录/注销参数。') : (ret.message || _('自动检测失败。'))), ret.ok ? 'info' : 'warning');
				window.setTimeout(function() { location.reload(); }, 800);
			});
		};

		o = s.taboption('version', form.DummyValue, '_current_version', _('当前版本'));
		o.rawhtml = true;
		o.default = E('span', {}, versionData.current || '-');

		o = s.taboption('version', form.Flag, 'update_check_enabled', _('定期检查更新'));
		o.default = o.disabled;

		o = s.taboption('version', form.Value, 'update_check_interval', _('检查间隔（秒）'));
		o.datatype = 'uinteger';
		o.default = '86400';

		o = s.taboption('version', form.Flag, 'update_auto_install', _('发现新版本后自动安装'));
		o.default = o.disabled;

		o = s.taboption('version', form.ListValue, 'update_source', _('更新来源'));
		o.value('github', _('GitHub Release'));
		o.value('mirror', _('镜像网站'));
		o.default = 'github';

		o = s.taboption('version', form.Value, 'github_repo', _('GitHub 仓库'));
		o.default = 'LingRadiance/openwrt-ruijie-campus-autologin';

		o = s.taboption('version', form.Value, 'update_mirror_url', _('镜像地址'));
		o.placeholder = 'https://example.com/ruijie-campus-autologin';
		o.description = _('镜像模式下需要提供 latest.json，包含 tag 和 ipk_url 字段。');
		o.rmempty = true;

		o = s.taboption('version', form.Button, '_check_update', _('手动检查更新'));
		o.inputstyle = 'reload';
		o.inputtitle = _('检查更新');
		o.onclick = function() {
			return fs.exec_direct('/usr/bin/ruijie-campus-autologin-ctl', [ 'check-update' ]).then(function(res) {
				var ret = parseJSON(res);
				var msg = ret.ok ? _('当前版本：') + ret.current + _('，最新版本：') + ret.latest : (ret.message || _('检查更新失败。'));
				ui.addNotification(null, E('p', msg), ret.ok ? 'info' : 'warning');
			});
		};

		o = s.taboption('version', form.Button, '_install_update', _('手动安装更新'));
		o.inputstyle = 'apply';
		o.inputtitle = _('拉取并安装更新');
		o.onclick = function() {
			return fs.exec_direct('/usr/bin/ruijie-campus-autologin-ctl', [ 'install-update' ]).then(function(res) {
				var ret = parseJSON(res);
				ui.addNotification(null, E('p', ret.message || (ret.ok ? _('更新已安装。') : _('更新安装失败。'))), ret.ok ? 'info' : 'warning');
			});
		};

		statusWrap = E('div', {}, [
			statusNode,
			E('div', { 'class': 'cbi-section-actions' }, [
				E('button', {
					'class': 'btn cbi-button cbi-button-reload',
					'click': ui.createHandlerFn(this, function() {
						return this.refreshStatus(statusNode);
					})
				}, _('刷新状态')),
				' ',
				E('button', {
					'class': 'btn cbi-button cbi-button-negative',
					'click': ui.createHandlerFn(this, function() {
						return fs.exec_direct('/usr/bin/ruijie-campus-autologin-ctl', [ 'logout' ]).then(L.bind(function() {
							return this.refreshStatus(statusNode);
						}, this));
					})
				}, _('注销登录'))
				,
				' ',
				E('button', {
					'class': 'btn cbi-button cbi-button-action',
					'click': ui.createHandlerFn(this, function() {
						return fs.exec_direct('/usr/bin/ruijie-campus-autologin-ctl', [ 'events' ]).then(function(res) {
							ui.addNotification(_('最近事件'), E('pre', { 'style': 'white-space: pre-wrap' }, res || '[]'), 'info');
						});
					})
				}, _('查看最近事件')),
				' ',
				E('button', {
					'class': 'btn cbi-button cbi-button-action',
					'click': ui.createHandlerFn(this, function() {
						return fs.exec_direct('/usr/bin/ruijie-campus-autologin-ctl', [ 'diagnose' ]).then(function(res) {
							ui.addNotification(_('诊断结果'), E('pre', { 'style': 'white-space: pre-wrap' }, res || '{}'), 'info');
						});
					})
				}, _('运行诊断'))
			])
		]);

		poll.add(L.bind(function() {
			return this.refreshStatus(statusNode);
		}, this), 5);

		return m.render().then(function(mapNode) {
			return E('div', {}, [ statusWrap, mapNode ]);
		});
	},

	handleSaveApply: function(ev, mode) {
		return view.prototype.handleSaveApply.call(this, ev, mode).then(function() {
			return fs.exec_direct('/usr/bin/ruijie-campus-autologin-ctl', [ 'configure-cron' ]).catch(function() {});
		}).then(function() {
			return fs.exec_direct('/usr/bin/ruijie-campus-autologin-ctl', [ 'apply-settings' ]).catch(function() {});
		});
	}
});
