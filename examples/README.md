# Example

`sample-result.xlsx` is the output format from a run against a **fictional** ticket:

> **SHOP-142: Bulk coupon grant from CSV.** Admins import a CSV of customer IDs, filter by account status and tags, and grant store credit or free-shipping vouchers to every match. The limit is 3,000 rows. Per the RD comment of 2026-09-15, an oversized file is rejected whole, not truncated.

The ticket, IDs, numbers and defects are made up. They show the shape of a real result: 55 cases across permissions, CSV import, limits, filters, validation, submit, grant history, results, API and i18n, with ten defects and findings and seven open questions. One grant was actually submitted after the user confirmed it; every other case that writes data is Not Run.

Things to look at:

- **Test Cases → Source**: TC-15 cites an RD comment, not the AC body. That is the kind of rule a description-only read misses.
- **Result** uses five values: Pass, Fail, Needs Review, Blocked, Not Run. Blocked and Not Run always say why.
- **Defects & Findings → F-08**: the sample CSV attached to the ticket can't be imported and contains personal data. The finding reports counts only.
- **Summary** counts are formulas, so they update when you change a Result.
