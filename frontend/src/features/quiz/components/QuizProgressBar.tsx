import { DIFFICULTY_LABELS, type Question } from "@/types/question";

export function QuizProgressBar({
  currentIndex,
  total,
  question,
}: {
  currentIndex: number;
  total: number;
  question: Question;
}) {
  return (
    <div>
      <div className="progress-row">
        <span>
          Question {currentIndex + 1} of {total}
        </span>
        <span>
          {question.nursing_system} · {DIFFICULTY_LABELS[question.difficulty]}
        </span>
      </div>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${((currentIndex + 1) / total) * 100}%` }} />
      </div>
    </div>
  );
}
