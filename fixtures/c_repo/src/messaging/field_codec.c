/* field_codec.c  v003  221207  mtm  */
/*********************************************
 Name:        field_codec.c
 Desc:        per-field encode/decode codec table
 MODIFICATION HISTORY:
     v003  221207  mtm  maintained
*/
/*
 * field_codec.c — per-field ISO 8583 codec table. (Tier 2, coverage: coarse)
 *
 * EXTRACTOR HAZARD (function-pointer dispatch keyed by field number):
 *   encode_field()/decode_field() index a static codec table and call through
 *   `codec_table[field].encode(...)`. ctags sees the table and the public
 *   functions; cscope cannot resolve which concrete encoder runs for a given
 *   field. The concrete codecs are file-static here, so the gap is intra-file
 *   (no missing cross-module edge), but the indirect call still forces
 *   coverage:coarse and an unresolved_patterns entry.
 */

#include "codec.h"
#include "errors.h"
#include "common.h"

static int encode_numeric(const iso_msg_t *m, int field, char *buf, int len)
{
    const char *v = FIELD_OR(m, field, "0");
    size_t n = strlen(v);
    if ((int)n >= len)
        return -1;
    memcpy(buf, v, n);
    return (int)n;
}

static int decode_numeric(iso_msg_t *m, int field, const char *raw, int len)
{
    PDLC_UNUSED(len);
    if (field < 0 || field >= ISO_MAX_FIELDS)
        return -1;
    m->fields[field] = (char *)raw;
    return 0;
}

static field_codec_t g_codecs[ISO_MAX_FIELDS];

int codec_register(int field, field_encode_fn enc, field_decode_fn dec)
{
    if (field < 0 || field >= ISO_MAX_FIELDS)
        return PDLC_ERR_CONFIG;
    g_codecs[field].field  = field;
    g_codecs[field].encode = enc;
    g_codecs[field].decode = dec;
    return PDLC_OK;
}

int encode_field(const iso_msg_t *m, int field, char *buf, int len)
{
    field_encode_fn fn;
    if (field < 0 || field >= ISO_MAX_FIELDS)
        return -1;
    fn = g_codecs[field].encode;
    if (!fn)
        fn = encode_numeric;                 /* default; chosen codec is dynamic */
    return fn(m, field, buf, len);           /* unresolved indirect call */
}

int decode_field(iso_msg_t *m, int field, const char *raw, int len)
{
    field_decode_fn fn;
    if (field < 0 || field >= ISO_MAX_FIELDS)
        return -1;
    fn = g_codecs[field].decode;
    if (!fn)
        fn = decode_numeric;
    return fn(m, field, raw, len);           /* unresolved indirect call */
}
