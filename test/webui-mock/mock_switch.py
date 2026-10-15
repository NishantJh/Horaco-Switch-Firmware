#!/usr/bin/env python3
"""Mock of the RTLPlayground HTTP API for SWTG018AS-A V2.0 (8x 2.5G + 1 SFP+).

Serves the web UI straight from an RTLPlayground checkout's html/ folder and
answers every JSON endpoint httpd/httpd.c routes, with the field shapes that
httpd/page_impl.c emits. POST /cmd applies the handful of CLI commands the UI
needs to look alive (port on/off/name, vlan, pvid, lag, mirror, stp, lldp);
anything else is accepted and ignored. No hardware, no auth checks.

  python3 mock_switch.py --html ../../../RTLPlayground/html [--port 8080]
"""
import argparse, http.server, json, os, random, re, time
from urllib.parse import urlparse, parse_qs

N = 9            # logical ports 0..8, port 8 = SFP+
SFP = 8
MIME = {".html": "text/html", ".js": "application/javascript",
        ".css": "text/css", ".svg": "image/svg+xml", ".ico": "image/x-icon"}

# link code = speed code + 1 (app.js LINKS): 3=1000M, 6=2.5G, 5=10G, 0=down
state = {
    "enabled": [True] * N,
    "link": [6, 6, 3, 0, 6, 2, 0, 0, 5],
    "names": ["nas", "desktop", "ap-office", "", "server", "printer", "", "", "uplink"],
    "vlans": {1: ("default", 0x1ff, 0x1ff), 10: ("lan", 0b100010011, 0b000010000),
              20: ("iot", 0b100100100, 0b000100100), 99: ("mgmt", 0x100, 0)},
    "pvid": [1] * N, "mgmt": 0,
    "lags": [0b000000011, 0, 0, 0], "lacp": [0b000000011, 0, 0, 0],
    "mirror": (0, 7, 0, 0), "stp": True, "lldp": True, "lldp_ports": 0x1ff,
    "mtu": [1522] * N,
}
state["pvid"][2] = 10; state["pvid"][5] = 20
counters = [[random.randint(10**6, 10**9), random.randint(10**6, 10**9)] for _ in range(N)]


def hexs(v, digits):
    return "%0*x" % (digits, v)


def bits16(mask):
    # page_impl.c prints 16 chars, bit 15 first
    return "".join("1" if mask & (1 << (15 - i)) else "0" for i in range(16))


last = [time.time()]


def status():
    out = []
    now = time.time()
    dt, last[0] = now - last[0], now
    for i in range(N):
        up = state["enabled"][i] and state["link"][i] > 0
        rate = {6: 9000, 3: 4000, 5: 30000, 2: 300}.get(state["link"][i], 0) if up else 0
        counters[i][0] += int(dt * rate * (0.6 + 0.4 * random.random()))
        counters[i][1] += int(dt * rate * (0.5 + 0.5 * random.random()))
        tx, rx = counters[i]
        p = {"portNum": i + 1, "logPort": i, "name": state["names"][i],
             "isSFP": 1 if i == SFP else 0, "enabled": 1 if state["enabled"][i] else 0}
        if i == SFP:
            p.update({"sfp_options": "0x5a", "sfp_temp": "0x2a80", "sfp_vcc": "0x8100",
                      "sfp_txbias": "0x1770", "sfp_txpower": "0x1f40", "sfp_rxpower": "0x1388",
                      "sfp_state": "0x00", "sfp_vendor": "FS", "sfp_model": "SFP-10GSR-85",
                      "sfp_serial": "F2210345678", "sfp_los": None})
        else:
            p["adv"] = "111111"
        p.update({"link": state["link"][i] if up else 0, "txG": "0x" + hexs(tx, 16),
                  "txB": "0x00000000", "rxG": "0x" + hexs(rx, 16),
                  "rxB": "0x%08x" % (3 if i == 5 else 0)})
        out.append(p)
    return out


def info():
    return {"ip_address": "192.168.1.2", "ip_gateway": "192.168.1.1", "ip_netmask": "255.255.255.0",
            "syslog_server": "0.0.0.0:514", "session_timeout": 600, "mac_address": "1c:2a:a3:12:34:56",
            "hostname": "rack-switch", "sw_ver": "v0.9-mock", "build_date": "2026-10-15",
            "hw_ver": "SWTG018AS_A_V_2_0", "chip_temp": "47.5", "flash_size": "2 MB",
            "sfp_slot_0": "FS              SFP-10GSR-85    "}


