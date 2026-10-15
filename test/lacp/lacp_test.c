/* Host-side LACP test: compiles the real rtl837x_lacp.c against shims and drives it with crafted LACPDUs. */
#include <stdio.h>
#include <stdlib.h>
#include "rtl837x_common.h"
#include "rtl837x_lacp.h"
#include "rtl837x_regs.h"

uint8_t uip_buf[UIP_CONF_BUFFER_SIZE + 2];
uint16_t uip_len;
struct uip_eth_addr uip_ethaddr = {{0x02,0x11,0x22,0x33,0x44,0x55}};
struct machine machine = {0, 8, {1,2,3,4,5,6,7,8,9}};
struct machine_runtime machine_detected;
uint16_t management_vlan = 1;
volatile uint32_t ticks;
uint8_t lacpEnabled;

static int tx_count[11];
static uint8_t last_tx[200];
static int last_tx_len;
static uint16_t members[LACP_NUM_LAGS];
static uint8_t rma_act;

void tcpip_output(void)
{
	/* TX frame starts at RTL_FRAME_DESC_SIZE: dst6 src6 rtl_tag8 ...; pmask is the tag's last 2 bytes */
	uint16_t pm = (uint16_t)((uip_buf[12 + 18] << 8) | uip_buf[12 + 19]);
	int port;
	for (port = 0; port < 10; port++)
		if (pm == PORT_BIT(port))
			break;
	tx_count[port]++;
	last_tx_len = uip_len;
	memcpy(last_tx, &uip_buf[12], uip_len < 200 ? uip_len : 200);
	if (management_vlan != 0) { printf("FAIL: mgmt vlan not cleared on TX\n"); exit(1); }
}
void port_lag_members_set(uint8_t lag, uint16_t m) { members[lag] = m; }
void trap_rma_set(uint16_t reg, uint8_t act) { (void)reg; rma_act = act; }
void print_string(const char *s) { fputs(s, stdout); }
void print_byte(uint8_t b) { printf("%02x", b); }
void print_short(uint16_t s) { printf("%04x", s); }
void write_char(char c) { putchar(c); }

static int fails, gaps;
#define GAP(c, msg) do { if (c) printf("ok:   %s\n", msg); else { printf("GAP:  %s\n", msg); gaps++; } } while (0)
#define CHECK(c, msg) do { if (!(c)) { printf("FAIL: %s (line %d)\n", msg, __LINE__); fails++; } else printf("ok:   %s\n", msg); } while (0)

/* Deliver a trapped partner LACPDU on `port`. `st` is the partner's actor state; `echo` its view of our state. */
static void rx(int port, const uint8_t sys[6], uint8_t st, uint16_t key, uint8_t echo)
{
	uint8_t *p = uip_buf;
	memset(uip_buf, 0, 200);
	p[0] = 0x01; p[1] = 0x80; p[2] = 0xc2; p[5] = 0x02;
	memcpy(p + 6, sys, 6);
	p[12] = 0x88; p[13] = 0x99; p[14] = 4; p[19] = (uint8_t)port;	/* rx pmask low nibble = port */
	p += 20;
	p[0] = 0x88; p[1] = 0x09; p[2] = 1; p[3] = 1; p[4] = 1; p[5] = 0x14;
	p[6] = 0xff; p[7] = 0xff; memcpy(p + 8, sys, 6);
	p[14] = key >> 8; p[15] = key; p[16] = 0; p[17] = 0xff; p[18] = 0; p[19] = port + 1; p[20] = st;
	p[26] = 2; p[27] = 0x14; memcpy(p + 28, uip_ethaddr.addr, 6); p[44] = echo;
	uip_len = 20 + 2 + 2 + 2 + 18 + 2 + 18 + 4;
	lacp_in();
}
static void run_ticks(int n) { for (int i = 0; i < n; i++) { ticks++; lacp_timers(); } }

