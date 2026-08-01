/* brand_registry.c  v004  230210  mtm  */
/*********************************************
 Name:        brand_registry.c
 Description: registry of known card brands and their handlers
 MODIFICATION HISTORY:
     v004  230210  mtm  maintained
*/
/*
 * brand_registry.c — brand handler registry. (Tier 2, coverage: coarse)
 *
 * EXTRACTOR HAZARD (callback registration):
 *   register_brand() stores a handler vtable pointer in a static array; the
 *   concrete vtables (g_visa_handler, ...) bind their `.route`/`.settle`
 *   members to the *macro-generated* functions in config/brand_rules.c
 *   (visa_route, mastercard_route, ...). ctags cannot see those generated
 *   symbols, and the link from `register_brand(&g_visa_handler)` to the
 *   eventual dispatch is not statically traceable. The clean, resolvable
 *   interfaces here are register_brand()/lookup_handler()/brand_name().
 */

#include "brand.h"
#include "brand_rules.h"
#include "errors.h"
#include "common.h"

/* Forward decls of the macro-generated route functions (defined in
 * config/brand_rules.c via DECLARE_BRAND_HANDLER). ctags does not index the
 * definitions, so these references stay unresolved. */
int visa_route(txn_t *t);
int mastercard_route(txn_t *t);
int amex_route(txn_t *t);

static const brand_handler_t g_visa_handler = {
    BRAND_VISA, "VISA", visa_route, 0, 0
};
static const brand_handler_t g_mc_handler = {
    BRAND_MASTERCARD, "MASTERCARD", mastercard_route, 0, 0
};
static const brand_handler_t g_amex_handler = {
    BRAND_AMEX, "AMEX", amex_route, 0, 0
};

static const brand_handler_t *g_registry[BRAND_MAX];

int register_brand(const brand_handler_t *h)
{
    if (!h || h->brand <= BRAND_UNKNOWN || h->brand >= BRAND_MAX)
        return PDLC_ERR_CONFIG;
    g_registry[h->brand] = h;
    return PDLC_OK;
}

const brand_handler_t *lookup_handler(brand_id_t brand)
{
    if (brand <= BRAND_UNKNOWN || brand >= BRAND_MAX)
        return 0;
    return g_registry[brand];
}

int register_default_brands(void)
{
    register_brand(&g_visa_handler);
    register_brand(&g_mc_handler);
    register_brand(&g_amex_handler);
    return PDLC_OK;
}

const char *brand_name(brand_id_t brand)
{
    const brand_handler_t *h = lookup_handler(brand);
    return h ? h->name : "UNKNOWN";
}
