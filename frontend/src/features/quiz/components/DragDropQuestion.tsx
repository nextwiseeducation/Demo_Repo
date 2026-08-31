import { Check, GripVertical, X } from "lucide-react";
import { useState } from "react";

import { cn } from "@/lib/utils";
import type { DragDropCategory, DragDropItem } from "@/types/question";

export interface DragDropPlacement {
  item_id: number;
  category_id: number | null;
  order: number | null;
}

/**
 * Covers both DragDropItem variants (see its own backend docstring): a
 * question is a "sort into categories" question if it has any categories at
 * all, otherwise it's a "put these in order" question — the same signal the
 * backend's grade_dragdrop uses (item.correct_category_id vs correct_order).
 */
export function DragDropQuestion({
  items,
  categories,
  placements,
  submitted,
  onChange,
}: {
  items: DragDropItem[];
  categories: DragDropCategory[];
  placements: DragDropPlacement[];
  submitted: boolean;
  onChange: (placements: DragDropPlacement[]) => void;
}) {
  if (categories.length > 0) {
    return (
      <CategoryDragDrop items={items} categories={categories} placements={placements} submitted={submitted} onChange={onChange} />
    );
  }
  return <SequenceDragDrop items={items} placements={placements} submitted={submitted} onChange={onChange} />;
}

function SequenceDragDrop({
  items,
  placements,
  submitted,
  onChange,
}: {
  items: DragDropItem[];
  placements: DragDropPlacement[];
  submitted: boolean;
  onChange: (placements: DragDropPlacement[]) => void;
}) {
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const orderById = new Map(placements.map((p) => [p.item_id, p.order]));
  const ordered = [...items].sort((a, b) => {
    const orderA = orderById.get(a.id) ?? a.display_order;
    const orderB = orderById.get(b.id) ?? b.display_order;
    return orderA - orderB;
  });

  function commit(nextOrdered: DragDropItem[]) {
    onChange(nextOrdered.map((item, index) => ({ item_id: item.id, category_id: null, order: index + 1 })));
  }

  function move(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= ordered.length) return;
    const next = [...ordered];
    [next[index], next[target]] = [next[target], next[index]];
    commit(next);
  }

  return (
    <div className="dragdrop">
      <p className="sata-label">Drag to put these in priority order</p>
      <ol className="dragdrop-sequence">
        {ordered.map((item, index) => {
          const isCorrect = submitted && item.correct_order === index + 1;
          const isIncorrect = submitted && item.correct_order !== undefined && item.correct_order !== index + 1;
          return (
            <li
              key={item.id}
              draggable={!submitted}
              onDragStart={() => setDragIndex(index)}
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => {
                if (dragIndex === null || dragIndex === index) return;
                const next = [...ordered];
                const [moved] = next.splice(dragIndex, 1);
                next.splice(index, 0, moved);
                commit(next);
                setDragIndex(null);
              }}
              className={cn("dragdrop-item", isCorrect && "correct", isIncorrect && "incorrect")}
            >
              <span className="dragdrop-handle">
                <GripVertical className="h-4 w-4" />
              </span>
              <span className="dragdrop-order-num">{index + 1}</span>
              <span style={{ flex: 1 }}>{item.text}</span>
              {isCorrect && (
                <span className="mk ok">
                  <Check className="h-3 w-3" />
                </span>
              )}
              {isIncorrect && (
                <span className="mk no">
                  <X className="h-3 w-3" />
                </span>
              )}
              {!submitted && (
                <span className="dragdrop-arrows">
                  <button type="button" aria-label="Move up" disabled={index === 0} onClick={() => move(index, -1)}>
                    ▲
                  </button>
                  <button
                    type="button"
                    aria-label="Move down"
                    disabled={index === ordered.length - 1}
                    onClick={() => move(index, 1)}
                  >
                    ▼
                  </button>
                </span>
              )}
            </li>
          );
        })}
      </ol>
      {submitted && (
        <div className="dragdrop-rationales">
          {ordered.map(
            (item) =>
              item.rationale && (
                <p key={item.id} className="choice-rationale matrix-row-rationale">
                  <span className="matrix-row-rationale-label">
                    #{item.correct_order} {item.text}:{" "}
                  </span>
                  {item.rationale}
                </p>
              ),
          )}
        </div>
      )}
    </div>
  );
}

