# formatter.py  v002  240301  mtm
# Intention: render settlement rows into the DSR fixed-width format
def format_rows(rows):
    return "\n".join("%-16s%12s" % (r["product"], r["amount"]) for r in rows)
