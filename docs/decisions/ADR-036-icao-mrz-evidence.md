# ADR-036: ICAO MRZ structural evidence

Status: Accepted

The OCR adapter emits versioned structural MRZ evidence for TD1, TD2 and TD3.
Checksum validation and field provenance are independent of document
classification, authenticity, country policy and business decisions. Valid MRZ
fields may replace OCR heuristics; invalid or unsupported evidence remains
explicit and cannot overwrite fields as trusted evidence.

Provenance refers to normalized OCR character positions and persists inside the
existing encrypted extraction/provider evidence. Public result projections expose
only fixed redacted issue codes. No endpoint or public SDK contract changes.
Century interpretation and country/age/expiry policy build on this evidence as
separate, versioned signals; MRZ dates retain their original YYMMDD encoding.