function CategoryDragDrop({
  items,
  categories,
  placements,
  submitted,
  onChange,
}: {
  items: DragDropItem[];
  categories: DragDropCategory[];
  placements: DragDropPlacement[];
  submitted: boolean;
  onChange: (placements: DragDropPlacement[]) => void;
}) {
  const [armedItemId, setArmedItemId] = useState<number | null>(null);
  const categoryByItem = new Map(placements.map((p) => [p.item_id, p.category_id]));
  const unplaced = items.filter((item) => categoryByItem.get(item.id) == null);

  function place(itemId: number, categoryId: number | null) {
    const next = placements.filter((p) => p.item_id !== itemId);
    next.push({ item_id: itemId, category_id: categoryId, order: null });
    onChange(next);
    setArmedItemId(null);
  }

  return (
    <div className="dragdrop">
      <p className="sata-label">Drag each item into the category it belongs to</p>

      {(!submitted || unplaced.length > 0) && (
        <div className="dragdrop-pool">
          {unplaced.length === 0 && <span className="dragdrop-pool-empty">All items placed</span>}
          {unplaced.map((item) => {
            // Once submitted, an item left here was simply never placed —
            // that's always wrong (it can't match its correct category by
            // sitting outside every category), so it renders the same
            // "incorrect" treatment the placed chips use below.
            const isIncorrect = submitted && item.correct_category_id !== undefined;
            return (
              <button
                key={item.id}
                type="button"
                disabled={submitted}
                draggable={!submitted}
                onDragStart={(e) => e.dataTransfer.setData("text/plain", String(item.id))}
                onClick={() => !submitted && setArmedItemId(item.id === armedItemId ? null : item.id)}
                className={cn("dragdrop-chip", armedItemId === item.id && "armed", isIncorrect && "incorrect")}
              >
                {item.text}
                {isIncorrect && (
                  <span className="mk no">
                    <X className="h-3 w-3" />
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      <div className="dragdrop-categories">
        {categories.map((category) => {
          const placed = items.filter((item) => categoryByItem.get(item.id) === category.id);
          return (
            <div
              key={category.id}
              className="dragdrop-category"
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                const itemId = Number(e.dataTransfer.getData("text/plain"));
                if (itemId) place(itemId, category.id);
              }}
              onClick={() => armedItemId !== null && place(armedItemId, category.id)}
            >
              <span className="dragdrop-category-label">{category.name}</span>
              <div className="dragdrop-category-items">
                {placed.map((item) => {
                  const isCorrect = submitted && item.correct_category_id === category.id;
                  const isIncorrect = submitted && item.correct_category_id !== undefined && item.correct_category_id !== category.id;
                  return (
                    <span key={item.id} className={cn("dragdrop-chip placed", isCorrect && "correct", isIncorrect && "incorrect")}>
                      {item.text}
                      {isCorrect && (
                        <span className="mk ok">
                          <Check className="h-3 w-3" />
                        </span>
                      )}
                      {isIncorrect && (
                        <span className="mk no">
                          <X className="h-3 w-3" />
                        </span>
                      )}
                      {!submitted && (
                        <button
                          type="button"
                          aria-label={`Remove ${item.text}`}
                          className="dragdrop-chip-remove"
                          onClick={(e) => {
                            e.stopPropagation();
                            place(item.id, null);
                          }}
                        >
                          ×
                        </button>
                      )}
                    </span>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {submitted && (
        <div className="dragdrop-rationales">
          {items.map(
            (item) =>
              item.rationale && (
                <p key={item.id} className="choice-rationale matrix-row-rationale">
                  <span className="matrix-row-rationale-label">{item.text}: </span>
                  {item.rationale}
                </p>
              ),
          )}
        </div>
      )}
    </div>
  );
}
