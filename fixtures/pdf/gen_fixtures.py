"""
Generate synthetic Payment Brand PDF fixtures for PDLC_App_v2.

Produces two parts of the same Mastercard mandate (MCS-2026-R3) to exercise
multi-file processing: both files belong to one card brand / one requirement
so the pipeline must aggregate them.

The two parts also make the D-A12 **disposition split** concrete — the split is
why Business Requirement and Technical Specification are separate classes at all:

  mastercard_mandate_part1_2026.pdf  — the ASK: mandate overview, brand rules,
      certification gates, compliance deadline.
      disposition: [business_requirement]   → routes to §2 / §4 / §8 / §15

  mastercard_mandate_part2_2026.pdf  — the NORMATIVE DETAIL: ISO 8583 DE 48
      subelements, interchange tiers, Banknet/Reg II routing, reporting.
      disposition: [technical_specification] → routes to §8 / §10, and is the
      primary input Arm 1 matches against code

Same corpus, different destinations. An SI section routes on `disposition`
(D-A13 matrix), then reads whole or via the per-artifact index (D-A18) — there
are no tags on either side any more.
"""
import os
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

MC_RED    = colors.HexColor("#EB001B")
MC_ORANGE = colors.HexColor("#FF5F00")
MC_GRAY   = colors.HexColor("#555555")
MC_LGRAY  = colors.HexColor("#F5F5F5")
MC_LRED   = colors.HexColor("#FFF5F5")


def _styles():
    ss = getSampleStyleSheet()
    h1   = ParagraphStyle("H1",   parent=ss["Heading1"], fontSize=16, spaceAfter=6,  spaceBefore=12)
    h2   = ParagraphStyle("H2",   parent=ss["Heading2"], fontSize=13, spaceAfter=4,  spaceBefore=10)
    body = ParagraphStyle("Body", parent=ss["Normal"],   fontSize=10, leading=14,    spaceAfter=6, alignment=TA_JUSTIFY)
    cover= ParagraphStyle("Cover",parent=ss["Normal"],   fontSize=11, alignment=TA_CENTER, spaceAfter=4)
    return h1, h2, body, cover


def _doc(filename, title):
    path = os.path.join(OUT_DIR, filename)
    doc  = SimpleDocTemplate(path, pagesize=LETTER,
                             leftMargin=1.1*inch, rightMargin=1.1*inch,
                             topMargin=1*inch,    bottomMargin=1*inch,
                             title=title)
    return doc, path


