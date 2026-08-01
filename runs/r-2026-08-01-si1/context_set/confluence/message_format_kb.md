# Brand Message Formats — Reference

This knowledge-base page documents the wire/message formats the Merchant Routing Service uses per
card brand. Reference material; not a change request.

## Message format

Mastercard uses ISO 8583 (1987) with brand-specific field 48 usage; Discover uses its own field
layout. Field-level mappings are maintained in the format registry.

## Brand rules

Each brand imposes operational rules on the message contract — mandatory fields, allowed values,
and certification constraints — that the format layer enforces before dispatch.
