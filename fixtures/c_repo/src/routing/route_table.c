/* route_table.c  v002  210903  mtm  */
/*********************************************
 Name:        route_table.c
 PURPOSE:     reloadable brand routing table lookup
 MODIFICATION HISTORY:
     v002  210903  mtm  maintained
*/
/*
 * route_table.c — brand dispatch table. (Tier 2, coverage: coarse)
 *
 * EXTRACTOR HAZARD (function-pointer dispatch through a table):
 *   route_via_table() indexes a static table of {brand_id, handler vtable}
 *   and invokes `entry->handler->route(t)` through a function pointer. ctags
 *   sees the g_route_table array and route_via_table(); cscope CANNOT resolve
 *   which concrete handler `entry->handler->route` calls, because the binding
 *   is installed at runtime via route_table_install(). This is the routing ->
 *   transaction cross-module edge that merge_edges cannot fully stitch — it
 *   belongs in coverage_report.unresolved_patterns, NOT in depends_on.
 */

#include "route_table.h"
#include "errors.h"
#include "common.h"

static route_entry_t g_route_table[BRAND_MAX];

int route_table_install(brand_id_t brand, const brand_handler_t *h)
{
    if (brand <= BRAND_UNKNOWN || brand >= BRAND_MAX || !h)
        return PDLC_ERR_CONFIG;
    g_route_table[brand].brand   = brand;
    g_route_table[brand].handler = h;
    return PDLC_OK;
}

int route_via_table(txn_t *t)
{
    route_entry_t *entry;

    if (!t || t->brand <= BRAND_UNKNOWN || t->brand >= BRAND_MAX)
        return PDLC_ERR_BRAND_UNKNOWN;

    entry = &g_route_table[t->brand];
    if (!entry->handler || !entry->handler->route)
        return PDLC_ERR_ROUTE_FAILED;

    /* Unresolvable indirect call: target depends on what was installed. */
    return entry->handler->route(t);
}
