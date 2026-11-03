# Fixer instructions

- Read each reviewer finding and verify it against current code before changing anything.
- Prioritize `introduced` critical/high/medium defects, then acceptance-criteria gaps.
- Reject false positives with concise evidence. Do not chase `pre_existing` or `unrelated` defects without need.
- Make the smallest safe fix consistent with repository practices; update regression tests where appropriate.
- Run targeted checks and collect actual exit codes.
- Re-run the separate reviewer (`scripts/review_once.sh`) on the new diff, up to three total correction cycles.
- When there is no progress, or the same issue persists twice, apply the diagnoser guidance.
- Do not claim PASS unless the external reviewer explicitly issued PASS and relevant tests passed. Document unresolved findings in the final issue comment.
- Never push, deploy, merge, or close the issue.
