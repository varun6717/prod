/* message.h  v005  231104  mtm  */
/*********************************************
 Name:        message.h
 PURPOSE:     ISO 8583 message struct and field accessors
 MODIFICATION HISTORY:
     v005  231104  mtm  maintained
*/
#ifndef PDLC_MESSAGE_H
#define PDLC_MESSAGE_H

#include <stdint.h>

/*
 * message.h — ISO 8583-style wire message model.
 * Clean, fully-typed struct + prototypes (Tier 1). The field codec table in
 * src/messaging/field_codec.c, however, dispatches through function pointers
 * indexed by field number, which the extractor cannot resolve (Tier 2).
 */

#define ISO_MAX_FIELDS 128

typedef struct iso_msg {
    uint16_t mti;             /* message type indicator, e.g. 0x0200 */
    uint8_t  bitmap[16];      /* primary + secondary bitmap          */
    char    *fields[ISO_MAX_FIELDS];
} iso_msg_t;

struct txn;  /* forward declaration */

/* Parser/builder (src/messaging/formatter.c, src/messaging/iso8583.c). */
int parse_iso8583(const char *raw, int len, iso_msg_t *out);
int build_iso8583(const iso_msg_t *m, char *buf, int len);

/* Settlement-message formatting — the second clean hop of the scope_ripple
 * chain: settlement/reconciler.c calls this. (src/messaging/formatter.c) */
int format_settlement_msg(struct txn *t, char *buf, int len);

/* Per-field encode/decode (src/messaging/field_codec.c). */
int encode_field(const iso_msg_t *m, int field, char *buf, int len);
int decode_field(iso_msg_t *m, int field, const char *raw, int len);

#endif /* PDLC_MESSAGE_H */
