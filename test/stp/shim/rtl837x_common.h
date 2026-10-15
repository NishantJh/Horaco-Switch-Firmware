/* Host shim: replaces RTLPlayground headers so rtl837x_lacp.c compiles unmodified with gcc. */
#ifndef SHIM_COMMON_H
#define SHIM_COMMON_H
#include <stdint.h>
#include <string.h>
#define __xdata
#define __code
#define __banked
#define __data
#define SYS_TICK_HZ 200
#define MAC_ADDR_LEN 6
#define PORT_BIT(p) ((uint16_t)1 << (p))
#define TICKS_DUE(last, period) ((uint8_t)((uint8_t)ticks - (last)) >= (period))
#define HTONS(x) ((uint16_t)((((x) & 0xff) << 8) | (((x) >> 8) & 0xff)))
#define RTL_FRAME_TAG_ID 0x8899
#define RTL_FRAME_TAG_VERSION 0x04
#define RTL_TAG_LEARN_DIS 0x0020
#define RTL_TAG_KEEP 0x0080
#define RTL_FRAME_DESC_SIZE 12
#define UIP_CONF_BUFFER_SIZE 1600
#define VLAN_TAG_SIZE 4
struct rtl_tag { uint16_t tag; uint8_t version; uint8_t reason; uint16_t flags; uint16_t pmask; };
#define RTL_TAG_SIZE (sizeof(struct rtl_tag))
struct uip_eth_addr { uint8_t addr[6]; };
struct machine { uint8_t min_port, max_port; uint8_t log_to_phys_port[10]; };
struct machine_runtime { uint8_t isRTL8373 : 1; uint8_t isN : 1; };
extern uint8_t uip_buf[UIP_CONF_BUFFER_SIZE + 2];
extern uint16_t uip_len;
extern volatile uint32_t ticks;
void tcpip_output(void);
void print_string(const char *s);
void print_byte(uint8_t b);
void print_short(uint16_t s);
void write_char(char c);
#endif
/* ---- extras for rtl837x_stp.c ---- */
#ifndef SHIM_STP_EXTRAS
#define SHIM_STP_EXTRAS
#define CPU_PORT 9
#define CMD_BUF_SIZE 128
#define PMASK_CPU 0x200
#define PMASK_6 0x40
#define PMASK_9 0x200
#define __reentrant
void reg_read_m(uint16_t reg_addr);
void reg_write_m(uint16_t reg_addr);
void print_reg(uint16_t reg);
void print_long(uint32_t v);
void itoa(uint8_t v);
int vlan_get(uint16_t vid);
void port_l2mc_set(uint8_t a, uint16_t vid, uint16_t pmask);
uint16_t port_pvid_get(uint8_t p);
extern uint8_t stp_enabled;
#define ERR_INVALID_ARGUMENT 1
#endif
