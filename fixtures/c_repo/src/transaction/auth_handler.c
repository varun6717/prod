/* auth_handler.c  v004  230301  mtm  */
/*********************************************
 Name:        auth_handler.c
 PURPOSE:     authorization stage handler
 MODIFICATION HISTORY:
     v004  230301  mtm  maintained
*/
/*
 * auth_handler.c — authorization-phase handler. (Tier 1, coverage: deep)
 *
 * One of the concrete phase handlers the route table reaches at runtime via
 * its function pointers. Statically, auth_handle() is a clean symbol and is
 * called directly by txn_lifecycle.c; the *table-driven* path into it is the
 * edge that route_table.c cannot resolve.
 */

#include "txn.h"
#include "transaction.h"
#include "message.h"
#include "errors.h"
#include "common.h"

int auth_handle(txn_t *t)
{
    if (!t)
        return PDLC_ERR_CONFIG;
    if (t->amount_minor == 0)
        return PDLC_ERR_ROUTE_FAILED;

    /* Validate the auth request frame before routing. */
    if (t->pan_token[0] == '\0')
        return PDLC_ERR_MSG_MALFORMED;

    t->flags |= TXN_FLAG_RETRYABLE;
    t->last_status = PDLC_OK;
    return PDLC_OK;
}
