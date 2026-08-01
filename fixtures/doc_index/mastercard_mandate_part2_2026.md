# Mastercard Brand Implementation Mandate MCS-2026-R3-T Part 2 of 2

MASTERCARD INTERNATIONAL INCORPORATED

**Technical Implementation Specification**

Mandate ID: **MCS-2026-R3-T**  |  Part **2 of 2**: Message Formats, Interchange & Routing

Applicable Card Brand: **Mastercard** (incl. Maestro, Debit Mastercard)

Version: 1.2  |  Status: Approved-Final  |  **Network Effective Date: 2026-07-01**  |  **Compliance
Deadline: 2026-09-30**

---

## 1. Introduction

This document is Part 2 of 2 for Mastercard mandate MCS-2026-R3 and contains the normative technical
specification. Read in conjunction with Part 1 (MCS-2026-R3), which covers mandate overview, brand
rules, and certification. The changes in this document are effective on the **Mastercard** network
as of **2026-07-01**; JPMC internal compliance deadline is **2026-09-30**.

## 2. ISO 8583 Message Format Changes

### 2.1 New Data Elements

The following new data elements are introduced in ISO 8583:2003 authorization (MTI 0100/0110) and
financial request (MTI 0200/0210) messages for **Mastercard** transactions effective 2026-07-01:

| DE | Field Name | Type/Length | Presence | Description |
|---|---|---|---|---|
| DE 48.66 | Token Requestor ID | N-11 | Conditional | TRID assigned by MDES to the wallet/device. Required when DE 2 is an MDES token (BIN 520000–529999). Must be preserved end-to-end; do not strip. |
| DE 48.77 | Digital Wallet Indicator | AN-2 | Conditional | Wallet type: 01=Apple Pay, 02=Google Pay, 03=Samsung Pay, 04=Masterpass, 05=Other. Required when payment originated from a digital wallet. |
| DE 48.78 | Token Assurance Level | N-2 | Conditional | Integer 00–99 from MDES vault indicating strength of token binding. Required when DE 2 is an MDES token. Value below 10 will trigger RC 55 from issuer. |
| DE 48.79 | Device Type | AN-2 | Optional | 00=POS terminal, 01=Mobile handset, 02=Wearable, 03=IoT device, 04=Browser. Informational; used for Mastercard fraud scoring. |

### 2.2 Modified Data Elements

| DE | Field Name | Change | Detail |
|---|---|---|---|
| DE 61.8 | POS Environment | Value extended | Bit 3: value '3' now = Soft POS (COTS device running certified payment app). Previously undefined. Implementors must not reject bit 3 = '3'. |
| DE 104 | Transaction Description | Length + encoding | Max length: 25 → 40 bytes. Encoding: ASCII → UTF-8. Truncate at 40 bytes (not characters) to avoid splitting multi-byte sequences. |
| DE 55 | ICC System-Related Data | New mandatory tag | EMV tag 9F6E (Enhanced Contactless Reader Capabilities, 4 bytes) is now mandatory for all contactless transactions above USD 50. Absence causes decline RC 96 from Banknet gateway. |
| DE 48.10 | Mastercard Assigned ID | Scope extended | Now also required on Maestro transactions in EU/EEA region. Previously Mastercard Credit only. |

## 3. Interchange Fee Schedule

### 3.1 Revised Consumer Credit Tiers (effective 2026-07-01)

Interchange fees are remitted acquirer-to-issuer via the Mastercard Interchange System (MIS).
MCS-2026-R3 restructures consumer credit tiers to reflect MDES token presence and enhanced
contactless eligibility. The 'Token Enhanced' column applies when DE 48.78 Token Assurance Level ≥
50:

| Product | Transaction Type | Standard Rate | Token Enhanced Rate | Effective |
|---|---|---|---|---|
| MC World Elite | Card-Present | 2.10% + $0.10 | 1.95% + $0.10 | 2026-07-01 |
| MC World Elite | Card-Not-Present | 2.40% + $0.10 | 2.15% + $0.10 | 2026-07-01 |
| MC World | Card-Present | 1.90% + $0.10 | 1.75% + $0.10 | 2026-07-01 |
| MC World | Card-Not-Present | 2.20% + $0.10 | 1.95% + $0.10 | 2026-07-01 |
| MC Standard | Card-Present | 1.65% + $0.15 | 1.65% + $0.15 | 2026-07-01 |
| MC Standard | Card-Not-Present | 1.85% + $0.15 | 1.85% + $0.15 | 2026-07-01 |
| Debit MC | PIN Debit | 0.05% + $0.21 | 0.05% + $0.21 | 2026-07-01 |
| Maestro | PIN Debit | 0.05% + $0.21 | 0.05% + $0.21 | 2026-07-01 |

