#!/bin/bash

cleanup() {
    tmux kill-session -t "$1" > /dev/null 2>&1
    sudo pkill -9 -f varnishd > /dev/null 2>&1
    sudo pkill -9 -f vha-agent > /dev/null 2>&1
    if [ ! -z "$2" ]; then
        sudo rm -rf "$2"
    fi
}

# Initializations.
SESSION="services"
TMP=`mktemp -d`
trap "cleanup '$SESSION' '$TMP'" EXIT
chmod a+rx "$TMP"

# Clean up previous session & start a new one.
cleanup "$SESSION"
cd "$TMP"
tmux new-session -d -s "$SESSION" -n "Terminal"
tmux set -g remain-on-exit on > /dev/null 2>&1
tmux set -g mode-mouse on > /dev/null 2>&1
tmux set -g mouse-resize-pane on > /dev/null 2>&1
tmux set -g mouse-select-pane on > /dev/null 2>&1
tmux set -g mouse-select-window on > /dev/null 2>&1

# Create VHA nodes file.
cat > "$TMP/nodes.conf" <<EOF
varnish1 = http://127.0.0.1:8001
varnish2 = http://127.0.0.1:8002
varnish3 = http://127.0.0.1:8003
EOF

# Create Varnish Cache VCL file.
cat > "$TMP/default.vcl" <<EOF
vcl 4.0;

backend default {
    .host = "127.0.0.1";
    .port = "8080";
}

sub vcl_recv {
    call vha_backend_selection;
}

sub vcl_backend_response {
    call vha_clean_headers;
}

EOF
vha-agent -N "$TMP/nodes.conf" -g >> "$TMP/default.vcl"

# Start Varnish Cache instances.
for i in {1..3}; do
    tmux new-window -t "$SESSION:$i" -n "VCP-$i" -c "$TMP"
    tmux send-keys "clear; \
        sudo varnishd \
            -F \
            -a 0.0.0.0:800$i \
            -s malloc,64m \
            -f '$TMP/default.vcl' \
            -i varnish$i \
            -p vsl_reclen=1024 \
            -n '/var/lib/varnish/varnish$i'" C-m
    tmux split-window -t "$SESSION:$i" -v -p 66
    tmux send-keys "clear; sudo varnishlog -n varnish$i" C-m
done

# Start VHA instances.
for i in {1..3}; do
    tmux new-window -t "$SESSION:$((i+3))" -n "VHA-$i" -c "$TMP"
    tmux send-keys "clear; sleep 1; \
        sudo vha-agent \
            -N '$TMP/nodes.conf' \
            -m varnish$i \
            -n /var/lib/varnish/varnish$i \
            -p stat_intvl=5 \
            -s '$TMP/vha$i-status'" C-m
    tmux split-window -t "$SESSION:$((i+3))" -v -p 66
    tmux send-keys "clear; sudo watch -n 5 cat '$TMP/vha$i-status'" C-m
done

# Start HTTP backend server.
tmux new-window -t "$SESSION:7" -n "Backend" -c "$TMP"
tmux send-keys "clear; \
python <<EOF
import BaseHTTPServer

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Cache-Control', 's-maxage=300')
        self.end_headers()
        self.wfile.write('http://' + self.headers['Host'] + self.path + '\n')

BaseHTTPServer.HTTPServer(('localhost', 8080), Handler).serve_forever()
EOF" C-m

# Start Zabbix Sender loop.
tmux new-window -t "$SESSION:8" -n "Zabbix" -c "$TMP"
tmux send-keys "clear; sleep 5; \
    while true; do
        clear
        sudo /vagrant/zabbix-vha-agent.py -i "$TMP/vha1-status, $TMP/vha2-status, $TMP/vha3-status" send -c /etc/zabbix/zabbix_agentd.conf -s dev
        sleep 60
    done" C-m

# Select first window & attach to the session.
tmux select-window -t "$SESSION:0"
tmux send-keys 'curl -H "Host: www.example.com" http://127.0.0.1:8001/foo.html -v' C-m
tmux -2 attach-session -t "$SESSION" -d
