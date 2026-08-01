/* fallback.c  v002  220916  mtm  */
/*********************************************
 Name:        fallback.c
 Intention:   fallback handling when a brand handler is unavailable
 MODIFICATION HISTORY:
     v002  220916  mtm  maintained
*/
/*
 * fallback.c — maps a hard error to a recovery disposition. (Tier 1, deep)
 */

#include "errors.h"
#include "common.h"

pdlc_status_t error_fallback(pdlc_status_t s)
{
    switch (s) {
    case PDLC_ERR_TIMEOUT:
    case PDLC_ERR_ROUTE_FAILED:
        return PDLC_ERR_RETRY_EXHAUSTED;   /* hand back to caller for retry */
    case PDLC_ERR_SETTLE_DECLINED:
        return PDLC_ERR_SETTLE_DECLINED;   /* terminal; no fallback */
    default:
        return s;
    }
}
