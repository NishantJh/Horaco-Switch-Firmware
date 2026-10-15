/* Host-side RSTP test: compiles the real rtl837x_stp.c against shims, fakes the MSTP-state and link
 * registers, feeds crafted BPDUs and a 50 Hz clock. "GAP" = desired 802.1w behaviour that is missing. */
#include <stdio.h>
#include <stdlib.h>
#include "rtl837x_common.h"
#include "rtl837x_regs.h"
#include "rtl837x_stp.h"

uint8_t uip_buf[UIP_CONF_BUFFER_SIZE + 2];
uint16_t uip_len;
struct uip_eth_addr uip_ethaddr = {{0x02,0x11,0x22,0x33,0x44,0x55}};
struct machine machine = {0, 8, {1,2,3,4,5,6,7,8,9}};
struct machine_runtime machine_detected = {1, 0};
volatile uint32_t ticks;
uint8_t sfr_data[4];
uint8_t cmd_buffer[CMD_BUF_SIZE];
uint8_t cmd_words_len;
uint8_t cmd_words_b[15];
char save_cmd;
uint8_t atoi_results_u8;
uint8_t stp_enabled, err_status;
void print_long(uint32_t v) { (void)v; }
void itoa(uint8_t v) { (void)v; }
int vlan_get(uint16_t v) { (void)v; return 0; }
void port_l2mc_set(uint8_t a, uint16_t v, uint16_t m) { (void)a; (void)v; (void)m; }
uint16_t port_pvid_get(uint8_t p) { (void)p; return 1; }

static uint8_t mstp[4];
static uint16_t link_mask;

void reg_read_m(uint16_t r)
{
	if (r == RTL837X_MSTP_STATES) memcpy(sfr_data, mstp, 4);
	else if (r == RTL837X_REG_LINKS_STS) { sfr_data[0] = 0; sfr_data[1] = link_mask & 0xff; sfr_data[2] = link_mask >> 8; sfr_data[3] = 0; }
}
void reg_write_m(uint16_t r) { if (r == RTL837X_MSTP_STATES) memcpy(mstp, sfr_data, 4); }
void print_reg(uint16_t r) { (void)r; }
void print_string(const char *s) { (void)s; }
void print_byte(uint8_t b) { (void)b; }
void print_short(uint16_t s) { (void)s; }
void write_char(char c) { (void)c; }
void trap_rma_set(uint16_t reg, uint8_t act) { (void)reg; (void)act; }
void port_l2_forget_port(uint8_t p) { (void)p; }
uint16_t port_lag_members_get(uint8_t lag) { (void)lag; return 0; }
uint8_t cmd_compare(uint8_t s, const uint8_t *c) { (void)s; (void)c; return 0; }
uint8_t atoi_byte(uint8_t i) { (void)i; return 0; }
uint8_t cmd_parse_port_separator(uint8_t i) { (void)i; return 0; }

/* TX log: one entry per BPDU sent */
struct txe { int port; uint8_t version, type, flags; long t; };
static struct txe txlog[512];
static int ntx;
static long now;	/* in 50 Hz ticks */
void tcpip_output(void)
{
	uint16_t pm = (uint16_t)((uip_buf[12 + 18] << 8) | uip_buf[12 + 19]);
	int port;
	for (port = 0; port < 10 && pm != PORT_BIT(port); port++) ;
	if (ntx < 512) txlog[ntx++] = (struct txe){port, uip_buf[12 + 27], uip_buf[12 + 28], uip_buf[12 + 29], now};
}
static int tx_since(int port, long t0, uint8_t flag_mask, int type)
{
	for (int i = 0; i < ntx; i++)
		if (txlog[i].port == port && txlog[i].t >= t0 && (type < 0 || txlog[i].type == type)
		    && (txlog[i].flags & flag_mask) == flag_mask)
			return 1;
	return 0;
}

static int fails, gaps;
#define CHECK(c, msg) do { if (!(c)) { printf("FAIL: %s (line %d)\n", msg, __LINE__); fails++; } else printf("ok:   %s\n", msg); } while (0)
#define GAP(c, msg) do { if (c) printf("ok:   %s\n", msg); else { printf("GAP:  %s\n", msg); gaps++; } } while (0)

static int pstate(int p) { return (mstp[3 - (p >> 2)] >> ((p << 1) & 7)) & 3; }
static void run(int n) { while (n--) { now++; ticks++; stp_timers(); } }

/* Deliver a BPDU on `port`. bridge_mac = designated bridge, root_prio = root's priority byte. */
static void rx_bpdu(int port, uint8_t root_prio, const uint8_t bridge_mac[6], uint8_t type, uint8_t flags,
                    uint8_t port_id, uint8_t bport_prio)
{
	static const uint8_t rmac[6] = {0x02, 0xaa, 0xaa, 0xaa, 0xaa, 0x01};
	uint8_t *h = uip_buf, *p;
	memset(uip_buf, 0, 200);
	h[0] = 0x01; h[1] = 0x80; h[2] = 0xc2;
	memcpy(h + 6, bridge_mac, 6);
	h[12] = 0x88; h[13] = 0x99; h[14] = 4; h[19] = (uint8_t)port;
	p = h + 20;
	p[0] = 0; p[1] = 0x27; p[2] = 0x42; p[3] = 0x42; p[4] = 3;
	p[7] = (type == 0x02) ? 2 : 0; p[8] = type; p[9] = flags;
	p[10] = root_prio; p[11] = 0; memcpy(p + 12, rmac, 6);
	/* cost 0 (root is directly behind the sender) */
	p[22] = root_prio; p[23] = 0; memcpy(p + 24, bridge_mac, 6);
	p[30] = bport_prio; p[31] = port_id;
	p[34] = 20; p[36] = 2; p[38] = 15;
	uip_len = 20 + 41;
	stp_in();
}
#define FL_DESIG (0x0c | 0x30)	/* role designated, learning, forwarding */

