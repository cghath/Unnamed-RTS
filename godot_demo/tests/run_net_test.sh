#!/bin/sh
# Starts a host and a client on this machine and lets them play for ~20 s.
#   GODOT=/path/to/godot sh tests/run_net_test.sh
GODOT=${GODOT:-godot}
cd "$(dirname "$0")/.."
$GODOT --headless --path . -- --host > /tmp/net_host.log 2>&1 &
sleep 2
$GODOT --headless --path . -- --join 127.0.0.1 > /tmp/net_client.log 2>&1
sleep 4
grep "^NET" /tmp/net_host.log /tmp/net_client.log
