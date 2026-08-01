/* iso8583_v2.c  v002  240605  mtm  */
/*********************************************
 Name:        iso8583_v2.c
 PURPOSE:     ISO 8583 message parse and build (2003 revision)
 MODIFICATION HISTORY:
     v001  240412  mtm  forked from iso8583.c for the 2003 field set
     v002  240605  mtm  extended bitmap handling
*/
/*
 * iso8583_v2.c — the VERSIONED DUPLICATE hazard (D-A20 finding 3).
 *
 * This file and iso8583.c are BOTH wired: both define a build/parse pair, both are
 * reachable, and neither is marked dead. That is the point. An assertion about ISO 8583
 * message construction lands on "message parsing" and must then answer a question the
 * code cannot: v1, v2, or both? Getting it wrong means shipping to the dead path.
 *
 * D-A20 measured 38 such suffix files repo-wide (_v2, _v6, _test, _old) with no silent
 * duplicate stems — so the hazard is real, bounded, and fully enumerable up front. The
 * extractor's job is to emit this as an ordinary file; SURFACING the pair as a finding
 * that requires operator disposition is the map build's job (D-A16), never a silent
 * pick by the agent.
 */

#include "message.h"
#include "errors.h"
#include "common.h"

static int set_bit_v2(uint8_t *bitmap, int field)
{
    int byte = (field - 1) / 8;
    int bit  = (field - 1) % 8;
    if (field < 1 || field > ISO_MAX_FIELDS)
        return -1;
    bitmap[byte] |= (uint8_t)(0x80u >> bit);
    return 0;
}

int build_iso8583_v2(const iso_msg_t *m, char *buf, int len)
{
    int written = 0;
    int f;

    if (!m || !buf || len < 4)
        return -1;

    buf[written++] = (char)(m->mti >> 8);
    buf[written++] = (char)(m->mti & 0xFF);

    for (f = 2; f <= ISO_MAX_FIELDS && written < len; f++) {
        if (m->fields[f]) {
            if (set_bit_v2((uint8_t *)buf + 2, f) != 0)
                return -1;
            written += 1;
        }
    }
    return written;
}

int parse_iso8583_v2(const char *buf, int len, iso_msg_t *out)
{
    if (!buf || !out || len < 4)
        return ERR_MSG_TRUNCATED;

    out->mti = (uint16_t)(((unsigned char)buf[0] << 8) | (unsigned char)buf[1]);
    return 0;
}
