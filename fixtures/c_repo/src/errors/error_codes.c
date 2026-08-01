/* error_codes.c  v001  210610  mtm  */
/*********************************************
 Name:        error_codes.c
 Descr:       error code definitions and text
 MODIFICATION HISTORY:
     v001  210610  mtm  maintained
*/
/*
 * error_codes.c — status-code to string mapping. (Tier 1, coverage: deep)
 * A plain switch; fully resolvable.
 */

#include "errors.h"
#include "common.h"

const char *pdlc_strerror(pdlc_status_t s)
{
    switch (s) {
    case PDLC_OK:                 return "ok";
    case PDLC_ERR_BRAND_UNKNOWN:  return "unknown card brand";
    case PDLC_ERR_ROUTE_FAILED:   return "routing failed";
    case PDLC_ERR_SETTLE_DECLINED:return "settlement declined";
    case PDLC_ERR_MSG_MALFORMED:  return "malformed message";
    case PDLC_ERR_TIMEOUT:        return "operation timed out";
    case PDLC_ERR_RETRY_EXHAUSTED:return "retries exhausted";
    case PDLC_ERR_CONFIG:         return "configuration error";
    default:                      return "unknown error";
    }
}

int is_retryable(pdlc_status_t s)
{
    return (s == PDLC_ERR_TIMEOUT || s == PDLC_ERR_ROUTE_FAILED) ? 1 : 0;
}
