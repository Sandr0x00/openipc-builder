#!/usr/bin/haserl
<%in p/common.cgi %>
<%

	. ./p/firmware.sh

	au_job=/usr/sbin/fw-autoupdate
	au_tab=/etc/crontabs/root
	au_line=$(grep -v '^[[:space:]]*#' "$au_tab" 2>/dev/null | grep " $au_job\$" | head -1)
	au_min=""; au_hour=""; au_day=""; au_foreign=""
	if [ -n "$au_line" ]; then
		au_min=$(echo "$au_line" | awk '{print $1}')
		au_hour=$(echo "$au_line" | awk '{print $2}')
		au_day=$(echo "$au_line" | awk '{print $5}')
		case "$au_min" in [0-9] | [1-5][0-9]) ;; *) au_foreign=1 ;; esac
		case "$au_hour" in [0-9] | 1[0-9] | 2[0-3]) ;; *) au_foreign=1 ;; esac
		case "$au_day" in '*' | [0-6]) ;; *) au_foreign=1 ;; esac
		[ "$(echo "$au_line" | awk '{print $3 $4}')" = '**' ] || au_foreign=1
	fi


	say_date() {
		local y=${1%%-*} rest=${1#*-} m d
		m=${rest%%-*}; d=${rest#*-}
		d=${d#0}
		case "$m" in
			01) m=January ;;   02) m=February ;; 03) m=March ;;     04) m=April ;;
			05) m=May ;;       06) m=June ;;     07) m=July ;;      08) m=August ;;
			09) m=September ;; 10) m=October ;;  11) m=November ;;  12) m=December ;;
			*) printf '%s' "$1"; return ;;
		esac
		printf '%s %s %s' "$d" "$m" "$y"
	}

	fw_active=""
	[ -f /tmp/majestic-upgrade-owner ] && fw_active=1

	fw_part=""
	[ "$GET_part" = "offer" ] && fw_part=offer
	fw_checking=""
	if [ -n "$fw_active" ]; then
		ver=""
	elif [ -z "$fw_part" ] && fw_has_route; then
		ver=""; fw_checking=1
	else
		ver=$(fw_latest_build)
	fi
	if [ -n "$ver" ]; then
		fw_date=$(echo "$ver" | grep -Eo '[0-9]{8}' | head -1 | sed -E 's/(....)(..)(..)/\1-\2-\3/')
		[ -z "$fw_date" ] && fw_date="$ver"
	else
		fw_date=""
	fi

	inst_sha=$(fw_sha_of "$fw_build")
	inst_date=$(echo "$fw_build" | grep -Eo '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1)
	latest_sha=$(fw_build_sha "$ver")
	fw_why=""
	fw_cmp=""
	fw_sev=""
	if [ -n "$fw_checking" ]; then
		fw_state="checking"
		fw_sev="info"
	elif [ -z "$ver" ]; then
		fw_state="offline"
		fw_sev="info"
		if [ -z "$network_gateway" ]; then fw_why="noroute"; else fw_why="nocheck"; fi
	else
		fw_cmp=$(fw_newer "$fw_build" "$ver")
		if [ "$fw_cmp" = false ]; then
			fw_state="current"; fw_cmp=""
			fw_sev="ok"
		elif [ "$fw_cmp" = true ]; then
			fw_state="available"; fw_cmp="newer"
			fw_sev="warn"
		else
			fw_state="available"; fw_cmp="unknown"
			fw_sev="info"
			if [ -n "$inst_sha" ] && [ -n "$latest_sha" ]; then fw_why="notlater"; else fw_why="noid"; fi
		fi
	fi

	au_rec=/etc/webui/fw-autoupdate.last
	au_get() { sed -n "s/^$1=\"\(.*\)\"\$/\1/p" "$au_rec" 2>/dev/null | head -1; }
	au_result=$(au_get au_result)
	au_when=$(au_get au_when)
	au_target=$(au_get au_target)
	au_code=$(au_get au_code)
	au_took=""
	if [ "$au_result" = "started" ]; then
		au_took=$(fw_newer "$fw_build" "$au_target")
	fi

	au_dayname() {
		case "$1" in
			'*') printf 'Every day' ;;
			0) printf 'Every Sunday' ;;    1) printf 'Every Monday' ;;
			2) printf 'Every Tuesday' ;;   3) printf 'Every Wednesday' ;;
			4) printf 'Every Thursday' ;;  5) printf 'Every Friday' ;;
			6) printf 'Every Saturday' ;;
		esac
	}

	hide_title=1

	fw_kernel="true"
	fw_rootfs="true"