Acquirers MUST update interchange qualification logic to populate DE 48.78 where applicable so that
eligible token transactions receive the reduced 'Token Enhanced' rate. Failure to populate DE 48.78
will result in Standard rate assessment regardless of actual token assurance. Retroactive
interchange adjustments are not processed.

## 4. Transaction Routing Rules

### 4.1 Banknet Endpoint Selection

Routing to Mastercard Banknet uses the BIN-first lookup in Mastercard BIN Table (MBT) v2026-Q2. The
routing handler MUST: (1) extract the 6-digit BIN from DE 2; (2) resolve to network ID and product
type in MBT; (3) select the Banknet authorization endpoint (primary or STIP) based on product type
and Regulation II routing preference. Routing decisions MUST be immutable once made —
mid-transaction re-routing is prohibited except on documented primary-endpoint timeout (≥ 4000ms).
The selected network ID and reason code must be written to the transaction audit record within 200ms
of routing decision.

### 4.2 Regulation II (Durbin) Routing for Debit Mastercard

US Debit Mastercard and Maestro transactions are subject to Regulation II (Durbin Amendment, 12 CFR
Part 235). JPMC MUST ensure: (a) at least two unaffiliated networks are available for PIN debit; (b)
the routing selection logic evaluates merchant preference (terminal flag), issuer routing preference
(DE 55 ICC data), and cost optimization (interchange tier) in that priority order; (c) no routing
exclusivity arrangement that limits merchant choice is implemented. The routing decision rationale
must be preserved in the audit ledger for Federal Reserve examination (minimum 3-year retention).

### 4.3 MDES Token Routing

Transactions presenting MDES tokens (BIN 520000–529999 in DE 2) MUST be routed exclusively to the
Mastercard Banknet MDES gateway (endpoint ID MCB-MDES-01). These transactions MUST NOT be routed to
acquirer-side processing or alternate debit networks. The MDES gateway performs de-tokenization and
forwards the real PAN to the issuer. Any routing path that bypasses MCB-MDES-01 for token BIN ranges
will result in a hard decline with Response Code 58 ('Transaction not permitted to terminal').

## 5. Reporting and Downstream Data Obligations

### 5.1 Daily Settlement Report (DSR) Format Changes

Effective 2026-07-01, the DSR submitted to Mastercard Settlement Services by 06:00 UTC must use the
new format: (a) Product Code field extended from 2 to 4 characters using MBT v2026-Q2 codes; (b) a
new 'Token Flag' column (Y/N) based on DE 48.77 presence; (c) wallet-type breakdown sub-section
required when any token transactions are present in the batch (DE 48.77 codes 01–05 each reported
separately). DSR files failing format validation will be rejected and the batch placed on settlement
hold pending resubmission.

### 5.2 Regulation II Quarterly Compliance Report

Quarterly Regulation II compliance reports are due to Mastercard Compliance by the 15th of the month
following each quarter end (Apr 15, Jul 15, Oct 15, Jan 15). Required fields: transaction count and
interchange paid by network, routing override count with justification codes, and a certification
statement from the acquirer's Chief Compliance Officer. Reports are filed via Mastercard Connect →
Compliance → Reg II Quarterly Filing. These reports feed Mastercard's downstream analytics platform
and are subject to Federal Reserve audit.

### 5.3 MDES Token Coverage Reporting

Monthly MDES token coverage reports must be submitted by the 5th of each month for the prior month.
The report must include: (a) total transaction count; (b) token transaction count (DE 48.77
present); (c) token assurance level distribution (buckets: 0–9, 10–49, 50–99); (d) DE 48.66 TRID
population rate. Mastercard will use these metrics to assess compliance with MAC Level 2
certification requirements and to identify acquirers at risk of interchange downgrade. First report
due 2026-10-05 covering September 2026.

## 6. Effective Dates and JPMC Internal Deadlines

Network effective date for all changes in this document: **2026-07-01**. Transactions processed on
or after 2026-07-01 must comply with the new message format, interchange qualification, and routing
rules. JPMC internal UAT sign-off deadline: **2026-06-20** (10 business days before network
effective date). Full compliance deadline (MAC Level 2 + production monitoring gate C3):
**2026-09-30**. See Part 1 (MCS-2026-R3) for the full milestone table.

## 7. Normative References

• Mastercard Rules, April 2026 edition, Sections 5.7, 9.3
• ISO 8583:2003 Financial transaction card originated messages — interchange message specifications
• Mastercard Digital Enablement Service (MDES) Acquirer Implementation Guide v5.2
• Mastercard BIN Table (MBT) v2026-Q2
• Mastercard Settlement Services Daily Settlement Report Format Guide v2026-07
• Regulation II (12 CFR Part 235) — Federal Reserve Debit Card Interchange Fee Standards
• EMV Contactless Kernel C-3 (MCK) v3.1
• Part 1 of this mandate: MCS-2026-R3 (Mandate Overview, Brand Rules & Certification)
