- Here are the synthetic payer rules for a prior authorisation demo:
  1. R1 - MRI lumbar spine: approve only if >= 6 weeks (42 days) of documented conservative therapy (physiotherapy or medication). Missing duration, therapy type, or documentation status → pending_info with outcome None. Supplied evidence that fails a condition → pending_info with outcome Needs info. R2 still takes precedence.
  2. R2 - Any red flag (history of cancer, new neurological deficit, suspected infection) → Clinician review, regardless of other rules.
  3. R3 - CT head: approve if trauma within 48 hours AND GCS documented. Missing required input → pending_info with outcome None. Otherwise an unsatisfied condition → pending_info with outcome Needs info.
  "Within 48 hours" is inclusive (0 <= trauma_hours <= 48); negative hours are
  invalid Needs info.
  4. R4 - Knee arthroscopy: approve only if >= 12 weeks (84 days) of conservative therapy AND an MRI report is attached.
  Missing required input → pending_info with outcome None. Otherwise an unsatisfied condition → pending_info with outcome Needs info.
  5. R5 - Any procedure not listed above Clinician review.
  6. R6 - The system NEVER denies. Only a clinician can deny.

  Workflow clarification: Approve and Clinician review have status completed. Needs info has status pending_info and is displayed as Needs more info. Pending clarification has status pending_info and outcome None. Explicit No/False answers and zero are supplied values, not missing inputs; known red flags always take precedence.
