/* dispatch.c  v001  210714  mtm  */
/*********************************************
 Name:        dispatch.c
 Intention:   dispatch a routed txn to its handler entry point
 MODIFICATION HISTORY:
     v001  210714  mtm  maintained
*/
/*
 * dispatch.c — computed-target dispatch. (Tier 3, coverage: coarse / unresolved)
 *
 * EXTRACTOR HAZARD (computed call target through an opaque pointer):
 *   dispatch_generic() obtains a handler via lookup_handler() — which returns
 *   a `const brand_handler_t *` whose concrete identity is only known at
 *   runtime — then selects a member function by a computed index and calls
 *   through it. The extractor cannot determine the call target at all; this
 *   file is the canonical "function-pointer dispatch in dispatch.c" entry in
 *   coverage_report.unresolved_patterns (§3.3 example).
 */

#include "brand.h"
#include "txn.h"
#include "errors.h"
#include "common.h"

typedef int (*phase_fn)(struct txn *t);

/* Selects route/settle by phase, then calls through the chosen pointer.
 * Neither the member selection nor the eventual target is statically known. */
int dispatch_generic(txn_t *t)
{
    const brand_handler_t *h;
    phase_fn fn;

    if (!t)
        return PDLC_ERR_ROUTE_FAILED;

    h = lookup_handler(t->brand);            /* opaque vtable pointer */
    if (!h)
        return PDLC_ERR_BRAND_UNKNOWN;

    /* Computed member selection: route for auth/capture, settle for settle. */
    fn = (t->phase == TXN_SETTLE) ? h->settle : h->route;
    if (!fn)
        return PDLC_ERR_ROUTE_FAILED;

    return fn(t);                            /* unresolved computed target */
}

/* Secondary indirection: a raw void* recovered from brand_ctx is cast to a
 * handler and dispatched — fully opaque to static analysis. */
int dispatch_via_ctx(txn_t *t)
{
    const brand_handler_t *h;

    if (!t || !t->brand_ctx)
        return PDLC_ERR_ROUTE_FAILED;

    h = (const brand_handler_t *)t->brand_ctx;
    if (!h->route)
        return PDLC_ERR_ROUTE_FAILED;
    return h->route(t);
}
