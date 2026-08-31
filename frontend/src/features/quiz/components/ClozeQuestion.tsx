import { cn } from "@/lib/utils";
import type { ClozeBlank } from "@/types/question";

/**
 * Splits `text` on every `[blank_key]` token (the content team's authoring
 * convention — see ClozeBlank.blank_key's own backend comment) into an
 * alternating array of plain strings and the ClozeBlank each token matches,
 * so the caller can render a dropdown inline wherever a blank belongs. A
 * bracketed token with no matching blank_key (a content typo) survives as
 * literal text rather than disappearing silently.
 */
function splitOnBlanks(text: string, blanks: ClozeBlank[]): (string | ClozeBlank)[] {
  const byKey = new Map(blanks.map((b) => [b.blank_key.trim().toLowerCase(), b]));
  const parts = text.split(/(\[[^\]]+\])/g);
  return parts.map((part) => {
    const match = /^\[([^\]]+)\]$/.exec(part);
    if (!match) return part;
    const blank = byKey.get(match[1].trim().toLowerCase());
    return blank ?? part;
  });
}

export function ClozeQuestion({
  stem,
  blanks,
  selections,
  submitted,
  onSelect,
}: {
  stem: string;
  blanks: ClozeBlank[];
  selections: { blank_id: number; option_id: number }[];
  submitted: boolean;
  onSelect: (blankId: number, optionId: number) => void;
}) {
  const selectedByBlank = new Map(selections.map((s) => [s.blank_id, s.option_id]));
  const segments = splitOnBlanks(stem, blanks);

  return (
    <p className="cloze-stem">
      {segments.map((segment, index) => {
        // "s"/"b" prefixes keep string-segment and blank keys from ever
        // colliding — see HotSpotQuestion's identical fix for why a plain
        // array-index key and an id key can otherwise land on the same value.
        if (typeof segment === "string") return <span key={`s${index}`}>{segment}</span>;

        const blank = segment;
        const selectedOptionId = selectedByBlank.get(blank.id);
        const selectedOption = blank.options.find((o) => o.id === selectedOptionId);
        const isCorrect = submitted && selectedOption?.is_correct;
        const isIncorrect = submitted && selectedOption && !selectedOption.is_correct;
        const correctOption = blank.options.find((o) => o.is_correct);

        return (
          <span key={`b${blank.id}`} className="cloze-blank-wrap">
            <select
              className={cn("cloze-blank", isCorrect && "correct", isIncorrect && "incorrect")}
              value={selectedOptionId ?? ""}
              disabled={submitted}
              onChange={(e) => onSelect(blank.id, Number(e.target.value))}
            >
              <option value="" disabled>
                Choose...
              </option>
              {[...blank.options]
                .sort((a, b) => a.option_text.localeCompare(b.option_text))
                .map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.option_text}
                  </option>
                ))}
            </select>
            {submitted && isIncorrect && correctOption && (
              <span className="cloze-correction">Correct: {correctOption.option_text}</span>
            )}
          </span>
        );
      })}
    </p>
  );
}
