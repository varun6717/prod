<!-- si_fail.md — a deliberately BROKEN v1. Not a bad document in general: each defect below is
     aimed at exactly one G1 hard precondition, so the validator's failure report can be checked
     violation by violation rather than merely "it failed".

       sections_complete          §11 present but empty
       conditionals_dispositioned §3 says "Not applicable" with NO reason; §9 absent entirely
       gaps_declared              two `open` coverage entries, §17 lists no question
       trace_15_to_4              S2 traces to O9 (does not exist); O2 has no criterion
       trace_8_to_7               R2 names D9 (not declared); D2 has no requirement
       assertions_enumerated      R2 carries no R2.n assertions
       flags_resolved             passed in by the caller, not expressible in the document

     See README.md. The PASS counterpart is fixtures/si_author/v1.md — the real authored v1. -->

# Solution Intent — Broken Fixture

## 1. Executive summary

A deliberately malformed Solution Intent used to prove the G1 preconditions bite.

<!-- coverage: {1: source, 2: source, 3: source, 4: source} -->

## 2. Problem statement

The current mechanism is inadequate. [TBD — unsourced]

<!-- coverage: {1: open, 2: source, 3: source, 4: open} -->

## 3. Client need & demand

Not applicable

<!-- coverage: {1: source, 2: source, 3: source} -->

## 4. Business objectives

- **O1 —** Maintain compliance.
- **O2 —** Reduce interchange cost.

<!-- coverage: {1: source, 2: source, 3: source} -->

## 5. Personas & actors

Merchant, settlement operations.

<!-- coverage: {1: source, 2: source, 3: source} -->

## 6. High-level use case

Authorization flows through the router to a brand handler.

<!-- coverage: {1: source, 2: source, 3: source} -->

## 7. Deliverables

| ID | Deliverable |
|---|---|
| **D1** | Authorization message layer update |
| **D2** | Reporting changes |

<!-- coverage: {1: source, 2: source, 3: source, 4: source} -->

## 8. Business requirements

#### R1 — Token data carried on the authorization message
**Deliverable:** D1
**Description:** The message must carry the new token elements.

**Assertions:**
- R1.1 — DE 48.66 carries the Token Requestor ID.
- R1.2 — DE 48.78 carries the Token Assurance Level.

#### R2 — Reporting updated
**Deliverable:** D9
**Description:** The reports must change. No assertions are enumerated here.

<!-- coverage: {1: source, 2: source, 3: source, 4: source} -->

## 10. Constraints & design principles

Field 48 subelement capacity is fixed.

<!-- coverage: {1: source, 2: source, 3: source, 4: source} -->

## 11. Stakeholders

<!-- coverage: {1: source, 2: source, 3: source} -->

## 12. Out of scope

Visa and Discover handling.

<!-- coverage: {1: source, 2: source, 3: source, 4: source} -->

## 13. Assumptions & risks

We assume the architecture is suitable.

<!-- coverage: {1: source, 2: source, 3: source, 4: source} -->

## 14. Dependencies

Mastercard BIN Table.

<!-- coverage: {1: source, 2: source, 3: source, 4: source} -->

## 15. Success criteria

| ID | Criterion | Traces to |
|---|---|---|
| S1 | Certification held by the deadline | O1 |
| S2 | Interchange cost reduced | O9 |

<!-- coverage: {1: source, 2: source, 3: source, 4: source} -->

## 16. Derived system impacts

*Authored during enrichment (v2 only).*

## 17. Open questions

None recorded.

<!-- coverage: {1: source, 2: source, 3: source, 4: source} -->

## 18. Verification summary

*Authored during enrichment (v2 only).*
