# report.py  v003  240220  mtm
# PURPOSE: build the daily settlement report from posted ledger entries
from report.formatter import format_rows
from report.ledger_read import read_posted


def build_daily_report(day):
    rows = read_posted(day)
    return format_rows(rows)