int main(void)
{
	const uint8_t partner[6] = {0x02,0xaa,0xbb,0xcc,0xdd,0xee};
	const uint8_t other[6]   = {0x02,0x99,0x99,0x99,0x99,0x99};
	uint8_t st1 = LACP_STATE_ACTIVITY | LACP_STATE_AGGREGATION | LACP_STATE_TIMEOUT;
	uint8_t st2 = st1 | LACP_STATE_SYNC;
	int before;

	lacp_init();
	CHECK(!lacpEnabled, "engine off after init");

	lacp_lag_set(0, PORT_BIT(2) | PORT_BIT(3));
	CHECK(lacpEnabled && rma_act == RTL837X_RMA_ACT_TRAP, "lag_set enables engine and traps slow-protocol frames");
	CHECK(lacp_port_lag[2] == 0 && lacp_port_lag[3] == 0 && lacp_port_lag[4] == LACP_LAG_NONE, "ports 2,3 assigned to lag 0");
	CHECK(lacp_actor_state[2] == st1, "initial actor state ACT|AGG|short-timeout");

	run_ticks(8);
	CHECK(tx_count[2] >= 1 && tx_count[3] >= 1 && tx_count[4] == 0, "initial LACPDU sent on member ports only");
	CHECK(last_tx[0] == 0x01 && last_tx[1] == 0x80 && last_tx[2] == 0xc2 && last_tx[5] == 0x02, "dst = 01:80:c2:00:00:02");
	CHECK(last_tx[20] == 0x88 && last_tx[21] == 0x09 && last_tx[22] == 1 && last_tx[23] == 1, "ethertype 0x8809, subtype 1, version 1");
	CHECK(last_tx[24] == 1 && last_tx[25] == 0x14, "actor TLV type/len");
	printf("      (LACPDU length %d)\n", last_tx_len);

	rx(2, partner, st1, 5, 0);
	rx(3, partner, st1, 5, 0);
	CHECK(lacp_rx_state[2] == LACP_RX_CURRENT && lacp_agg_valid[0], "partner learned, aggregator selected");
	CHECK((lacp_actor_state[2] & LACP_STATE_SYNC) && !(lacp_actor_state[2] & LACP_STATE_COLLECTING), "actor SYNC set, waiting for partner sync");
	CHECK(members[0] == 0, "no LAG members until partner is in sync");

	rx(2, partner, st2, 5, lacp_actor_state[2]);
	rx(3, partner, st2, 5, lacp_actor_state[3]);
	CHECK((lacp_actor_state[2] & LACP_STATE_FULL) == LACP_STATE_FULL, "actor reaches SYNC|COLLECTING|DISTRIBUTING");
	CHECK(members[0] == (PORT_BIT(2) | PORT_BIT(3)), "hardware LAG members = ports 2,3");

	/* port 3 partner goes silent, port 2 keeps refreshing */
	for (int i = 0; i < 300; i++) {
		ticks += 4;
		if (i % 40 == 0)
			rx(2, partner, st2, 5, lacp_actor_state[2]);
		lacp_timers();
	}
	CHECK(lacp_rx_state[3] == LACP_RX_DEFAULTED, "silent port times out to DEFAULTED");
	CHECK(members[0] == PORT_BIT(2), "silent port removed from hardware LAG, other stays");

	rx(3, other, st2, 6, 0);
	CHECK(!(lacp_actor_state[3] & LACP_STATE_SYNC), "port with different partner system is not selected");
	CHECK(members[0] == PORT_BIT(2), "mismatched port not added to LAG");

	before = lacp_rx_count[2];
	rx(2, uip_ethaddr.addr, st2, 1, 0);
	CHECK(lacp_rx_count[2] == before, "looped-back own LACPDU ignored");

	rx(5, partner, st2, 5, 0);
	CHECK(lacp_rx_count[5] == 0, "LACPDU on non-LAG port ignored");

	lacp_off();
	CHECK(!lacpEnabled && rma_act == RTL837X_RMA_ACT_DROP, "lacp_off disables engine and drops slow-protocol frames");
	CHECK(members[0] == 0, "LAG members cleared on lacp_off");

	/* ---- Gap tests (PLAN step 2): desired 802.1AX behaviour; a GAP is a known missing feature, not a failure ---- */
	printf("\n-- gap tests --\n");
	{
		int tx6;
		uint8_t *p;
		tx_count[6] = 0;
		lacp_lag_set(1, PORT_BIT(6) | PORT_BIT(7));
		run_ticks(8);

		/* B. decoupled collect/distribute: partner in SYNC but not yet COLLECTING */
		rx(6, partner, st2, 5, 0);
		rx(6, partner, st2, 5, lacp_actor_state[6]);
		GAP((lacp_actor_state[6] & LACP_STATE_COLLECTING) && !(lacp_actor_state[6] & LACP_STATE_DISTRIBUTING),
		    "collecting enabled first, distributing only after partner collecting");
		GAP(members[1] == 0, "port not in LAG members until partner reports COLLECTING");
		rx(6, partner, st2 | LACP_STATE_COLLECTING, 5, lacp_actor_state[6]);
		CHECK(members[1] == PORT_BIT(6), "port joins LAG once partner is collecting (regression)");

		/* A. partner key selection: second port, same partner system but a different key */
		rx(7, partner, st2, 6, 0);
		rx(7, partner, st2 | LACP_STATE_COLLECTING, 6, lacp_actor_state[7]);
		GAP(!(members[1] & PORT_BIT(7)), "port with different partner key must not join the same aggregator");

		/* C. Marker protocol: Marker PDU (subtype 2) must be answered with a Marker Response */
		tx6 = tx_count[6];
		rx(6, partner, st2, 5, 0);	/* rebuild a valid frame, then turn it into a Marker PDU */
		p = uip_buf + 20;
		p[2] = 2;			/* subtype = Marker */
		p[4] = 1;			/* TLV marker information */
		lacp_in();
		GAP(tx_count[6] > tx6 && last_tx[22] == 2, "Marker PDU answered with Marker Response");
	}

	printf("\n%s (%d failure(s)), %d known gap(s)\n", fails ? "FAILED" : "ALL PASSED", fails, gaps);
	return fails != 0;
}
