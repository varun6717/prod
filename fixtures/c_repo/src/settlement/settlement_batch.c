/* settlement_batch.c  v002  220405  mtm  */
/*********************************************
 Name:        settlement_batch.c
 Intention:   assemble and close settlement batches
 MODIFICATION HISTORY:
     v002  220405  mtm  maintained
*/
/*
 * settlement_batch.c — settlement batch accumulation. (Tier 1, coverage: deep)
 * Pure, fully-resolvable struct manipulation; no indirection.
 */

#include "batch.h"
#include "message.h"
#include "errors.h"
#include "common.h"

int batch_add(settle_batch_t *b, const txn_t *t)
{
    if (!b || !t)
        return PDLC_ERR_CONFIG;
    if (t->phase != TXN_SETTLE)
        return PDLC_ERR_SETTLE_DECLINED;

    b->count++;
    b->total_minor += t->amount_minor;
    return PDLC_OK;
}

int batch_flush(settle_batch_t *b)
{
    iso_msg_t m;
    char buf[512];
    int rc;

    if (!b || b->count == 0)
        return PDLC_ERR_CONFIG;

    memset(&m, 0, sizeof(m));
    m.mti = 0x0500;                          /* settlement advice */
    rc = build_iso8583(&m, buf, (int)sizeof(buf));  /* -> messaging/iso8583 */
    if (rc <= 0)
        return PDLC_ERR_MSG_MALFORMED;

    b->count = 0;
    b->total_minor = 0;
    return PDLC_OK;
}
