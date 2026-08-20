# Content Team — Question Writing Template

This is the CSV format for delivering questions into the NextWise Education question bank. It maps directly onto the database schema, so a row that passes the format below imports without manual cleanup.

**Two things are still pending your/the client's confirmation and are marked below rather than guessed at:**
1. The full `nursing_system` / `topic` / `subtopic` list (see `CLIENT_QUESTIONS_taxonomy_and_weighting.md`, question 1) — don't start populating this column against a real list until that's confirmed. The example rows below use a placeholder system name for format illustration only.
2. Whether PN content is in scope for Phase 1 — the `client_needs_category` list below is **RN only**. A PN sibling list gets added once that's confirmed (see the same doc, question 2).

---

## 1. Core columns (every row, every question type)

| Column | Required | Notes |
|---|---|---|
| `question_ref` | Yes | Your own unique ID per question (e.g. `Q0001`). Used only to keep multi-row NGN content organized during review — not stored as-is in the database. |
| `question_type` | Yes | One of: `MCQ`, `SATA`, `MATRIX`, `BOWTIE`, `EMR`, `DRAG_DROP`, `CLOZE`, `HOTSPOT`, `NGN_CASE` |
| `ngn_type` | Only if `question_type=NGN_CASE` | Which of the other types this case-study item renders as, e.g. `MATRIX` |
| `stem` | Yes | The question text. For `CLOZE`, include `{{blank_1}}`, `{{blank_2}}`, etc. inline where each dropdown belongs — see §2.5. |
| `clinical_scenario` | No | Patient vignette, if separate from the stem |
| `case_study_title` | Only for `NGN_CASE` | All rows sharing a case study must use the exact same title |
| `case_study_sequence` | Only for `NGN_CASE` | Order within the case study (1, 2, 3, ...) |
| `image_filename` | No | Filename only (e.g. `lab_results_04.png`) — deliver image files separately alongside the CSV |
| `difficulty` | Yes | `EASY`, `MEDIUM`, `HARD` |
| `nursing_system` | Yes* | *Pending — see note above |
| `topic` | Yes* | *Pending |
| `subtopic` | No | |
| `client_needs_category` | Yes | See §3 — RN list only for now |
| `client_needs_subcategory` | Yes | Must belong to the category above |
| `clinical_judgment_skill` | Yes | `RECOGNIZE_CUES`, `ANALYZE_CUES`, `PRIORITIZE_HYPOTHESES`, `GENERATE_SOLUTIONS`, `TAKE_ACTION`, `EVALUATE_OUTCOMES` |
| `cognitive_level` | Yes | `REMEMBER`, `UNDERSTAND`, `APPLY`, `ANALYZE`, `EVALUATE`, `CREATE` |
| `tags` | No | Semicolon-separated, e.g. `medication safety;heart failure` |
| `rationale_correct` | Yes | Why the correct answer is correct |
| `rationale_incorrect` | No | Why the distractors are wrong |
| `reference` | No | Citation |

## 2. Type-specific columns

A flat CSV means every question type's extra data lives in a fixed set of columns on the same row, using two delimiter conventions:
- **`;` separates list items** within one cell
- **`*` prefixing an item marks it correct**

### 2.1 MCQ / SATA / EMR — answer choices

Columns `choice_1_text` .. `choice_8_text` (8 slots is enough for any current NCLEX item; leave unused ones blank) plus `choice_1_correct` .. `choice_8_correct` (`TRUE`/`FALSE`).

- MCQ: exactly one `choice_N_correct = TRUE`
- SATA / EMR: two or more

### 2.2 MATRIX — `matrix_rows`, `matrix_columns`, `matrix_correct_cells`

- `matrix_rows`: semicolon list, e.g. `Weight gain 3 lbs in 2 days;Dry cough;Blood pressure 118/76`
- `matrix_columns`: semicolon list, e.g. `Expected finding;Needs immediate follow-up`
- `matrix_correct_cells`: semicolon list of `row|column` pairs marking which column is correct for each row, e.g. `Weight gain 3 lbs in 2 days|Needs immediate follow-up;Blood pressure 118/76|Expected finding`

