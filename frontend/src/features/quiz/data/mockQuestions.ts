import type { Question } from "@/types/question";

/**
 * Schema-shaped sample data — mirrors Question/AnswerChoice from
 * backend/apps/questions/models.py field-for-field, so swapping this for a
 * real /api/questions/ response later is a drop-in, not a rewrite. Only
 * MCQ/SATA render interactively right now; other types below exist purely
 * to prove the "coming soon" notice renders instead of crashing.
 */
export const MOCK_QUESTIONS: Question[] = [
  {
    id: "q1",
    question_type: "MCQ",
    stem: "A client with heart failure reports a weight gain of 3 lbs over the past 2 days. What is the nurse's priority action?",
    clinical_scenario:
      "68-year-old client, 3 days post-discharge for heart failure exacerbation, presents to the outpatient clinic for a routine follow-up.",
    difficulty: "MEDIUM",
    nursing_system: "Cardiovascular",
    topic: "Heart Failure",
    nclex_client_needs_category: "Physiological Adaptation",
    clinical_judgment_skill: "Take Action",
    rationale_correct:
      "A rapid weight gain of 2-3 lbs in a day, or 5 lbs in a week, is a key indicator of fluid retention in heart failure and should be reported to the provider immediately, since it often precedes a decompensation episode.",
    rationale_incorrect:
      "Restricting fluids without provider guidance and simply documenting the finding both delay an intervention that may already be needed.",
    answer_choices: [
      { id: "q1c1", choice_text: "Notify the provider", is_correct: true, display_order: 1 },
      { id: "q1c2", choice_text: "Restrict the client's fluids to 500 mL/day", is_correct: false, display_order: 2 },
      { id: "q1c3", choice_text: "Document the finding and reassess in a week", is_correct: false, display_order: 3 },
      { id: "q1c4", choice_text: "Advise the client to elevate their legs", is_correct: false, display_order: 4 },
    ],
  },
  {
    id: "q2",
    question_type: "SATA",
    stem: "A client is prescribed digoxin. Which findings should the nurse recognize as signs of digoxin toxicity? Select all that apply.",
    clinical_scenario: null,
    difficulty: "HARD",
    nursing_system: "Pharmacology",
    topic: "Cardiac Glycosides",
    nclex_client_needs_category: "Pharmacological Therapies",
    clinical_judgment_skill: "Recognize Cues",
    rationale_correct:
      "Nausea, visual disturbances (yellow-green halos), and bradycardia are classic signs of digoxin toxicity caused by the drug's narrow therapeutic index.",
    rationale_incorrect: "Hypertension and increased appetite are not associated with digoxin toxicity.",
    answer_choices: [
      { id: "q2c1", choice_text: "Nausea", is_correct: true, display_order: 1 },
      { id: "q2c2", choice_text: "Yellow-green visual halos", is_correct: true, display_order: 2 },
      { id: "q2c3", choice_text: "Bradycardia", is_correct: true, display_order: 3 },
      { id: "q2c4", choice_text: "Hypertension", is_correct: false, display_order: 4 },
      { id: "q2c5", choice_text: "Increased appetite", is_correct: false, display_order: 5 },
    ],
  },
  {
    id: "q3",
    question_type: "MCQ",
    stem: "The nurse is caring for a client with type 1 diabetes who is diaphoretic, shaky, and reports feeling confused. Blood glucose is 52 mg/dL. What should the nurse do first?",
    clinical_scenario: null,
    difficulty: "EASY",
    nursing_system: "Endocrine",
    topic: "Diabetes Mellitus",
    nclex_client_needs_category: "Physiological Adaptation",
    clinical_judgment_skill: "Generate Solutions",
    rationale_correct:
      "A blood glucose of 52 mg/dL with symptomatic hypoglycemia requires immediate treatment with a fast-acting carbohydrate before any other action.",
    rationale_incorrect: "Rechecking in 30 minutes or calling the provider first both delay urgently needed treatment.",
    answer_choices: [
      { id: "q3c1", choice_text: "Give 15-20 g of a fast-acting carbohydrate", is_correct: true, display_order: 1 },
      { id: "q3c2", choice_text: "Recheck the blood glucose in 30 minutes", is_correct: false, display_order: 2 },
      { id: "q3c3", choice_text: "Administer the client's scheduled insulin dose", is_correct: false, display_order: 3 },
      { id: "q3c4", choice_text: "Call the provider before intervening", is_correct: false, display_order: 4 },
    ],
  },
  {
    id: "q4",
    question_type: "MATRIX",
    stem: "For each assessment finding, indicate whether it is an expected or unexpected finding in a client 2 hours post-thyroidectomy.",
    clinical_scenario: null,
    difficulty: "HARD",
    nursing_system: "Endocrine",
    topic: "Thyroid Surgery",
    nclex_client_needs_category: "Reduction of Risk Potential",
    clinical_judgment_skill: "Analyze Cues",
    rationale_correct: "",
    rationale_incorrect: null,
    answer_choices: [],
  },
];
