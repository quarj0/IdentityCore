# Retention hold ownership

A verification-specific hold must share its verification's tenant. Model creation
and saves validate this relation; a tenant-wide hold has no verification. Raw SQL,
QuerySet updates and bulk insertion bypass model validation and are restricted to
trusted maintenance. There is no cross-table database constraint.

The media-retention guard conservatively honors an active verification-specific
hold even if an invalid legacy tenant association exists. Operators must inspect
such legacy associations and establish the authorized tenant before repair; the
service does not silently move a hold or release it. Invalid associations must be
corrected before normal model saves, including release. Keep tenant-wide holds
restricted to the matching tenant. Legal authority, expiry and release procedures
remain deployment responsibilities.
