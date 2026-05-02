# Direct Evidence-Contract Prompt v1

Read the epilepsy clinic letter and emit the final extraction schema.

For every extracted field, ground it in an exact quote from the letter.
Use only text present in the letter. Do not invent missing clinical facts.
Where a field cannot be supported by the letter, omit the value and add
a warning for that field.

Return only valid JSON matching `schemas/final_extraction_v1.json`.
Populate the `citations` array with exact quotes for each supported field.
