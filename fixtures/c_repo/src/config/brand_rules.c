/* brand_rules.c  v002  220228  mtm  */
/*********************************************
 Name:        brand_rules.c
 PURPOSE:     brand rule table load and cache
 MODIFICATION HISTORY:
     v002  220228  mtm  maintained
*/
/*
 * brand_rules.c — brand rule table + macro-generated handlers.
 * (Tier 3, coverage: coarse / unresolved)
 *
 * EXTRACTOR HAZARD (a macro that generates whole functions):
 *   DECLARE_BRAND_HANDLER(brand) token-pastes a complete `<brand>_route`
 *   function definition. ctags does NOT expand macros, so the generated
 *   symbols visa_route / mastercard_route / amex_route / discover_route are
 *   INVISIBLE to the index — yet brand_registry.c references them by name and
 *   the route table dispatches into them. The file's real interface is
 *   therefore under-reported: only get_brand_rule() is resolvable, so this
 *   file lands in coverage_report.files_unresolved.
 *
 *   The generated *_route functions are also what route_table.c's function
 *   pointers ultimately reach — closing the unresolvable routing loop.
 */

#include "brand_rules.h"
#include "txn.h"
#include "errors.h"
#include "common.h"

/* Clean, resolvable lookup — this is the depends_on target of
 * routing/brand_router.c and routing/capture_route.c. */
static const brand_rule_t g_rules[] = {
    { BRAND_VISA,       3, 1, 86400 },
    { BRAND_MASTERCARD, 3, 1, 86400 },
    { BRAND_DISCOVER,   2, 0, 43200 },
    { BRAND_AMEX,       2, 1, 86400 },
};

const brand_rule_t *get_brand_rule(brand_id_t brand)
{
    size_t i;
    for (i = 0; i < PDLC_ARRAY_LEN(g_rules); i++) {
        if (g_rules[i].brand == brand)
            return &g_rules[i];
    }
    return 0;
}

/*
 * The macro hazard. Each invocation expands to a full function definition that
 * ctags cannot see. cscope cannot trace calls into these symbols.
 */
#define DECLARE_BRAND_HANDLER(br)                             \
    int br##_route(txn_t *t)                                  \
    {                                                         \
        const brand_rule_t *r = get_brand_rule(t->brand);     \
        if (!r)                                               \
            return PDLC_ERR_BRAND_UNKNOWN;                     \
        if (r->requires_3ds && t->amount_minor > 0)           \
            t->flags |= TXN_FLAG_RETRYABLE;                   \
        return PDLC_OK;                                       \
    }

DECLARE_BRAND_HANDLER(visa)
DECLARE_BRAND_HANDLER(mastercard)
DECLARE_BRAND_HANDLER(amex)

/* Discover is generated only when the brand is enabled in the build (see
 * feature_flags.c) — a macro AND a conditional-compilation hazard combined. */
#ifdef ENABLE_DISCOVER
DECLARE_BRAND_HANDLER(discover)
#endif
