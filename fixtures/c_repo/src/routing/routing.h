/* routing.h  v003  220118  mtm  */
/*********************************************
 Name:        routing.h
 PURPOSE:     routing entry points
 MODIFICATION HISTORY:
     v003  220118  mtm  maintained
*/
#ifndef PDLC_ROUTING_H
#define PDLC_ROUTING_H

#include "txn.h"
#include "brand.h"

/*
 * routing.h — public interface of the routing module.
 * route_transaction() is the clean entry point the transaction lifecycle
 * calls; it makes the two clean cross-module calls of the scope_ripple
 * chain (-> settlement/reconciler) plus a brand-rule lookup (-> config).
 */

/* Primary router entry (src/routing/brand_router.c). */
int route_transaction(txn_t *t);
int register_brand_routes(void);

/* Capture-phase routing (src/routing/capture_route.c). */
int route_capture(txn_t *t);

#endif /* PDLC_ROUTING_H */
