# Anchor Retrieval Prompt v1

Extract only the current seizure-frequency label from the retrieved context passages.

The context passages were retrieved from the clinic letter using seizure-frequency
keywords. The full clinic letter follows for reference.

Return JSON with:

- `label`: normalized seizure-frequency label.
- `evidence`: exact supporting quote from the letter.
- `confidence`: number from 0 to 1.
- `warnings`: list of strings.

Do not use gold labels, references, or evaluation fields.
