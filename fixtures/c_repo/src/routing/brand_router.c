/* brand_router.c  v003  220118  mtm  */
/*********************************************
 Name:        brand_router.c
 PURPOSE:     route an authorization to the brand handler
 MODIFICATION HISTORY:
     v003  220118  mtm  maintained
*/
/*
 * brand_router.c — primary transaction router. (Tier 1, coverage: deep)
 *
 * This is the clean head of the scope_ripple chain: route_transaction() makes
 * a direct, statically-resolvable call to reconcile_txn() (settlement) on the
 * settle path. That edge — routing/brand_router -> settlement/reconciler — is
 * the "adding a brand also changes settlement" relationship D6b traces.
 */

#include "routing.h"
#include "route_table.h"
#include "reconciler.h"
#include "brand_rules.h"
#include "errors.h"
#include "common.h"

int route_transaction(txn_t *t)
{
    const brand_rule_t *rule;
    int rc;

    if (!t)
        return PDLC_ERR_ROUTE_FAILED;

    rule = get_brand_rule(t->brand);          /* -> config/brand_rules (clean) */
    if (!rule)
        return PDLC_ERR_BRAND_UNKNOWN;

    rc = route_via_table(t);                  /* -> routing/route_table (clean call;
                                                 the fn-ptr hop inside is coarse)   */
    if (rc != PDLC_OK)
        return rc;

    if (t->phase == TXN_SETTLE) {
        rc = reconcile_txn(t);                /* -> settlement/reconciler  (HOP 1, clean) */
        if (rc == PDLC_OK)
            t->flags |= TXN_FLAG_SETTLED;
    }
    return rc;
}

int register_brand_routes(void)
{
    brand_id_t b;
    int rc = PDLC_OK;

    for (b = BRAND_VISA; b < BRAND_MAX; b++) {
        const brand_handler_t *h = lookup_handler(b);   /* -> routing/brand_registry */
        if (h)
            rc = route_table_install(b, h);             /* -> routing/route_table    */
    }
    return rc;
}
