# Financial release policy

The staging workflow has read-only repository permissions. A successful run is not publication approval.

1. Inspect manifest, candidate, reconciliation and release-review artifacts from the same successful run.
2. Confirm the baseline SHA-256 still matches the published file and candidate SHA-256 matches the reviewed artifact.
3. Review all missing identities, additions, revisions, period types and source totals. No missing values may be substituted with zero.
4. Update current and historical datasets, crosswalk, profile clocks, reporting dates and validation expectations together. Current code contains period-specific paths and day counts; replacing only the snapshot is unsafe.
5. Submit changes for review, run foundation validation and verify the production deployment. Preserve the previous Git commit as the rollback point.
6. If validation or deployment fails, revert the release commit and verify the restored deployment.

No automatic write or deployment is enabled. A permanent public update history must be added when a release is approved; staging artifacts expire after 30 days.
