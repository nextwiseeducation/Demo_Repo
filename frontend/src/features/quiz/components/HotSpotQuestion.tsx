import { cn } from "@/lib/utils";
import type { HotSpotTarget } from "@/types/question";

/**
 * Splits `text` into plain-string and HotSpotTarget segments, in the order
 * they appear — each target is matched against its exact target_text (see
 * HotSpotTarget's own backend docstring: "the student selects the correct
 * word/phrase within the question's stem or clinical_scenario"). `claimed`
 * is shared across the scenario and stem calls (both made synchronously,
 * back to back, by HotSpotQuestion below) so a target whose text happens to
 * appear in both blocks is only made clickable at its first occurrence.
 *
 * Mutates `claimed` deliberately — the two calls must run in a fixed order
 * within a single synchronous pass (never split across independently
 * re-invoked child components), otherwise React StrictMode's dev-mode
 * double-render of a child can see a `claimed` set another render pass
 * already populated and silently produce zero segments.
 */
function buildHotspotSegments(text: string, targets: HotSpotTarget[], claimed: Set<number>): (string | HotSpotTarget)[] {
  const candidates = targets
    .filter((t) => !claimed.has(t.id))
    .map((t) => ({ target: t, index: text.indexOf(t.target_text) }))
    .filter((c) => c.index !== -1)
    .sort((a, b) => a.index - b.index);

  const segments: (string | HotSpotTarget)[] = [];
  let cursor = 0;
  for (const { target, index } of candidates) {
    if (index < cursor) continue; // overlaps an already-claimed span — skip
    if (index > cursor) segments.push(text.slice(cursor, index));
    segments.push(target);
    claimed.add(target.id);
    cursor = index + target.target_text.length;
  }
  if (cursor < text.length) segments.push(text.slice(cursor));
  return segments;
}

/** Pure presentational rendering of a pre-computed segment list — no mutation, safe to re-invoke any number of times. */
function HotspotSegments({
  segments,
  className,
  selectedTargetIds,
  submitted,
  onToggle,
}: {
  segments: (string | HotSpotTarget)[];
  className: string;
  selectedTargetIds: number[];
  submitted: boolean;
  onToggle: (targetId: number) => void;
}) {
  return (
    <div className={className}>
      {segments.map((segment, index) => {
        // "s"/"t" prefixes keep string-segment and target-button keys from
        // ever colliding — plain array-index keys for one and target.id for
        // the other can otherwise land on the same value within one list.
        if (typeof segment === "string") return <span key={`s${index}`}>{segment}</span>;
        const target = segment;
        const isSelected = selectedTargetIds.includes(target.id);
        const isCorrect = submitted && target.is_correct;
        const isWrongPick = submitted && isSelected && !target.is_correct;
        return (
          <button
            key={`t${target.id}`}
            type="button"
            disabled={submitted}
            onClick={() => onToggle(target.id)}
            className={cn(
              "hotspot-target",
              !submitted && isSelected && "selected",
              isCorrect && "correct",
              isWrongPick && "incorrect",
            )}
          >
            {target.target_text}
          </button>
        );
      })}
    </div>
  );
}

export function HotSpotQuestion({
  clinicalScenario,
  stem,
  targets,
  selectedTargetIds,
  submitted,
  onToggle,
}: {
  clinicalScenario: string | null;
  stem: string;
  targets: HotSpotTarget[];
  selectedTargetIds: number[];
  submitted: boolean;
  onToggle: (targetId: number) => void;
}) {
  // Both calls happen here, synchronously, in one pass — see
  // buildHotspotSegments' own docstring on why that matters.
  const claimed = new Set<number>();
  const scenarioSegments = clinicalScenario ? buildHotspotSegments(clinicalScenario, targets, claimed) : null;
  const stemSegments = buildHotspotSegments(stem, targets, claimed);

  return (
    <div className="hotspot">
      <p className="sata-label">Select the finding(s) that require follow-up</p>
      {scenarioSegments && (
        <HotspotSegments
          segments={scenarioSegments}
          className="scenario"
          selectedTargetIds={selectedTargetIds}
          submitted={submitted}
          onToggle={onToggle}
        />
      )}
      <HotspotSegments
        segments={stemSegments}
        className="stem"
        selectedTargetIds={selectedTargetIds}
        submitted={submitted}
        onToggle={onToggle}
      />
      {submitted && (
        <div className="hotspot-rationales">
          {targets
            .filter((t) => t.rationale)
            .map((target) => (
              <p key={target.id} className="choice-rationale matrix-row-rationale">
                <span className="matrix-row-rationale-label">{target.target_text}: </span>
                {target.rationale}
              </p>
            ))}
        </div>
      )}
    </div>
  );
}
