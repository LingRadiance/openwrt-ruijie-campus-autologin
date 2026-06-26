'use strict';
'require view';
'require form';
'require uci';
'require fs';
'require poll';
'require ui';

function renderStatus(data) {
	var stateMap = {
		online: '已登录',
		offline: '未登录',
		error: '错误',
		disabled: '服务未启用',
		waiting_config: '等待配置',
		logged_out: '已发送注销',
		unknown: '未知'
	};

	var state = stateMap[data.state] || data.state || '未知';
	var running = data.running ? '运行中' : '未运行';
	var account = data.account || '-';
	var updated = data.updated || '-';
	var message = data.message || '-';

	return E('div', { 'class': 'cbi-section' }, [
		E('h3', {}, _('登录状态')),
		E('div', { 'class': 'table' }, [
			E('div', { 'class': 'tr' }, [
				E('div', { 'class': 'td left', 'style': 'width: 25%' }, _('服务状态')),
				E('div', { 'class': 'td left' }, running)
			]),
			E('div', { 'class': 'tr' }, [
				E('div', { 'class': 'td left' }, _('登录状态')),
				E('div', { 'class': 'td left' }, state)
			]),
			E('div', { 'class': 'tr' }, [
				E('div', { 'class': 'td left' }, _('当前账号')),
				E('div', { 'class': 'td left' }, account)
			]),
			E('div', { 'class': 'tr' }, [
				E('div', { 'class': 'td left' }, _('更新时间')),
				E('div', { 'class': 'td left' }, updated)
			]),
			E('div', { 'class': 'tr' }, [
				E('div', { 'class': 'td left' }, _('状态信息')),
				E('div', { 'class': 'td left' }, message)
			])
		])
	]);
}

return view.extend({
	load: function() {
		return Promise.all([
			uci.load('ruijie-campus-autologin'),
			fs.exec_direct('/usr/bin/ruijie-campus-autologin-ctl', [ 'status' ]).catch(function() { return '{}'; })
		]);
	},

	refreshStatus: function(node) {
		return fs.exec_direct('/usr/bin/ruijie-campus-autologin-ctl', [ 'status' ]).then(function(res) {
			var data = {};
			try { data = JSON.parse(res || '{}'); } catch (e) {}
			node.innerHTML = '';
			node.appendChild(renderStatus(data));
		});
	},

	render: function(data) {
		var m, s, o, statusData, statusNode, statusWrap, actions;

		try { statusData = JSON.parse(data[1] || '{}'); } catch (e) { statusData = {}; }

		statusNode = E('div', {}, renderStatus(statusData));

		m = new form.Map('ruijie-campus-autologin', _('锐捷校园网自动登录'));

		s = m.section(form.NamedSection, 'main', 'login', _('基础设置'));
		s.anonymous = true;

		o = s.option(form.Flag, 'enabled', _('启用服务'));
		o.default = o.disabled;

		o = s.option(form.Value, 'portal_url', _('认证服务器地址'));
		o.default = 'http://192.168.16.3/';
		o.placeholder = 'http://192.168.16.3/';

		o = s.option(form.Value, 'login_path', _('登录接口路径'));
		o.default = '/drcom/login';
		o.placeholder = '/drcom/login';

		o = s.option(form.Value, 'logout_path', _('注销接口路径'));
		o.default = '/drcom/logout';
		o.placeholder = '/drcom/logout';

		o = s.option(form.Value, 'username', _('账号'));
		o.rmempty = false;

		o = s.option(form.Value, 'password', _('密码'));
		o.password = true;
		o.rmempty = false;

		o = s.option(form.ListValue, 'operator', _('运营商'));
		o.value('cmcc', _('中国移动 (@cmcc)'));
		o.value('unicom', _('中国联通 (@unicom)'));
		o.value('telecom', _('中国电信 (@dx)'));
		o.value('none', _('不追加后缀'));
		o.value('campus', _('校园用户'));
		o.value('teacher', _('教师登录'));
		o.value('continuing', _('继续教育学院'));
		o.default = 'cmcc';

		o = s.option(form.Value, 'check_interval', _('状态检查间隔（秒）'));
		o.datatype = 'uinteger';
		o.default = '15';
		o.description = _('每隔多少秒检查一次当前登录状态。');

		o = s.option(form.Value, 'login_retry_interval', _('登录重试间隔（秒）'));
		o.datatype = 'uinteger';
		o.default = '60';
		o.description = _('登录失败或离线后，至少等待多少秒再发起下一次登录。');

		o = s.option(form.Value, 'probe_url', _('外网探测地址'));
		o.placeholder = 'http://connectivitycheck.gstatic.com/generate_204';
		o.rmempty = true;

		o = s.option(form.Value, 'probe_expect_code', _('外网探测期望 HTTP 状态码'));
		o.datatype = 'uinteger';
		o.default = '204';

		o = s.option(form.Value, 'connect_timeout', _('连接超时'));
		o.datatype = 'uinteger';
		o.default = '5';

		o = s.option(form.Value, 'max_time', _('请求超时'));
		o.datatype = 'uinteger';
		o.default = '10';

		o = s.option(form.Value, 'mkkey', _('0MKKey'));
		o.default = '123456';

		o = s.option(form.Value, 'callback', _('回调函数名'));
		o.default = 'dr1003';

		o = s.option(form.Value, 'terminal_type', _('终端类型'));
		o.default = '1';

		o = s.option(form.Value, 'js_version', _('JS 版本'));
		o.default = '4.1.3';

		o = s.option(form.Value, 'v', _('版本随机值'));
		o.default = '7651';

		o = s.option(form.Value, 'para', _('para'));
		o.default = '00';

		s = m.section(form.NamedSection, 'main', 'login', _('远程关闭'));
		s.anonymous = true;

		o = s.option(form.DynamicList, 'remote_command', _('允许的远程关闭指令'));
		o.placeholder = 'stop-autologin';
		o.description = _('当路由器 WAN 口已开启 SSH 时，可在校园内网执行：ssh root@路由器WAN地址 "ruijie-campus-autologin-remote 指令"。命中此列表中的任意指令后，服务会被停止并禁用。');

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
					'class': 'btn cbi-button cbi-button-apply',
					'click': ui.createHandlerFn(this, function() {
						return fs.exec_direct('/usr/bin/ruijie-campus-autologin-ctl', [ 'autodetect' ]).then(function(res) {
							var data = {};
							try { data = JSON.parse(res || '{}'); } catch (e) {}

							if (data.ok)
								ui.addNotification(null, E('p', _('已自动填充登录/注销参数。')), 'info');
							else
								ui.addNotification(null, E('p', data.message || _('自动检测失败。')), 'warning');

							window.setTimeout(function() { location.reload(); }, 800);
						});
					})
				}, _('自动填充参数')),
				' ',
				E('button', {
					'class': 'btn cbi-button cbi-button-negative',
					'click': ui.createHandlerFn(this, function() {
						return fs.exec_direct('/usr/bin/ruijie-campus-autologin-ctl', [ 'logout' ]).then(L.bind(function() {
							return this.refreshStatus(statusNode);
						}, this));
					})
				}, _('注销登录'))
			])
		]);

		poll.add(L.bind(function() {
			return this.refreshStatus(statusNode);
		}, this), 5);

		return m.render().then(function(mapNode) {
			return E('div', {}, [ statusWrap, mapNode ]);
		});
	}
});