### 2.3 BOW-TIE — `bowtie_action_options`, `bowtie_condition_options`, `bowtie_assessment_options`

Each is a semicolon list; correct options get a `*` prefix.

Example: `bowtie_condition_options` = `*Heart failure;Pneumonia;Chronic kidney disease`

### 2.4 DRAG_DROP — `dragdrop_categories`, `dragdrop_items`

- `dragdrop_categories`: semicolon list (omit entirely for a pure ordering/sequencing item)
- `dragdrop_items`: semicolon list of `item text|target`, where target is either a category name from the list above, or a number for ordering, e.g. `Assess airway|1;Administer oxygen|2;Notify provider|3`

### 2.5 CLOZE — `cloze_blanks`

One entry per blank, semicolons between blanks, commas between that blank's options, `*` marking the correct one:

`cloze_blanks` = `blank_1:2 L/min,*4 L/min,6 L/min;blank_2:*hypoxia,hypercapnia,anemia`

Each `blank_key` (`blank_1`, `blank_2`, ...) must appear as `{{blank_1}}` etc. somewhere in `stem`.

### 2.6 HOTSPOT — `hotspot_targets`

Semicolon list of exact word/phrase spans copied from `stem` or `clinical_scenario`, correct ones `*`-prefixed:

`hotspot_targets` = `crackles bilaterally;*oxygen saturation of 88%;pain level 3/10`

This assumes text-span hotspots (click/highlight a word or phrase), not image-region clicks — flagged as an assumption in the schema notes; confirm before writing HOTSPOT content if image-coordinate hotspots are wanted instead.

## 3. Accepted `client_needs_category` values (RN, Phase 1)

Pending final confirmation, but this is the working RN list per the official NCSBN Client Needs framework:

`Management of Care`, `Safety and Infection Prevention and Control`, `Health Promotion and Maintenance`, `Psychosocial Integrity`, `Basic Care and Comfort`, `Pharmacological and Parenteral Therapies`, `Reduction of Risk Potential`, `Physiological Adaptation`

Each needs a `client_needs_subcategory` underneath it — that finer-grained list will be confirmed alongside the nursing-system taxonomy.

## 4. Example rows

**MCQ**

| question_ref | question_type | stem | difficulty | nursing_system | topic | client_needs_category | client_needs_subcategory | clinical_judgment_skill | cognitive_level | choice_1_text | choice_1_correct | choice_2_text | choice_2_correct | rationale_correct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Q0001 | MCQ | A client with heart failure reports 3 lbs weight gain in 2 days. What is the priority action? | MEDIUM | Cardiovascular *(placeholder)* | Heart Failure *(placeholder)* | Physiological Adaptation | Illness Management | TAKE_ACTION | APPLY | Notify the provider | TRUE | Restrict fluids to 500 mL/day | FALSE | Rapid weight gain indicates fluid retention and must be reported immediately. |

**SATA**

| question_ref | question_type | stem | ... | choice_1_text | choice_1_correct | choice_2_text | choice_2_correct | choice_3_text | choice_3_correct |
|---|---|---|---|---|---|---|---|---|---|
| Q0002 | SATA | Which findings indicate digoxin toxicity? (Select all that apply.) | ... | Nausea | TRUE | Yellow-green visual halos | TRUE | Hypertension | FALSE |

**BOW-TIE (NGN)**

| question_ref | question_type | stem | clinical_scenario | bowtie_action_options | bowtie_condition_options | bowtie_assessment_options |
|---|---|---|---|---|---|---|
| Q0003 | BOWTIE | Complete the bow-tie for this client. | 68-year-old with sudden dyspnea, crackles, JVD... | *Administer oxygen;Restrict fluids;Elevate legs | *Heart failure;Pneumonia;Pulmonary embolism | *Crackles bilaterally;JVD;Fever |
