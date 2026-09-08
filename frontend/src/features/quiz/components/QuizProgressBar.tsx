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
    <div className="flex-1 min-w-0">
      <div className="progress-row">
        <span className="shrink-0 whitespace-nowrap">
          Question {currentIndex + 1} of {total}
        </span>
        <span className="min-w-0 truncate">
          {question.nursing_system} · {DIFFICULTY_LABELS[question.difficulty]}
        </span>
      </div>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${((currentIndex + 1) / total) * 100}%` }} />
      </div>
    </div>
  );
}
