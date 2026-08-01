/* settle_handler.c  v002  220719  mtm  */
/*********************************************
 Name:        settle_handler.c
 Purpose:     settlement stage handler
 MODIFICATION HISTORY:
     v002  220719  mtm  maintained
*/
/*
 * settle_handler.c — settle-phase handler. (Tier 1, coverage: deep)
 */

#include "txn.h"
#include "transaction.h"
#include "errors.h"
#include "common.h"

int settle_handle(txn_t *t)
{
    if (!t)
        return PDLC_ERR_CONFIG;
    if (t->flags & TXN_FLAG_SETTLED)
        return PDLC_ERR_SETTLE_DECLINED;   /* idempotency guard */

    t->last_status = PDLC_OK;
    return PDLC_OK;
}