%>
<% fw_head() { %>
	<div id="fw-head" data-fw-part="head" data-fw-state="<% attr_escape "$fw_state" %>" data-fw-latest="" hidden></div>
	<div id="fw-counts" hidden></div>
<% } %>
<% fw_wide() { %>
		<% if [ "$fw_state" = "offline" ]; then %>
			<div class="col-12 col-lg-7 mj-fw-wide" data-fw-part="wide">
				<div class="card h-100"><div class="card-body d-flex flex-column">
					<% card_head "Install from a file" "the only route from here" %>
					<p class="hint text-secondary">On a machine that does have internet, download the image for
						<code><% esc "$soc" %></code> on <% esc "$(echo "$flash_type" | tr 'a-z' 'A-Z')" %> flash, then upload it here.
						The camera checks the image before it writes anything.</p>
					<p class="string mj-row mt-3">
						<label for="fw-file" class="form-label">Image</label>
						<span class="mj-ctl"><span class="mj-ctl-in">
							<input id="fw-file" type="file" accept=".tgz,.gz" class="form-control">
						</span></span>
					</p>
					<div class="mj-foot mt-auto">
						<span class="mj-foot-note">Writes the kernel and the rootfs. Video stops and the camera reboots &mdash; do not power it off.</span>
						<button id="fw-install-upload" type="button" class="btn btn-primary">Upload &amp; install</button>
					</div>
				</div></div>
			</div>
		<% else %>
			<div id="fw-news" class="col-12 col-lg-7 mj-fw-wide" data-fw-part="wide" hidden>
				<div class="card"><div class="card-body">
					<% card_head "What&rsquo;s new" "since your build" %>
					<div id="fw-news-body"></div>
				</div></div>
			</div>
		<% fi %>
<% } %>
<% fw_ifback() { %>
				<% if [ "$fw_state" = "available" ]; then %>
					<div class="col-12" data-fw-part="ifback">
						<div class="card h-100"><div class="card-body">
							<% card_head "If it does not come back" %>
							<p class="hint text-secondary">The camera stops answering while it writes and returns in about
								two minutes. If it has not returned after five, power it off and on
								once, then reload this page.</p>
						</div></div>
					</div>
				<% else %>
					<div class="col-12" data-fw-part="ifback" hidden></div>
				<% fi %>
<% } %>
<% fw_railfile() { %>
				<% if [ "$fw_state" != "offline" ]; then %>
					<div class="col-12" data-fw-part="railfile">
						<div class="card h-100"><div class="card-body">
							<% card_head "Install from a file" %>
							<p class="hint text-secondary mb-3">Have a <code>.tgz</code> image on your computer? Use it instead of downloading.</p>
							<p class="string mj-row mb-0">
								<label for="fw-file" class="form-label">Image</label>
								<span class="mj-ctl"><span class="mj-ctl-in">
									<input id="fw-file" type="file" accept=".tgz,.gz" class="form-control form-control-sm">
								</span></span>
							</p>
							<div class="mj-foot mt-3">
								<span class="mj-foot-note">Same reboot, same caution.</span>
								<button id="fw-install-upload" type="button" class="btn btn-sm btn-primary">Install this file</button>
							</div>
						</div></div>
					</div>
				<% else %>
					<div class="col-12" data-fw-part="railfile" hidden></div>
				<% fi %>
<% } %>
<%
	if [ -n "$fw_part" ]; then
		printf 'Content-type: text/html; charset=UTF-8\nCache-Control: no-store\n\n'
		if [ -n "$fw_active" ]; then
			printf '<div data-fw-active></div>\n'
		else
			fw_head; fw_wide; fw_ifback; fw_railfile
		fi
		exit 0
	fi
%>
<%in p/header.cgi %>

<h2 class="mj-rail-title mj-page-title"><%= $page_title %></h2>

<div id="fw-status" role="status" aria-live="polite"></div>

<div id="fw-inflight" hidden data-active="<% attr_escape "$fw_active" %>"></div>

