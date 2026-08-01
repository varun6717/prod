/* iso8583.c  v006  240119  mtm  */
/*********************************************
 Name:        iso8583.c
 PURPOSE:     ISO 8583 message parse and build
 MODIFICATION HISTORY:
     v006  240119  mtm  maintained
*/
/*
 * iso8583.c — low-level ISO 8583 frame builder. (Tier 1, coverage: deep)
 * Bit/byte manipulation only; fully resolvable.
 */

#include "message.h"
#include "errors.h"
#include "common.h"

static int set_bit(uint8_t *bitmap, int field)
{
    int byte = (field - 1) / 8;
    int bit  = (field - 1) % 8;
    if (field < 1 || field > ISO_MAX_FIELDS)
        return -1;
    bitmap[byte] |= (uint8_t)(0x80u >> bit);
    return 0;
}

int build_iso8583(const iso_msg_t *m, char *buf, int len)
{
    int written = 0;
    int f;

    if (!m || !buf || len < 4)
        return -1;

    buf[written++] = (char)(m->mti >> 8);
    buf[written++] = (char)(m->mti & 0xFF);

    for (f = 2; f <= ISO_MAX_FIELDS && written < len; f++) {
        if (m->fields[f]) {
            size_t flen = strlen(m->fields[f]);
            if (written + (int)flen >= len)
                break;
            memcpy(buf + written, m->fields[f], flen);
            written += (int)flen;
        }
    }
    return written;
}
