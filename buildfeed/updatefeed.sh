#!/usr/bin/env bash
set -e
### First argument is the main feed; second is the file containing the new item
### If second is omitted, create an empty new feed

usage() {
	cat <<EOF
$0 feed
    will create a new, empty, feed file
$0 feed itemfile
    will add the item contained in itemfile to the feed
EOF
}

feed_new() {
	feed="$1"
	if [ -f "$feed" ]; then
		echo "File $feed already exists" >&2
		return 1
	fi
	cat <<EOF > "$feed"
<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
	<channel>
		<title>Freepto buildlog</title>
		<description>All build events are here</description>
		<link>https://github.com/AvANa-BBS/freepto-lb</link>
		<!-- this MUST be the last line --></channel></rss>
EOF
}

feed_append() {
	feed="$1"
	item="$2"
	if ! [ -w "$feed" ]; then
		echo "File $feed does not exist or has invalid permissions" >&2
		return 1
	fi
	temp=$(mktemp)
	(head -n -1 "$feed"; cat "$item"; tail -n1 "$feed") > "$temp"
	mv "$temp" "$feed"
}

item_new() {
	buildimg="$1"
	description="$buildimg"
	d=$(date -R)
	cat <<EOF
	<item>
	<title>New build</title>
	<description>${description}</description>
	<link>https://github.com/AvANa-BBS/freepto-lb</link>
	<pubDate>${d}</pubDate>
	</item>
EOF
}

if [ "$1" = "-item" ]; then
	item_new "$2"
	exit $?
fi
if [ $# -eq 2 ]; then
	feed_append "$1" "$2"
	exit $?
fi
if [ $# -eq 1 ]; then
	feed_new "$1"
	exit $?
fi
usage
exit 63