<div id="fw-controls">

	<% fw_head %>

	<div class="row g-4 mt-0 mj-fw-cols">

		<% fw_wide %>

		<div class="col-12 col-lg-5 mj-fw-rail">
			<div class="row g-4">

				<div class="col-12">
					<div class="card h-100"><div class="card-body">
						<% card_head "This camera" %>
						<dl class="small list mb-0">
							<dt>Installed</dt><dd id="fw-installed"><% esc "${fw_version}-${fw_variant}" %></dd>
							<% if [ -n "$inst_date" ]; then %>
								<dt>Built</dt><dd><% esc "$inst_date" %></dd>
							<% fi %>
							<dt>SoC</dt><dd><% esc "$soc" %> <span class="text-secondary">(<% esc "$soc_family" %>)</span></dd>
							<dt>Sensor</dt><dd><% esc "$sensor" %></dd>
							<dt>Flash</dt><dd><% esc "$flash_type" %></dd>
						</dl>
					</div></div>
				</div>

				<div class="col-12">
					<div class="card h-100"><div class="card-body">
						<% card_head "What gets written" %>
						<p class="hint text-secondary mb-3">Both are written unless you turn one off.</p>
						<% field_switch "fw_kernel" "Upgrade kernel" "true" %>
						<% field_switch "fw_rootfs" "Upgrade rootfs" "true" %>
						<details class="mt-2">
							<summary class="text-secondary small">Advanced options</summary>
							<div class="mt-2">
								<% field_switch "fw_reset" "Reset config (wipe overlay)" "false" "Erases every setting on this camera; it comes back as a fresh flash. <span class='text-danger'>Destroys all changes, and cannot be undone.</span>" "Wipe ALL settings during this upgrade?&#10;&#10;Every configuration change on this camera is erased: network and Wi-Fi, video and image settings, timezone, passwords, and every extension you have configured.&#10;&#10;It comes back as if freshly flashed. This cannot be undone.&#10;&#10;Leave this off unless you specifically want a factory reset." %>
								<% field_switch "fw_force" "Reflash even if the same version" "false" "Re-writes flash even when installed and target versions match." %>
							</div>
						</details>
					</div></div>
				</div>


				<% fw_ifback %>

				<% fw_railfile %>

			</div>
		</div>
	</div>
</div>

<div id="fw-progress" class="mt-4" style="display:none">
	<div class="card mj-hero-card mj-sev-progress">
		<div class="card-body">
			<div class="mj-hero">
				<svg class="mj-hero-ico" viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6" rx="1"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3"/></svg>
				<div class="mj-hero-txt">
					<p class="mj-hero-kick">Installing</p>
					<h3 class="mj-hero-hl" id="fw-progress-hl">Writing firmware</h3>
					<div id="fw-meter" class="mj-meter" hidden>
						<div class="mj-meter-head">
							<span id="fw-meter-what"></span>
							<span id="fw-meter-pct" class="mj-mono"></span>
						</div>
						<div id="fw-bar" class="progress" role="progressbar"
						     aria-valuemin="0" aria-valuemax="100"><div class="progress-bar"></div></div>
					</div>
					<ol id="fw-steps" class="mj-steps">
						<li data-step="download">Downloading</li>
						<li data-step="verify">Checking image</li>
						<li data-step="kernel">Update kernel</li>
						<li data-step="rootfs">Update rootfs</li>
						<li data-step="overlay">Erasing settings</li>
						<li data-step="reboot">Rebooting</li>
					</ol>
				</div>
			</div>
		</div>
		<div class="mj-foot mj-foot-loud">
			<svg class="mj-foot-ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 9v5m0 3.5h.01M10.3 3.9 1.9 18.3A2 2 0 0 0 3.6 21.3h16.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/></svg>
			<span class="mj-foot-note">Do not power the camera off, and do not close this page.</span>
		</div>
	</div>

	<div class="card mt-4"><div class="card-body">
		<% card_head "Progress" "sysupgrade" %>
		<pre id="fw-output" class="border rounded p-2 bg-body-tertiary mb-0" style="height:50vh;overflow:auto;white-space:pre-wrap;font-size:12px"></pre>
	</div></div>
</div>

<script src="/a/update.js"></script>
<%in p/footer.cgi %>
