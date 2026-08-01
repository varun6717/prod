# Mastercard Brand Implementation Mandate MCS-2026-R3 — Part 1 of 2: Mandate Overview, Brand Rules & Certification

MASTERCARD INTERNATIONAL INCORPORATED
Brand Implementation Mandate
Mandate ID: MCS-2026-R3 | Part 1 of 2: Mandate Overview, Brand Rules & Certification
Applicable Card Brand: Mastercard (incl. Maestro, Debit Mastercard)
Version: 1.2 | Status: Approved-Final | Compliance Deadline: 2026-09-30

## 1. Mandate Summary

This document is Part 1 of 2 for Mastercard brand mandate MCS-2026-R3. It covers the mandate
rationale, brand rules, and certification requirements. Part 2 of 2 (document MCS-2026-R3-T)
contains the technical implementation specification including ISO 8583 message format changes,
revised interchange fee schedules, and Banknet routing updates. Both parts must be read together
as a single binding requirement.
Mandate MCS-2026-R3 is issued by Mastercard International Incorporated under authority of the
Mastercard Rules and the Mastercard Security Rules and Procedures and is binding on all
Mastercard-licensed acquirers, including JPMC Merchant Services. This mandate requires
acquirers to update their processing systems to support Mastercard Digital Enablement Service
(MDES) token-based transactions, revised interchange qualification criteria, and enhanced
Banknet routing logic for Debit Mastercard and Maestro products. Full compliance is required by
2026-09-30. This mandate supersedes circular MCS-2024-R7 in all matters relating to MDES token
routing and interchange qualification.

## 2. Scope and Affected Card Brands

This mandate applies to all transactions bearing the following Mastercard card brand identifiers
processed through JPMC Merchant Services acquiring infrastructure:
- Mastercard Credit — all tiers (Standard, World, World Elite, Corporate)
- Debit Mastercard — US and international debit products
- Maestro — PIN debit, international card-present
- Mastercard Commercial — purchasing, fleet, and business cards
Prepaid Mastercard products are excluded from MDES token requirements but remain subject to
interchange and routing changes in Part 2 of this mandate.
BIN ranges in scope: 510000–559999 (Mastercard Credit/Debit), 600000–699999 (Maestro). Token
BIN ranges 520000–529999 are specifically in scope for MDES token processing requirements.
Transactions with primary account numbers outside these ranges and not presenting an MDES
token are not affected by this mandate.

## 3. Brand Rules and Operational Constraints

### 3.1 MDES Token Handling

Brand rule BR-01: Acquirers MUST NOT de-tokenize MDES tokens prior to forwarding authorization
requests to Mastercard Banknet. De-tokenization is the exclusive responsibility of the Mastercard
Digital Enablement Service and occurs at the Banknet gateway. Acquirer systems that strip or
substitute token values will receive authorization declines with Response Code 14 ('Invalid card
number') from the issuer.
Brand rule BR-02: Token Requestor IDs (TRIDs) must be preserved in DE 48.66 through the full
authorization chain. The TRID identifies the wallet or device that initiated the token-based
transaction and is required for Mastercard's fraud analytics platform. Acquirers sourcing from mobile
wallets (Apple Pay, Google Pay, Samsung Pay) MUST populate DE 48.66 and DE 48.77 (wallet
indicator) as specified in Part 2.

### 3.2 Cardholder Verification Rules

Brand rule BR-03: For Mastercard contactless transactions above USD 100.00, the terminal MUST
request CVM results per EMV Contactless Kernel C-3 (Mastercard Contactless Kernel, MCK).
Acceptable CVM methods in priority order: (1) Online PIN, (2) Offline Enciphered PIN, (3) Signature.
No CVM ('NOCVM') is permitted for transit and toll MCCs only (MCCs 4111, 4121, 4131, 7523).
CVM result must appear in DE 55 Tag 9F34 (CVM Results).

### 3.3 Authorization Timeout and Fallback

Brand rule BR-04: If the primary Banknet authorization endpoint does not respond within 4000ms,
acquirer systems MAY attempt the secondary Banknet endpoint. The fallback attempt MUST be
logged with reason code T (timeout) in the transaction audit record. Stand-in processing (STIP) is
available for issuers that have enrolled in Mastercard STIP; acquirers MUST forward the
authorization to STIP on secondary endpoint timeout rather than declining the transaction at the
acquiring host.

### 3.4 Decline Reason Code Updates

Brand rule BR-05: Response Code 55 returned for MDES token transactions now indicates 'Token
Assurance Level insufficient' rather than its legacy meaning of 'Incorrect PIN'. Acquirer host systems
and merchant-facing decline reason engines MUST be updated to display 'Unable to process —
please retry with chip card' for MC Response Code 55 on token transactions (identifiable by MDES
token BIN range 520000–529999). Failure to distinguish this code will cause incorrect merchant
messaging and consumer friction that Mastercard monitors via dispute rate metrics.