def vlan(vid):
    name, mem, unt = state["vlans"].get(vid, ("", 0, 0))
    pv = sum(1 << i for i in range(N) if state["pvid"][i] == vid)
    valid = 0x02 if vid in state["vlans"] else 0
    return {"members": "0x%08x" % ((valid << 24) | ((unt & 0x3ff) << 10) | (mem & 0x3ff)),
            "name": name, "pvid": "0x%04x" % pv}


def stp():
    ports = []
    for i in range(N):
        up = state["enabled"][i] and state["link"][i] > 0
        st = 3 if up else 1
        ports.append({"p": i + 1, "lag": 0, "mbr": 0, "st": st, "role": (1 if i == SFP else 2) if up else 0,
                      "f": 1, "pc": "00000000", "prio": 128, "p2": 0, "db": "80001c2aa3123456",
                      "dp": "80%02x" % (i + 1), "dc": "00000000"})
    return {"on": 1 if state["stp"] else 0, "rstp": 1, "prio": 8, "hello": 2, "maxage": 20, "fwd": 15,
            "txhold": 6, "rootPrio": "1000", "rootMac": "245a4c010203", "myMac": "1c2aa3123456",
            "cost": "00000fa0", "weRoot": 0, "rootPort": 9, "tc": "0004", "ports": ports}


def lacp():
    return {"on": 1, "lags": [{"cfg": "%04x" % state["lacp"][l], "aggValid": 1 if state["lacp"][l] else 0,
                               "agg": "245a4c0a0b0c" if state["lacp"][l] else "000000000000",
                               "members": "%04x" % state["lags"][l]} for l in range(4)],
            "ports": [{"p": i + 1, "lag": 0 if state["lacp"][0] >> i & 1 else 255,
                       "a": "3d" if state["lacp"][0] >> i & 1 else "00",
                       "pt": "3d" if state["lacp"][0] >> i & 1 else "00", "rs": 4 if state["lacp"][0] >> i & 1 else 0,
                       "rx": "01f4", "psys": "245a4c0a0b0c"} for i in range(N)]}


def l2(idx):
    entries = [(0x010, "00:11:32:aa:bb:01", 1, 0), (0x044, "3c:7c:3f:10:20:30", 1, 1),
               (0x090, "f4:92:bf:00:11:22", 10, 2), (0x120, "b8:27:eb:44:55:66", 20, 5),
               (0x200, "24:5a:4c:01:02:03", 1, 8), (0x350, "1c:2a:a3:12:34:56", 1, 9)]
    rows = [e for e in entries if e[0] >= idx][:5]
    return [{"idx": "%03x" % e[0], "mac": e[1], "vlan": "%03x" % e[2], "type": "l", "port": e[3],
             "lag": 1 if e[3] in (0, 1) else 0} for e in rows]


def per_port(fn):
    return [dict(portNum=i + 1, **fn(i)) for i in range(N)]


ROUTES = {
    "/status.json": status, "/information.json": info, "/stp.json": stp, "/lacp.json": lacp,
    "/vlanlist": lambda: {"mgmt": state["mgmt"], "vlan": [{"id": v, "name": state["vlans"][v][0]}
                                                         for v in sorted(state["vlans"])]},
    "/lag.json": lambda: [{"lagNum": l, "members": bits16(state["lags"][l]), "hash": "0000005f"} for l in range(4)],
    "/mirror.json": lambda: {"enabled": state["mirror"][0], "mPort": state["mirror"][1],
                             "mirror_rx": bits16(state["mirror"][2]), "mirror_tx": bits16(state["mirror"][3])},
    "/lldp.json": lambda: {"on": 1 if state["lldp"] else 0, "portStatus": [
        {"portNum": i + 1, "logPort": i, "name": state["names"][i], "permitted": 1 if state["lldp_ports"] >> i & 1 else 0}
        for i in range(N)]},
    "/eee.json": lambda: per_port(lambda i: {"isSFP": 1} if i == SFP else
                                  {"isSFP": 0, "eee": "011", "eee_lp": "011" if i < 3 else "000", "active": 1 if i < 3 else 0}),
    "/bandwidth.json": lambda: per_port(lambda i: {"iLimited": 0, "iBW": "000000", "iFC": 0, "eLimited": 0, "eBW": "000000"}),
    "/storm.json": lambda: per_port(lambda i: {"en": "1000" if i < 8 else "0000", "pps": "1111",
                                               "rate": "0003e8" + "000000" * 3}),
    "/isolation.json": lambda: per_port(lambda i: {"allow": "%04x" % 0x1ff}),
    "/mtu.json": lambda: per_port(lambda i: {"mtu": "0x%04x" % state["mtu"][i]}),
}


