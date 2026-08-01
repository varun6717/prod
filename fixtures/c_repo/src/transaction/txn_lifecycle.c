/* txn_lifecycle.c  v003  221115  mtm  */
/*********************************************
 Name:        txn_lifecycle.c
 DESCRIPTION: transaction state machine and stage advance
 MODIFICATION HISTORY:
     v003  221115  mtm  maintained
*/
/*
 * txn_lifecycle.c — end-to-end transaction lifecycle. (Tier 1, coverage: deep)
 *
 * The orchestrator: txn_authorize/capture/settle drive the phase machine and
 * call into routing (route_transaction, route_capture). These are the clean
 * routing -> ... entry calls, so brand_router/capture_route are used_by here.
 */

#include "txn.h"
#include "transaction.h"
#include "routing.h"
#include "errors.h"
#include "common.h"

int txn_authorize(txn_t *t)
{
    int rc;
    if (!t)
        return PDLC_ERR_CONFIG;

    t->phase = TXN_AUTH;
    rc = auth_handle(t);                      /* -> transaction/auth_handler */
    if (rc != PDLC_OK)
        return rc;

    rc = route_transaction(t);                /* -> routing/brand_router */
    if (rc == PDLC_OK)
        txn_advance(t, TXN_CAPTURE);
    return rc;
}

int txn_capture(txn_t *t)
{
    int rc;
    if (!t || t->phase != TXN_CAPTURE)
        return PDLC_ERR_CONFIG;

    rc = capture_handle(t);                   /* -> transaction/capture_handler */
    if (rc != PDLC_OK)
        return rc;

    rc = route_capture(t);                    /* -> routing/capture_route */
    if (rc == PDLC_OK)
        txn_advance(t, TXN_SETTLE);
    return rc;
}

int txn_settle(txn_t *t)
{
    int rc;
    if (!t || t->phase != TXN_SETTLE)
        return PDLC_ERR_CONFIG;

    rc = settle_handle(t);                    /* -> transaction/settle_handler */
    if (rc == PDLC_OK)
        rc = route_transaction(t);            /* -> routing/brand_router (settle path) */
    return rc;
}