## 4. Certification and Conformance Requirements

All acquirers subject to MCS-2026-R3 MUST obtain Mastercard Acquirer Certification (MAC)
Level 2 for MDES token processing before the compliance deadline. Certification is administered by
the Mastercard Certification Authority (MCA) via the Mastercard Connect portal. The certification
process has three gates:
Gate C1 — Functional Test Suite: Acquirer runs the Mastercard Test Suite (MTS) v8.4 test scripts
against a UAT environment connected to the Mastercard Simulator. Required pass rate: 100% of
Category A (mandatory) test cases, 85% of Category B (conditional) test cases. MTS v8.4 test
scripts are available on Mastercard Connect under 'Certification > MDES Token > Acquirer Suite'.
Estimated duration: 4 weeks.
Gate C2 — Interoperability Testing: Acquirer submits 1,000 end-to-end transaction traces
including MDES token transactions (minimum 300), fallback chip transactions (minimum 100), and
Regulation II debit routing samples (minimum 50). Traces must be submitted via the Mastercard
Testing API in JSONL format as specified in the MTS Integration Guide v8.4 Appendix D.
Gate C3 — Production Validation: 60-day post-certification production monitoring period.
Mastercard monitors token decline rates, TRID population rates, and DE 48.77 coverage via
Mastercard Settlement Services data feeds. Any metric exceeding the alert threshold triggers a
mandatory remediation review within 5 business days. MAC Level 2 is revoked if remediation is not
completed within 30 calendar days.
Acquirers that do not achieve MAC Level 2 by 2026-09-30 will have all Mastercard and Maestro
transactions automatically downgraded to the Standard non-qualified interchange tier and will be
placed on a 90-day remediation plan per Mastercard Rules Section 9.3.2.

## 5. Compliance Deadline and Milestones

Milestone
Target Date
Owner
MTS v8.4 test harness provisioned
2026-04-15
JPMC Merchant Tech
Gate C1 functional tests complete
2026-06-15
JPMC QA
Gate C2 interoperability submission
2026-07-31
JPMC + MCA
Production deployment (UAT → PROD)
2026-09-01
JPMC Ops
Gate C3 monitoring period begins
2026-09-01
MCA
COMPLIANCE DEADLINE (MCS-2026-R3)
2026-09-30
All parties

## 6. Normative References

- Mastercard Rules, April 2026 edition, Section 9.3
- Mastercard Security Rules and Procedures v2026-Q1
- Mastercard Digital Enablement Service (MDES) Acquirer Implementation Guide v5.2
- Mastercard Test Suite (MTS) v8.4 Acquirer Script Package
- EMV Contactless Kernel C-3 (Mastercard Contactless Kernel) v3.1
- Prior mandate: MCS-2024-R7 (superseded by this document)
- Part 2 of this mandate: MCS-2026-R3-T (Technical Specification)