# ---------------------------------------------------------------------------
# Part 1 — Mandate overview, brand rules, certification
# tags: mandate, compliance_deadline, brand_rules, card_brand, certification
# ---------------------------------------------------------------------------
def make_part1():
    doc, path = _doc(
        "mastercard_mandate_part1_2026.pdf",
        "Mastercard Brand Implementation Mandate MCS-2026-R3 Part 1 of 2"
    )
    h1, h2, body, cover = _styles()
    story = []

    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("MASTERCARD INTERNATIONAL INCORPORATED", cover))
    story.append(Paragraph("<b>Brand Implementation Mandate</b>", cover))
    story.append(Paragraph("Mandate ID: <b>MCS-2026-R3</b>  |  Part <b>1 of 2</b>: Mandate Overview, Brand Rules &amp; Certification", cover))
    story.append(Paragraph("Applicable Card Brand: <b>Mastercard</b> (incl. Maestro, Debit Mastercard)", cover))
    story.append(Paragraph("Version: 1.2  |  Status: Approved-Final  |  <b>Compliance Deadline: 2026-09-30</b>", cover))
    story.append(HRFlowable(width="100%", thickness=1, color=MC_RED, spaceAfter=12))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("1. Mandate Summary", h1))
    story.append(Paragraph(
        "This document is Part 1 of 2 for Mastercard brand mandate <b>MCS-2026-R3</b>. "
        "It covers the mandate rationale, brand rules, and certification requirements. "
        "Part 2 of 2 (document MCS-2026-R3-T) contains the technical implementation "
        "specification including ISO 8583 message format changes, revised interchange fee "
        "schedules, and Banknet routing updates. Both parts must be read together as a "
        "single binding requirement.", body))
    story.append(Paragraph(
        "Mandate MCS-2026-R3 is issued by Mastercard International Incorporated under "
        "authority of the Mastercard Rules and the Mastercard Security Rules and Procedures "
        "and is binding on all Mastercard-licensed acquirers, including JPMC Merchant Services. "
        "This mandate requires acquirers to update their processing systems to support "
        "<b>Mastercard Digital Enablement Service (MDES) token-based transactions</b>, "
        "revised interchange qualification criteria, and enhanced Banknet routing logic for "
        "Debit Mastercard and Maestro products. Full compliance is required by <b>2026-09-30</b>. "
        "This mandate supersedes circular MCS-2024-R7 in all matters relating to MDES token "
        "routing and interchange qualification.", body))

    story.append(Paragraph("2. Scope and Affected Card Brands", h1))
    story.append(Paragraph(
        "This mandate applies to all transactions bearing the following <b>Mastercard</b> "
        "card brand identifiers processed through JPMC Merchant Services acquiring infrastructure:", body))
    story.append(Paragraph(
        "• <b>Mastercard Credit</b> — all tiers (Standard, World, World Elite, Corporate)<br/>"
        "• <b>Debit Mastercard</b> — US and international debit products<br/>"
        "• <b>Maestro</b> — PIN debit, international card-present<br/>"
        "• <b>Mastercard Commercial</b> — purchasing, fleet, and business cards<br/>"
        "Prepaid Mastercard products are excluded from MDES token requirements but remain "
        "subject to interchange and routing changes in Part 2 of this mandate.", body))
    story.append(Paragraph(
        "BIN ranges in scope: 510000–559999 (Mastercard Credit/Debit), 600000–699999 (Maestro). "
        "Token BIN ranges 520000–529999 are specifically in scope for MDES token processing "
        "requirements. Transactions with primary account numbers outside these ranges "
        "and not presenting an MDES token are not affected by this mandate.", body))

    story.append(Paragraph("3. Brand Rules and Operational Constraints", h1))
    story.append(Paragraph("3.1 MDES Token Handling", h2))
    story.append(Paragraph(
        "Brand rule BR-01: Acquirers MUST NOT de-tokenize MDES tokens prior to forwarding "
        "authorization requests to Mastercard Banknet. De-tokenization is the exclusive "
        "responsibility of the Mastercard Digital Enablement Service and occurs at the Banknet "
        "gateway. Acquirer systems that strip or substitute token values will receive authorization "
        "declines with Response Code 14 ('Invalid card number') from the issuer.", body))
    story.append(Paragraph(
        "Brand rule BR-02: Token Requestor IDs (TRIDs) must be preserved in DE 48.66 through "
        "the full authorization chain. The TRID identifies the wallet or device that initiated "
        "the token-based transaction and is required for Mastercard's fraud analytics platform. "
        "Acquirers sourcing from mobile wallets (Apple Pay, Google Pay, Samsung Pay) MUST "
        "populate DE 48.66 and DE 48.77 (wallet indicator) as specified in Part 2.", body))
    story.append(Paragraph("3.2 Cardholder Verification Rules", h2))
    story.append(Paragraph(
        "Brand rule BR-03: For Mastercard contactless transactions above USD 100.00, the "
        "terminal MUST request CVM results per EMV Contactless Kernel C-3 (Mastercard "
        "Contactless Kernel, MCK). Acceptable CVM methods in priority order: (1) Online PIN, "
        "(2) Offline Enciphered PIN, (3) Signature. No CVM ('NOCVM') is permitted for transit "
        "and toll MCCs only (MCCs 4111, 4121, 4131, 7523). CVM result must appear in DE 55 "
        "Tag 9F34 (CVM Results).", body))
    story.append(Paragraph("3.3 Authorization Timeout and Fallback", h2))
    story.append(Paragraph(
        "Brand rule BR-04: If the primary Banknet authorization endpoint does not respond "
        "within 4000ms, acquirer systems MAY attempt the secondary Banknet endpoint. The "
        "fallback attempt MUST be logged with reason code T (timeout) in the transaction "
        "audit record. Stand-in processing (STIP) is available for issuers that have enrolled "
        "in Mastercard STIP; acquirers MUST forward the authorization to STIP on secondary "
        "endpoint timeout rather than declining the transaction at the acquiring host.", body))
    story.append(Paragraph("3.4 Decline Reason Code Updates", h2))
    story.append(Paragraph(
        "Brand rule BR-05: Response Code 55 returned for MDES token transactions now indicates "
        "'Token Assurance Level insufficient' rather than its legacy meaning of 'Incorrect PIN'. "
        "Acquirer host systems and merchant-facing decline reason engines MUST be updated to "
        "display 'Unable to process — please retry with chip card' for MC Response Code 55 "
        "on token transactions (identifiable by MDES token BIN range 520000–529999). "
        "Failure to distinguish this code will cause incorrect merchant messaging and consumer "
        "friction that Mastercard monitors via dispute rate metrics.", body))

    story.append(Paragraph("4. Certification and Conformance Requirements", h1))
    story.append(Paragraph(
        "All acquirers subject to MCS-2026-R3 MUST obtain <b>Mastercard Acquirer Certification "
        "(MAC) Level 2</b> for MDES token processing before the compliance deadline. "
        "Certification is administered by the Mastercard Certification Authority (MCA) via "
        "the Mastercard Connect portal. The certification process has three gates:", body))
    story.append(Paragraph(
        "<b>Gate C1 — Functional Test Suite:</b> Acquirer runs the Mastercard Test Suite (MTS) "
        "v8.4 test scripts against a UAT environment connected to the Mastercard Simulator. "
        "Required pass rate: 100% of Category A (mandatory) test cases, 85% of Category B "
        "(conditional) test cases. MTS v8.4 test scripts are available on Mastercard Connect "
        "under 'Certification &gt; MDES Token &gt; Acquirer Suite'. Estimated duration: 4 weeks.", body))
    story.append(Paragraph(
        "<b>Gate C2 — Interoperability Testing:</b> Acquirer submits 1,000 end-to-end "
        "transaction traces including MDES token transactions (minimum 300), fallback chip "
        "transactions (minimum 100), and Regulation II debit routing samples (minimum 50). "
        "Traces must be submitted via the Mastercard Testing API in JSONL format as specified "
        "in the MTS Integration Guide v8.4 Appendix D.", body))
    story.append(Paragraph(
        "<b>Gate C3 — Production Validation:</b> 60-day post-certification production monitoring "
        "period. Mastercard monitors token decline rates, TRID population rates, and DE 48.77 "
        "coverage via Mastercard Settlement Services data feeds. Any metric exceeding the "
        "alert threshold triggers a mandatory remediation review within 5 business days. "
        "MAC Level 2 is revoked if remediation is not completed within 30 calendar days.", body))
    story.append(Paragraph(
        "Acquirers that do not achieve MAC Level 2 by 2026-09-30 will have all Mastercard "
        "and Maestro transactions automatically downgraded to the Standard non-qualified "
        "interchange tier and will be placed on a 90-day remediation plan per "
        "Mastercard Rules Section 9.3.2.", body))

    story.append(Paragraph("5. Compliance Deadline and Milestones", h1))
    tdata = [
        ["Milestone", "Target Date", "Owner"],
        ["MTS v8.4 test harness provisioned", "2026-04-15", "JPMC Merchant Tech"],
        ["Gate C1 functional tests complete", "2026-06-15", "JPMC QA"],
        ["Gate C2 interoperability submission", "2026-07-31", "JPMC + MCA"],
        ["Production deployment (UAT → PROD)", "2026-09-01", "JPMC Ops"],
        ["Gate C3 monitoring period begins", "2026-09-01", "MCA"],
        ["COMPLIANCE DEADLINE (MCS-2026-R3)", "2026-09-30", "All parties"],
    ]
    t = Table(tdata, colWidths=[3.2*inch, 1.5*inch, 2.0*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  MC_RED),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("BACKGROUND",    (0, -1),(-1, -1), colors.HexColor("#FFF3CD")),
        ("FONTNAME",      (0, -1),(-1, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -2), [colors.white, MC_LGRAY]),
        ("ALIGN",         (1, 0), (1, -1),  "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("6. Normative References", h1))
    story.append(Paragraph(
        "• Mastercard Rules, April 2026 edition, Section 9.3<br/>"
        "• Mastercard Security Rules and Procedures v2026-Q1<br/>"
        "• Mastercard Digital Enablement Service (MDES) Acquirer Implementation Guide v5.2<br/>"
        "• Mastercard Test Suite (MTS) v8.4 Acquirer Script Package<br/>"
        "• EMV Contactless Kernel C-3 (Mastercard Contactless Kernel) v3.1<br/>"
        "• Prior mandate: MCS-2024-R7 (superseded by this document)<br/>"
        "• Part 2 of this mandate: MCS-2026-R3-T (Technical Specification)", body))

    doc.build(story)
    return path


# ---------------------------------------------------------------------------
# Part 2 — Technical specification: message format, interchange, routing, reporting
# tags: message_format, interchange_fees, routing, reporting, compliance_deadline, card_brand
# ---------------------------------------------------------------------------
def make_part2():
    doc, path = _doc(
        "mastercard_mandate_part2_2026.pdf",
        "Mastercard Brand Implementation Mandate MCS-2026-R3-T Part 2 of 2"
    )
    h1, h2, body, cover = _styles()
    story = []

    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("MASTERCARD INTERNATIONAL INCORPORATED", cover))
    story.append(Paragraph("<b>Technical Implementation Specification</b>", cover))
    story.append(Paragraph("Mandate ID: <b>MCS-2026-R3-T</b>  |  Part <b>2 of 2</b>: Message Formats, Interchange &amp; Routing", cover))
    story.append(Paragraph("Applicable Card Brand: <b>Mastercard</b> (incl. Maestro, Debit Mastercard)", cover))
    story.append(Paragraph("Version: 1.2  |  Status: Approved-Final  |  <b>Network Effective Date: 2026-07-01</b>  |  <b>Compliance Deadline: 2026-09-30</b>", cover))
    story.append(HRFlowable(width="100%", thickness=1, color=MC_ORANGE, spaceAfter=12))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("1. Introduction", h1))
    story.append(Paragraph(
        "This document is Part 2 of 2 for Mastercard mandate MCS-2026-R3 and contains the "
        "normative technical specification. Read in conjunction with Part 1 (MCS-2026-R3), "
        "which covers mandate overview, brand rules, and certification. The changes in this "
        "document are effective on the <b>Mastercard</b> network as of <b>2026-07-01</b>; "
        "JPMC internal compliance deadline is <b>2026-09-30</b>.", body))

    story.append(Paragraph("2. ISO 8583 Message Format Changes", h1))
    story.append(Paragraph("2.1 New Data Elements", h2))
    story.append(Paragraph(
        "The following new data elements are introduced in ISO 8583:2003 authorization "
        "(MTI 0100/0110) and financial request (MTI 0200/0210) messages for <b>Mastercard</b> "
        "transactions effective 2026-07-01:", body))
    new_de = [
        ["DE", "Field Name", "Type/Length", "Presence", "Description"],
        ["DE 48.66", "Token Requestor ID", "N-11", "Conditional", "TRID assigned by MDES to the wallet/device. Required when DE 2 is an MDES token (BIN 520000–529999). Must be preserved end-to-end; do not strip."],
        ["DE 48.77", "Digital Wallet Indicator", "AN-2", "Conditional", "Wallet type: 01=Apple Pay, 02=Google Pay, 03=Samsung Pay, 04=Masterpass, 05=Other. Required when payment originated from a digital wallet."],
        ["DE 48.78", "Token Assurance Level", "N-2", "Conditional", "Integer 00–99 from MDES vault indicating strength of token binding. Required when DE 2 is an MDES token. Value below 10 will trigger RC 55 from issuer."],
        ["DE 48.79", "Device Type", "AN-2", "Optional", "00=POS terminal, 01=Mobile handset, 02=Wearable, 03=IoT device, 04=Browser. Informational; used for Mastercard fraud scoring."],
    ]
    nt = Table(new_de, colWidths=[0.55*inch, 1.5*inch, 0.85*inch, 0.75*inch, 2.85*inch])
    nt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  MC_RED),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, MC_LRED]),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(nt)
    story.append(Spacer(1, 0.08*inch))

    story.append(Paragraph("2.2 Modified Data Elements", h2))
    mod_de = [
        ["DE", "Field Name", "Change", "Detail"],
        ["DE 61.8", "POS Environment",       "Value extended", "Bit 3: value '3' now = Soft POS (COTS device running certified payment app). Previously undefined. Implementors must not reject bit 3 = '3'."],
        ["DE 104", "Transaction Description", "Length + encoding", "Max length: 25 → 40 bytes. Encoding: ASCII → UTF-8. Truncate at 40 bytes (not characters) to avoid splitting multi-byte sequences."],
        ["DE 55",  "ICC System-Related Data", "New mandatory tag", "EMV tag 9F6E (Enhanced Contactless Reader Capabilities, 4 bytes) is now mandatory for all contactless transactions above USD 50. Absence causes decline RC 96 from Banknet gateway."],
        ["DE 48.10","Mastercard Assigned ID", "Scope extended",    "Now also required on Maestro transactions in EU/EEA region. Previously Mastercard Credit only."],
    ]
    mt2 = Table(mod_de, colWidths=[0.55*inch, 1.6*inch, 1.1*inch, 3.25*inch])
    mt2.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  MC_ORANGE),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#FFF8F0")]),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(mt2)
    story.append(Spacer(1, 0.08*inch))

    story.append(Paragraph("3. Interchange Fee Schedule", h1))
    story.append(Paragraph("3.1 Revised Consumer Credit Tiers (effective 2026-07-01)", h2))
    story.append(Paragraph(
        "Interchange fees are remitted acquirer-to-issuer via the Mastercard Interchange "
        "System (MIS). MCS-2026-R3 restructures consumer credit tiers to reflect MDES token "
        "presence and enhanced contactless eligibility. The 'Token Enhanced' column applies "
        "when DE 48.78 Token Assurance Level ≥ 50:", body))
    fee_data = [
        ["Product", "Transaction Type", "Standard Rate", "Token Enhanced Rate", "Effective"],
        ["MC World Elite", "Card-Present",     "2.10% + $0.10", "1.95% + $0.10", "2026-07-01"],
        ["MC World Elite", "Card-Not-Present", "2.40% + $0.10", "2.15% + $0.10", "2026-07-01"],
        ["MC World",       "Card-Present",     "1.90% + $0.10", "1.75% + $0.10", "2026-07-01"],
        ["MC World",       "Card-Not-Present", "2.20% + $0.10", "1.95% + $0.10", "2026-07-01"],
        ["MC Standard",    "Card-Present",     "1.65% + $0.15", "1.65% + $0.15", "2026-07-01"],
        ["MC Standard",    "Card-Not-Present", "1.85% + $0.15", "1.85% + $0.15", "2026-07-01"],
        ["Debit MC",       "PIN Debit",        "0.05% + $0.21", "0.05% + $0.21", "2026-07-01"],
        ["Maestro",        "PIN Debit",        "0.05% + $0.21", "0.05% + $0.21", "2026-07-01"],
    ]
    ft = Table(fee_data, colWidths=[1.1*inch, 1.3*inch, 1.2*inch, 1.4*inch, 1.0*inch])
    ft.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  MC_RED),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8.5),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, MC_LRED]),
        ("ALIGN",         (2, 0), (4, -1),  "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(ft)
    story.append(Spacer(1, 0.08*inch))
    story.append(Paragraph(
        "Acquirers MUST update interchange qualification logic to populate DE 48.78 where "
        "applicable so that eligible token transactions receive the reduced 'Token Enhanced' "
        "rate. Failure to populate DE 48.78 will result in Standard rate assessment regardless "
        "of actual token assurance. Retroactive interchange adjustments are not processed.", body))

    story.append(Paragraph("4. Transaction Routing Rules", h1))
    story.append(Paragraph("4.1 Banknet Endpoint Selection", h2))
    story.append(Paragraph(
        "Routing to Mastercard Banknet uses the BIN-first lookup in Mastercard BIN Table "
        "(MBT) v2026-Q2. The routing handler MUST: (1) extract the 6-digit BIN from DE 2; "
        "(2) resolve to network ID and product type in MBT; (3) select the Banknet "
        "authorization endpoint (primary or STIP) based on product type and Regulation II "
        "routing preference. Routing decisions MUST be immutable once made — mid-transaction "
        "re-routing is prohibited except on documented primary-endpoint timeout (≥ 4000ms). "
        "The selected network ID and reason code must be written to the transaction audit "
        "record within 200ms of routing decision.", body))
    story.append(Paragraph("4.2 Regulation II (Durbin) Routing for Debit Mastercard", h2))
    story.append(Paragraph(
        "US Debit Mastercard and Maestro transactions are subject to Regulation II "
        "(Durbin Amendment, 12 CFR Part 235). JPMC MUST ensure: (a) at least two "
        "unaffiliated networks are available for PIN debit; (b) the routing selection logic "
        "evaluates merchant preference (terminal flag), issuer routing preference (DE 55 "
        "ICC data), and cost optimization (interchange tier) in that priority order; "
        "(c) no routing exclusivity arrangement that limits merchant choice is implemented. "
        "The routing decision rationale must be preserved in the audit ledger for Federal "
        "Reserve examination (minimum 3-year retention).", body))
    story.append(Paragraph("4.3 MDES Token Routing", h2))
    story.append(Paragraph(
        "Transactions presenting MDES tokens (BIN 520000–529999 in DE 2) MUST be routed "
        "exclusively to the Mastercard Banknet MDES gateway (endpoint ID MCB-MDES-01). "
        "These transactions MUST NOT be routed to acquirer-side processing or alternate "
        "debit networks. The MDES gateway performs de-tokenization and forwards the "
        "real PAN to the issuer. Any routing path that bypasses MCB-MDES-01 for token "
        "BIN ranges will result in a hard decline with Response Code 58 "
        "('Transaction not permitted to terminal').", body))

    story.append(Paragraph("5. Reporting and Downstream Data Obligations", h1))
    story.append(Paragraph("5.1 Daily Settlement Report (DSR) Format Changes", h2))
    story.append(Paragraph(
        "Effective 2026-07-01, the DSR submitted to Mastercard Settlement Services by "
        "06:00 UTC must use the new format: (a) Product Code field extended from 2 to 4 "
        "characters using MBT v2026-Q2 codes; (b) a new 'Token Flag' column (Y/N) based "
        "on DE 48.77 presence; (c) wallet-type breakdown sub-section required when any "
        "token transactions are present in the batch (DE 48.77 codes 01–05 each reported "
        "separately). DSR files failing format validation will be rejected and the batch "
        "placed on settlement hold pending resubmission.", body))
    story.append(Paragraph("5.2 Regulation II Quarterly Compliance Report", h2))
    story.append(Paragraph(
        "Quarterly Regulation II compliance reports are due to Mastercard Compliance by "
        "the 15th of the month following each quarter end (Apr 15, Jul 15, Oct 15, Jan 15). "
        "Required fields: transaction count and interchange paid by network, routing override "
        "count with justification codes, and a certification statement from the acquirer's "
        "Chief Compliance Officer. Reports are filed via Mastercard Connect → Compliance → "
        "Reg II Quarterly Filing. These reports feed Mastercard's downstream analytics "
        "platform and are subject to Federal Reserve audit.", body))
    story.append(Paragraph("5.3 MDES Token Coverage Reporting", h2))
    story.append(Paragraph(
        "Monthly MDES token coverage reports must be submitted by the 5th of each month "
        "for the prior month. The report must include: (a) total transaction count; "
        "(b) token transaction count (DE 48.77 present); (c) token assurance level "
        "distribution (buckets: 0–9, 10–49, 50–99); (d) DE 48.66 TRID population rate. "
        "Mastercard will use these metrics to assess compliance with MAC Level 2 "
        "certification requirements and to identify acquirers at risk of interchange "
        "downgrade. First report due 2026-10-05 covering September 2026.", body))

    story.append(Paragraph("6. Effective Dates and JPMC Internal Deadlines", h1))
    story.append(Paragraph(
        "Network effective date for all changes in this document: <b>2026-07-01</b>. "
        "Transactions processed on or after 2026-07-01 must comply with the new message "
        "format, interchange qualification, and routing rules. JPMC internal UAT sign-off "
        "deadline: <b>2026-06-20</b> (10 business days before network effective date). "
        "Full compliance deadline (MAC Level 2 + production monitoring gate C3): "
        "<b>2026-09-30</b>. See Part 1 (MCS-2026-R3) for the full milestone table.", body))

    story.append(Paragraph("7. Normative References", h1))
    story.append(Paragraph(
        "• Mastercard Rules, April 2026 edition, Sections 5.7, 9.3<br/>"
        "• ISO 8583:2003 Financial transaction card originated messages — interchange message specifications<br/>"
        "• Mastercard Digital Enablement Service (MDES) Acquirer Implementation Guide v5.2<br/>"
        "• Mastercard BIN Table (MBT) v2026-Q2<br/>"
        "• Mastercard Settlement Services Daily Settlement Report Format Guide v2026-07<br/>"
        "• Regulation II (12 CFR Part 235) — Federal Reserve Debit Card Interchange Fee Standards<br/>"
        "• EMV Contactless Kernel C-3 (MCK) v3.1<br/>"
        "• Part 1 of this mandate: MCS-2026-R3 (Mandate Overview, Brand Rules &amp; Certification)", body))

    doc.build(story)
    return path


if __name__ == "__main__":
    p1 = make_part1()
    print(f"Created: {p1}")
    p2 = make_part2()
    print(f"Created: {p2}")
