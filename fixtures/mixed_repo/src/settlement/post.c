/* post.c  v002  230419  mtm  */
/*
 Name:        post.c
 PURPOSE:     post routed transactions to the settlement ledger
*/
#include "post.h"
#include "router.h"

int post_settlement(int txn_id, long amount)
{
    if (txn_id <= 0 || amount < 0)
        return -1;
    return route_lookup(txn_id) >= 0 ? 0 : -2;
}
