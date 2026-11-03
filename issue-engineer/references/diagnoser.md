# Diagnosis when verification/fix attempts fail

- Classify the failure as: incorrect hypothesis, missing requirement, test/environment problem, dependency mismatch, implementation defect, or missing authorization.
- Cite evidence and decide whether safe local progress is possible.
- Change approach only if supporting evidence exists. Do not mask test failures or extend retries without bound.
- Escalate materially ambiguous data/security/API behavior.
- If there is no safe resolution after three review/fix cycles, keep local changes isolated and report PARTIAL/BLOCKED with exact failed commands, findings, and remaining risk.
- No background retries or recovery daemon.
