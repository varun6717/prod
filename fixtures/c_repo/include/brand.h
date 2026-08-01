/* brand.h  v002  220228  mtm  */
/*********************************************
 Name:        brand.h
 PURPOSE:     card brand identifiers and rule struct
 MODIFICATION HISTORY:
     v002  220228  mtm  maintained
*/
#ifndef PDLC_BRAND_H
#define PDLC_BRAND_H

/*
 * brand.h — card-brand identifiers and the runtime handler vtable.
 *
 * The brand_handler_t struct is the central Tier-2 pattern in this repo:
 * a table of function pointers resolved at runtime. ctags sees the struct
 * definition and its members, but cscope cannot resolve which concrete
 * function a given `.route` / `.settle` / `.format_msg` member points to at
 * a call site — the binding happens through register_brand()/lookup_handler()
 * at init time, which static analysis cannot trace.
 */

typedef enum brand_id {
    BRAND_UNKNOWN    = 0,
    BRAND_VISA       = 1,
    BRAND_MASTERCARD = 2,
    BRAND_DISCOVER   = 3,
    BRAND_AMEX       = 4,
    BRAND_MAX
} brand_id_t;

struct txn;  /* forward declaration; full type in txn.h */

/* Per-brand handler vtable. Concrete functions live in src/transaction/*
 * and src/routing/*; they are wired in at registration, not at compile time. */
typedef struct brand_handler {
    brand_id_t  brand;
    const char *name;
    int       (*route)(struct txn *t);                       /* dispatch into a brand router  */
    int       (*settle)(struct txn *t);                      /* brand-specific settlement     */
    int       (*format_msg)(struct txn *t, char *buf, int len); /* brand wire formatting      */
} brand_handler_t;

/* Registry API (implemented in src/routing/brand_registry.c). */
int                    register_brand(const brand_handler_t *h);
const brand_handler_t *lookup_handler(brand_id_t brand);

const char *brand_name(brand_id_t brand);

#endif /* PDLC_BRAND_H */
