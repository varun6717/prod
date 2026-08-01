/* capture_route.c  v001  211102  mtm  */
/*********************************************
 Name:        capture_route.c
 Putpose:     route capture-stage traffic to settlement
 MODIFICATION HISTORY:
     v001  211102  mtm  maintained
*/
/*
 * capture_route.c — capture-phase routing. (Tier 1, coverage: deep)
 * A second clean routing entry point so the routing module has more than one
 * resolvable interface and route_table has more than one caller.
 */

#include "routing.h"
#include "route_table.h"
#include "brand_rules.h"
#include "errors.h"
#include "common.h"

int route_capture(txn_t *t)
{
    const brand_rule_t *rule;

    if (!t || t->phase != TXN_CAPTURE)
        return PDLC_ERR_ROUTE_FAILED;

    rule = get_brand_rule(t->brand);          /* -> config/brand_rules (clean) */
    if (!rule)
        return PDLC_ERR_BRAND_UNKNOWN;

    if (rule->requires_3ds && !(t->flags & TXN_FLAG_RETRYABLE))
        return PDLC_ERR_ROUTE_FAILED;

    return route_via_table(t);                /* -> routing/route_table (clean) */
}
