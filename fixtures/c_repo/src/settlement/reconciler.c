/* reconciler.c  v005  230614  mtm  */
/*********************************************
 Name:        reconciler.c
 PURPOSE:     reconcile captured transactions against the ledger
 MODIFICATION HISTORY:
     v005  230614  mtm  maintained
*/
/*
 * reconciler.c — settlement reconciliation. (Tier 1, coverage: deep)
 *
 * Middle node of the scope_ripple chain:
 *   routing/brand_router -> settlement/reconciler (this file) -> messaging/formatter
 * reconcile_txn() makes a clean, statically-resolvable call to
 * format_settlement_msg() (HOP 2). It also posts to the ledger and batches.
 */

#include "reconciler.h"
#include "batch.h"
#include "message.h"
#include "errors.h"
#include "common.h"

static settle_batch_t g_open_window;

int reconcile_txn(txn_t *t)
{
    char msg[256];
    int n;

    if (!t)
        return PDLC_ERR_SETTLE_DECLINED;

    n = format_settlement_msg(t, msg, (int)sizeof(msg));  /* -> messaging/formatter (HOP 2) */
    if (n <= 0)
        return PDLC_ERR_MSG_MALFORMED;

    if (batch_add(&g_open_window, t) != PDLC_OK)          /* -> settlement/settlement_batch */
        return PDLC_ERR_SETTLE_DECLINED;

    if (ledger_post(t) != PDLC_OK)                        /* -> settlement/ledger_post */
        return PDLC_ERR_SETTLE_DECLINED;

    return PDLC_OK;
}

int reconcile_close_window(int window_id)
{
    if (g_open_window.window_id != window_id)
        return PDLC_ERR_CONFIG;
    return batch_flush(&g_open_window);                   /* -> settlement/settlement_batch */
}
