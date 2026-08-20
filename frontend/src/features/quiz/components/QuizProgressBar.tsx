import { Progress } from "@/components/ui/progress";

export function QuizProgressBar({ currentIndex, total }: { currentIndex: number; total: number }) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          Question {currentIndex + 1} of {total}
        </span>
      </div>
      <Progress value={((currentIndex + 1) / total) * 100} />
    </div>
  );
}
