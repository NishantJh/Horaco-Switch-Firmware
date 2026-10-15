# Web UI mock

Runs the RTLPlayground web UI in a browser without a switch, to develop and
screenshot UI changes. `mock_switch.py` serves `html/` from an RTLPlayground
checkout and fakes every JSON endpoint `httpd/httpd.c` routes, shaped like
`httpd/page_impl.c` output, for an SWTG018AS-A V2.0 (ports 1-8 2.5G, port 9
SFP+). `POST /cmd` applies the port/vlan/pvid/lag/mirror/stp/lldp commands so
edits show up; other commands are accepted and ignored.

```
python3 mock_switch.py --html ../../../RTLPlayground/html      # http://127.0.0.1:8080
node shoot.js http://127.0.0.1:8080 out/                        # screenshots (needs playwright)
```

Not a firmware test: it checks layout and the commands the UI sends, nothing
about what the chip does with them. Screenshots of the current UI are in
[docs/webui](../../docs/webui).