int main(void)
{
	const uint8_t up_mac[6] = {0x02, 0xaa, 0xaa, 0xaa, 0xaa, 0x01};
	long t0;

	link_mask = PORT_BIT(1) | PORT_BIT(2) | PORT_BIT(4) | PORT_BIT(5);
	stp_defaults();
	stp_setup();
	CHECK(stp_root_port == 0xff, "starts as root");
	CHECK(pstate(1) == 1, "ports start blocking (listen period)");

	/* ---- election and fast listen ---- */
	rx_bpdu(1, 0x10, up_mac, 0x02, FL_DESIG, 1, 0x80);
	CHECK(stp_root_port == 1 && root_bridge.prio == 0x10, "better root on port 1: becomes root port");
	CHECK(root_bridge_cost == 20000, "root path cost = port cost");

	/* ---- alternate port: second link to the same upstream bridge ---- */
	for (int i = 0; i < 800; i++) {
		if (i % 100 == 0) {
			rx_bpdu(1, 0x10, up_mac, 0x02, FL_DESIG, 1, 0x80);
			rx_bpdu(2, 0x10, up_mac, 0x02, FL_DESIG, 2, 0x80);
		}
		run(1);
	}
	CHECK(pstate(1) == 3, "root port forwards after listen period");
	CHECK(pstate(2) == 1 && stp_alt[2], "second link to same upstream bridge is Alternate (blocking)");
	CHECK(pstate(4) == 3, "port facing a host/downstream still forwards (designated)");

	/* ---- topology change ---- */
	t0 = now;
	link_mask &= ~PORT_BIT(5);
	run(120);
	GAP(tx_since(1, t0, 0x01, -1) || tx_since(1, t0, 0, 0x80), "topology change notified toward the root (TC BPDU or TCN on root port)");
	CHECK(tx_since(4, t0, 0x01, -1), "designated port sets TC flag in its hellos (regression)");

	/* ---- TCN received -> TCA ---- */
	t0 = now;
	rx_bpdu(4, 0, up_mac, 0x80, 0, 0, 0);
	CHECK(tx_since(4, t0, 0x80, -1), "received TCN acknowledged with TCA (regression)");

	/* ---- backup role: own BPDU heard on a sibling port ---- */
	link_mask |= PORT_BIT(6) | PORT_BIT(7);
	run(150);
	rx_bpdu(6, 0x80, uip_ethaddr.addr, 0x02, FL_DESIG, 8, 0x80);	/* our own BPDU of port 7 */
	CHECK(pstate(7) != 3, "own BPDU on port 6 (sibling of 7): one port blocked (loop hold, backup-like)");

	/* ---- proposal / agreement (fresh start) ---- */
	link_mask = PORT_BIT(1) | PORT_BIT(4);
	ntx = 0;
	stp_defaults();
	stp_setup();
	t0 = now;
	rx_bpdu(1, 0x10, up_mac, 0x02, 0x02 /*proposal*/ | 0x0c, 1, 0x80);
	run(60);	/* ~1 s */
	GAP(tx_since(1, t0, 0x40, -1), "Agreement BPDU sent in answer to a Proposal");
	GAP(pstate(1) == 3, "root port forwards within ~1 s after Proposal/Agreement (not after 2x forward delay)");

	/* ---- alternate failover and expiry (fresh start) ---- */
	link_mask = PORT_BIT(1) | PORT_BIT(2) | PORT_BIT(4);
	stp_defaults();
	stp_setup();
	for (int i = 0; i < 800; i++) {
		if (i % 100 == 0) {
			rx_bpdu(1, 0x10, up_mac, 0x02, FL_DESIG, 1, 0x80);
			rx_bpdu(2, 0x10, up_mac, 0x02, FL_DESIG, 2, 0x80);
		}
		run(1);
	}
	CHECK(stp_root_port == 1 && pstate(1) == 3 && pstate(2) == 1, "setup: root port 1, alternate port 2");
	for (int i = 0; i < 1100; i++) {	/* root port goes silent, alternate keeps hearing the root */
		if (i % 100 == 0)
			rx_bpdu(2, 0x10, up_mac, 0x02, FL_DESIG, 2, 0x80);
		run(1);
	}
	CHECK(stp_root_port == 2 && pstate(2) == 3, "root port lost: alternate takes over and forwards");
	CHECK(root_bridge.prio == 0x10, "root bridge kept through failover (no re-election as root)");

	stp_defaults();
	stp_setup();
	for (int i = 0; i < 800; i++) {
		if (i % 100 == 0) {
			rx_bpdu(1, 0x10, up_mac, 0x02, FL_DESIG, 1, 0x80);
			rx_bpdu(2, 0x10, up_mac, 0x02, FL_DESIG, 2, 0x80);
		}
		run(1);
	}
	for (int i = 0; i < 1100; i++) {	/* alternate port goes silent, root port stays */
		if (i % 100 == 0)
			rx_bpdu(1, 0x10, up_mac, 0x02, FL_DESIG, 1, 0x80);
		run(1);
	}
	CHECK(stp_root_port == 1 && !stp_alt[2] && pstate(1) == 3, "silent alternate expires, root port unaffected");

	printf("\n%s (%d failure(s)), %d known gap(s)\n", fails ? "FAILED" : "ALL PASSED", fails, gaps);
	return fails != 0;
}
