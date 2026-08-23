import type { Question } from "@/types/question";

/**
 * Schema-shaped sample data — mirrors Question/AnswerChoice from
 * backend/apps/questions/models.py field-for-field, so swapping this for a
 * real /api/questions/ response later is a drop-in, not a rewrite. Only
 * MCQ/SATA render interactively right now; other types below exist purely
 * to prove the "coming soon" notice renders instead of crashing.
 *
 * rationale_correct/rationale_incorrect are left null on q1-q3 deliberately
 * — each answer_choice below carries its own `rationale` instead, shown
 * inline under that option (client-requested Aug 2026), which is what the
 * quiz UI actually renders for MCQ/SATA now.
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
    rationale_correct: null,
    rationale_incorrect: null,
    answer_choices: [
      {
        id: "q1c1",
        choice_text: "Notify the provider",
        is_correct: true,
        display_order: 1,
        rationale:
          "A rapid weight gain of 2-3 lbs in a day, or 5 lbs in a week, is a key indicator of fluid retention in heart failure and should be reported to the provider immediately, since it often precedes a decompensation episode.",
      },
      {
        id: "q1c2",
        choice_text: "Restrict the client's fluids to 500 mL/day",
        is_correct: false,
        display_order: 2,
        rationale: "Fluid restriction requires a provider order — a nurse should not independently impose one, and doing so delays notifying the provider of a finding that needs immediate attention.",
      },
      {
        id: "q1c3",
        choice_text: "Document the finding and reassess in a week",
        is_correct: false,
        display_order: 3,
        rationale: "Waiting a week delays intervention for a finding that often precedes decompensation — this weight gain needs same-day follow-up, not routine documentation.",
      },
      {
        id: "q1c4",
        choice_text: "Advise the client to elevate their legs",
        is_correct: false,
        display_order: 4,
        rationale: "Leg elevation may help with peripheral edema but does nothing for the underlying fluid retention driving the weight gain, and doesn't address the need to notify the provider.",
      },
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
    rationale_correct: null,
    rationale_incorrect: null,
    answer_choices: [
      {
        id: "q2c1",
        choice_text: "Nausea",
        is_correct: true,
        display_order: 1,
        rationale: "Gastrointestinal symptoms, especially nausea and anorexia, are among the earliest signs of digoxin toxicity.",
      },
      {
        id: "q2c2",
        choice_text: "Yellow-green visual halos",
        is_correct: true,
        display_order: 2,
        rationale: "Visual disturbances, classically yellow-green halos around lights, are a hallmark sign of digoxin toxicity caused by the drug's effect on the optic pathway.",
      },
      {
        id: "q2c3",
        choice_text: "Bradycardia",
        is_correct: true,
        display_order: 3,
        rationale: "Digoxin's therapeutic effect slows AV conduction — at toxic levels this can progress to a dangerous bradycardia or heart block.",
      },
      {
        id: "q2c4",
        choice_text: "Hypertension",
        is_correct: false,
        display_order: 4,
        rationale: "Digoxin toxicity is associated with dysrhythmias, not elevated blood pressure — hypertension isn't a recognized toxicity sign.",
      },
      {
        id: "q2c5",
        choice_text: "Increased appetite",
        is_correct: false,
        display_order: 5,
        rationale: "Toxicity causes anorexia and nausea, the opposite of increased appetite.",
      },
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
    rationale_correct: null,
    rationale_incorrect: null,
    answer_choices: [
      {
        id: "q3c1",
        choice_text: "Give 15-20 g of a fast-acting carbohydrate",
        is_correct: true,
        display_order: 1,
        rationale: "A blood glucose of 52 mg/dL with symptomatic hypoglycemia requires immediate treatment with a fast-acting carbohydrate before any other action.",
      },
      {
        id: "q3c2",
        choice_text: "Recheck the blood glucose in 30 minutes",
        is_correct: false,
        display_order: 2,
        rationale: "Rechecking without treating first delays urgently needed carbohydrate for a client who is already symptomatic.",
      },
      {
        id: "q3c3",
        choice_text: "Administer the client's scheduled insulin dose",
        is_correct: false,
        display_order: 3,
        rationale: "Giving insulin during hypoglycemia would lower blood glucose further and worsen the client's condition.",
      },
      {
        id: "q3c4",
        choice_text: "Call the provider before intervening",
        is_correct: false,
        display_order: 4,
        rationale: "Symptomatic hypoglycemia is treated immediately under standing protocol — calling the provider first delays urgently needed treatment.",
      },
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
    rationale_correct: null,
    rationale_incorrect: null,
    answer_choices: [],
  },
];
