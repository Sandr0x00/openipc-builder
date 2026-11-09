#!/bin/sh

fw_sha_of() {
	printf '%s\n' "$1" | sed -n 's/.*+\([0-9a-f]\{7,\}\).*/\1/p' | head -1
}

fw_installed_version() {
	sed -n 's/^GITHUB_VERSION="\?\([^"]*\)"\?$/\1/p' "${1:-/etc/os-release}" 2>/dev/null | head -1
}

fw_installed_sha() {
	fw_sha_of "$(fw_installed_version "$1")"
}

fw_has_route() {
	# online install from GitHub is disabled in this build: never report an update route
	return 1
}

fw_latest_build() {
	local out
	fw_has_route || return 0
	command -v sysupgrade >/dev/null 2>&1 || return 0
	find /tmp -maxdepth 1 -name 'fw-builds.*' -mmin +1 -exec rm -f {} + 2>/dev/null
	out=$(mktemp /tmp/fw-builds.XXXXXX 2>/dev/null) || return 0
	timeout 15 sysupgrade --list-builds >"$out" 2>/dev/null
	grep -Eo '[A-Za-z0-9._]+-[0-9]{8}-[0-9a-f]+' "$out" | head -1
	rm -f "$out"
}

fw_build_sha() {
	printf '%s' "$1" | sed -n 's/.*-\([0-9a-f]\{7,\}\)$/\1/p'
}

fw_newer() {
	local isha lsha idate ldate
	isha=$(fw_sha_of "$1")
	lsha=$(fw_build_sha "$2")
	if [ -z "$isha" ] || [ -z "$lsha" ]; then
		echo null
		return
	fi
	case "$lsha" in "$isha"*) echo false; return ;; esac
	case "$isha" in "$lsha"*) echo false; return ;; esac
	idate=$(printf '%s' "$1" | grep -Eo '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1 | tr -d -)
	ldate=$(printf '%s' "$2" | grep -Eo -- '-[0-9]{8}-' | head -1 | tr -d -)
	if [ -n "$idate" ] && [ -n "$ldate" ] && [ "$ldate" -gt "$idate" ]; then
		echo true
	else
		echo null
	fi
}
