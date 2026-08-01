/* txn.h  v003  221115  mtm  */
/*********************************************
 Name:        txn.h
 Description: transaction struct and stage enum
 MODIFICATION HISTORY:
     v003  221115  mtm  maintained
*/
#ifndef PDLC_TXN_H
#define PDLC_TXN_H

#include <stdint.h>
#include "brand.h"

/*
 * txn.h — the core transaction record threaded through the whole pipeline.
 * Every module reads or mutates a txn_t. This is the canonical shared struct
 * the extractor must resolve cleanly (Tier 1).
 */

typedef enum txn_phase {
    TXN_AUTH    = 0,
    TXN_CAPTURE = 1,
    TXN_SETTLE  = 2,
    TXN_REFUND  = 3
} txn_phase_t;

#define TXN_FLAG_RETRYABLE  0x0001u
#define TXN_FLAG_SETTLED    0x0002u
#define TXN_FLAG_REVERSED   0x0004u

typedef struct txn {
    char        txn_id[32];
    brand_id_t  brand;
    txn_phase_t phase;
    uint64_t    amount_minor;   /* amount in minor currency units */
    char        currency[4];    /* ISO 4217, e.g. "USD" */
    char        pan_token[24];  /* tokenized PAN, never the real number */
    uint32_t    flags;
    int         last_status;    /* pdlc_status_t of the last stage */
    void       *brand_ctx;      /* opaque per-brand context blob */
} txn_t;

/* Lifecycle entry points (implemented in src/transaction/txn_lifecycle.c). */
int txn_authorize(txn_t *t);
int txn_capture(txn_t *t);
int txn_settle(txn_t *t);

/* State helpers (src/transaction/txn_state.c). */
int  txn_advance(txn_t *t, txn_phase_t next);
int  txn_is_terminal(const txn_t *t);

#endif /* PDLC_TXN_H */
