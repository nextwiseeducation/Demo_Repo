import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { OptionRowActions, reorder } from "@/features/admin/components/builders/OptionRowActions";
import { RationaleField } from "@/features/admin/components/builders/RationaleField";
import { nextDraftKey, type DragDropCategoryDraft, type DragDropItemDraft } from "@/types/admin";

interface DragDropBuilderProps {
  categories: DragDropCategoryDraft[];
  items: DragDropItemDraft[];
  onCategoriesChange: (categories: DragDropCategoryDraft[]) => void;
  onItemsChange: (items: DragDropItemDraft[]) => void;
}

const NO_CATEGORY = "__none__";

/**
 * One component for both variants. The variant is DERIVED from whether any
 * categories exist — never a separately chosen mode — matching exactly the
 * rule the backend (apps.questions.authoring) and the student-facing
 * renderer both use, so the three can never disagree about which variant a
 * question is.
 */
export function DragDropBuilder({ categories, items, onCategoriesChange, onItemsChange }: DragDropBuilderProps) {
  const isCategoryVariant = categories.length > 0;

  function addCategory() {
    onCategoriesChange([...categories, { key: nextDraftKey(), name: "", display_order: categories.length }]);
  }

  function updateCategory(index: number, patch: Partial<DragDropCategoryDraft>) {
    onCategoriesChange(categories.map((c, i) => (i === index ? { ...c, ...patch } : c)));
  }

  function removeCategory(index: number) {
    const removedKey = categories[index].key;
    onCategoriesChange(categories.filter((_, i) => i !== index).map((c, i) => ({ ...c, display_order: i })));
    onItemsChange(
      items.map((item) => (item.correct_category_key === removedKey ? { ...item, correct_category_key: null } : item)),
    );
  }

  function switchToSequencing() {
    onCategoriesChange([]);
    onItemsChange(items.map((item, i) => ({ ...item, correct_category_key: null, correct_order: i + 1 })));
  }

  function switchToCategories() {
    onItemsChange(items.map((item) => ({ ...item, correct_order: null })));
    addCategory();
  }

  function addItem() {
    onItemsChange([
      ...items,
      {
        text: "",
        display_order: items.length,
        correct_category_key: null,
        correct_order: isCategoryVariant ? null : items.length + 1,
        rationale: "",
      },
    ]);
  }

  function updateItem(index: number, patch: Partial<DragDropItemDraft>) {
    onItemsChange(items.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  }

  function removeItem(index: number) {
    const next = items.filter((_, i) => i !== index).map((item, i) => ({ ...item, display_order: i }));
    onItemsChange(isCategoryVariant ? next : next.map((item, i) => ({ ...item, correct_order: i + 1 })));
  }

  function moveItem(index: number, delta: number) {
    const next = reorder(items, index, delta);
    onItemsChange(isCategoryVariant ? next : next.map((item, i) => ({ ...item, correct_order: i + 1 })));
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-foreground">Variant:</span>
        <Button variant={isCategoryVariant ? "default" : "outline"} size="sm" onClick={switchToCategories}>
          Sort into categories
        </Button>
        <Button variant={!isCategoryVariant ? "default" : "outline"} size="sm" onClick={switchToSequencing}>
          Put in order
        </Button>
      </div>

      {isCategoryVariant ? (
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-foreground">Categories</span>
            <Button variant="outline" size="sm" onClick={addCategory}>
              <Plus className="h-4 w-4" />
              Add category
            </Button>
          </div>
          {categories.map((category, index) => (
            <div key={category.key} className="flex items-center gap-2">
              <Input
                value={category.name}
                onChange={(e) => updateCategory(index, { name: e.target.value })}
                placeholder={`Category ${index + 1}`}
                className="flex-1"
              />
              <OptionRowActions onDelete={() => removeCategory(index)} />
            </div>
          ))}
        </div>
      ) : null}

      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-foreground">Items</span>
          <Button variant="outline" size="sm" onClick={addItem}>
            <Plus className="h-4 w-4" />
            Add item
          </Button>
        </div>
        {items.map((item, index) => (
          <div key={index} className="flex flex-col gap-2 rounded-lg border border-border p-3">
            <div className="flex items-center gap-2">
              {!isCategoryVariant ? (
                <span className="w-6 text-center text-sm text-muted-foreground">{item.correct_order}</span>
              ) : null}
              <Input
                value={item.text}
                onChange={(e) => updateItem(index, { text: e.target.value })}
                placeholder={`Item ${index + 1}`}
                className="flex-1"
              />
              {isCategoryVariant ? (
                <Select
                  value={item.correct_category_key ?? NO_CATEGORY}
                  onValueChange={(value) => updateItem(index, { correct_category_key: value === NO_CATEGORY ? null : value })}
                >
                  <SelectTrigger className="w-44">
                    <SelectValue>
                      {(value: string) => categories.find((c) => c.key === value)?.name || "Choose category"}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={NO_CATEGORY}>Choose category</SelectItem>
                    {categories.map((c) => (
                      <SelectItem key={c.key} value={c.key}>
                        {c.name || "(unnamed)"}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : null}
              <OptionRowActions
                onMoveUp={!isCategoryVariant ? () => moveItem(index, -1) : undefined}
                onMoveDown={!isCategoryVariant ? () => moveItem(index, 1) : undefined}
                onDelete={() => removeItem(index)}
                canMoveUp={index > 0}
                canMoveDown={index < items.length - 1}
              />
            </div>
            <RationaleField value={item.rationale} onChange={(v) => updateItem(index, { rationale: v })} />
          </div>
        ))}
      </div>
    </div>
  );
}