def ports_of(tokens):
    for tok in tokens:
        m = re.fullmatch(r"(\d+)(t?)", tok)
        if m:
            yield int(m.group(1)) - 1, bool(m.group(2))


def run_cmd(line):
    w = line.split()
    if not w:
        return
    if w[0] == "port" and len(w) >= 3:
        i = int(w[1]) - 1
        if w[2] in ("on", "off"):
            state["enabled"][i] = w[2] == "on"
        elif w[2] == "name" and len(w) > 3:
            state["names"][i] = w[3][:15]
    elif w[0] == "vlan" and len(w) >= 2:
        vid = int(w[1])
        if len(w) == 3 and w[2] == "d":
            state["vlans"].pop(vid, None)
        elif len(w) == 3 and w[2] == "mgmt":
            state["mgmt"] = vid
        else:
            rest = w[2:]
            name = rest.pop(0) if rest and not rest[0][0].isdigit() else ""
            mem = unt = 0
            for i, tagged in ports_of(rest):
                mem |= 1 << i
                if not tagged:
                    unt |= 1 << i
            state["vlans"][vid] = (name, mem, unt)
    elif w[0] == "pvid" and len(w) == 3:
        state["pvid"][int(w[1]) - 1] = int(w[2])
    elif w[0] == "lag" and len(w) >= 3:
        l = int(w[1]) - 1
        if w[2] == "d":
            state["lags"][l] = state["lacp"][l] = 0
        elif w[2] == "lacp":
            state["lacp"][l] = 0 if w[3:] == ["off"] else sum(1 << i for i, _ in ports_of(w[3:]))
            state["lags"][l] = state["lacp"][l]
        else:
            state["lags"][l] = sum(1 << i for i, _ in ports_of(w[2:]))
    elif w[0] == "mirror":
        if w[1:] == ["off"]:
            state["mirror"] = (0, 0, 0, 0)
        else:
            rx = tx = 0
            for tok in w[2:]:
                i = int(re.match(r"\d+", tok).group()) - 1
                if not tok.endswith("t"):
                    rx |= 1 << i
                if not tok.endswith("r"):
                    tx |= 1 << i
            state["mirror"] = (1, int(w[1]) - 1, rx, tx)
    elif w[0] == "stp" and w[1:] in (["on"], ["off"]):
        state["stp"] = w[1] == "on"
    elif w[0] == "lldp" and w[1:] in (["on"], ["off"]):
        state["lldp"] = w[1] == "on"
    elif w[0] == "mtu" and len(w) == 3:
        state["mtu"][int(w[1]) - 1] = int(w[2])
    elif w[0] == "hostname" and len(w) == 2:
        pass


class Handler(http.server.BaseHTTPRequestHandler):
    html = "."

    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json", extra=()):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=UTF-8")
        self.send_header("Cache-Control", "no-store")
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        path = "/index.html" if u.path == "/" else u.path
        if path in ROUTES:
            return self.send(200, json.dumps(ROUTES[path]()))
        if path == "/vlan.json":
            return self.send(200, json.dumps(vlan(int(parse_qs(u.query).get("vid", ["1"])[0]))))
        if path == "/l2.json":
            return self.send(200, json.dumps(l2(int(parse_qs(u.query).get("idx", ["0"])[0]))))
        if path == "/counters.json":
            return self.send(200, json.dumps(["0x%016x" % random.randint(0, 10**7) for _ in range(0x37)]))
        if path in ("/config", "/cmd_log"):
            return self.send(200, "hostname rack-switch\nvlan 10 lan 1 2 5 9t\n", "text/plain")
        if path == "/cmd_log_clear":
            return self.send(200, "[]")
        f = os.path.join(self.html, os.path.basename(path))
        if os.path.isfile(f):
            with open(f, "rb") as fh:
                return self.send(200, fh.read(), MIME.get(os.path.splitext(f)[1], "application/octet-stream"))
        self.send(404, "not found", "text/plain")

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode(errors="replace")
        path = urlparse(self.path).path
        if path == "/login":
            return self.send(302, "", "text/html", [("Set-Cookie", "session=1234567890ab"), ("Location", "/index.html")])
        if path == "/cmd":
            for line in body.splitlines():
                run_cmd(line.strip())
            return self.send(200, "", "text/plain")
        self.send(200, "<h1>Upload OK</h1>", "text/html")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True, help="RTLPlayground html/ folder")
    ap.add_argument("--port", type=int, default=8080)
    a = ap.parse_args()
    Handler.html = os.path.abspath(a.html)
    print("mock switch on http://127.0.0.1:%d serving %s" % (a.port, Handler.html))
    http.server.ThreadingHTTPServer(("127.0.0.1", a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
