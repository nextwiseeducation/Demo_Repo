import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useTaxonomyOptions } from "@/features/admin/hooks/useTaxonomyOptions";
import {
  CLINICAL_JUDGMENT_SKILL_LABELS,
  DIFFICULTY_LABELS,
  type AdminQuestionFilters,
} from "@/types/admin";
import { QUESTION_TYPE_LABELS, SUPPORTED_QUESTION_TYPES, type QuestionType } from "@/types/question";

const ALL_VALUE = "__all__";

const QUESTION_TYPE_SELECT_LABELS: Record<string, string> = {
  [ALL_VALUE]: "All types",
  ...QUESTION_TYPE_LABELS,
};

const DIFFICULTY_SELECT_LABELS: Record<string, string> = {
  [ALL_VALUE]: "All difficulties",
  ...DIFFICULTY_LABELS,
};

const STATUS_SELECT_LABELS: Record<string, string> = {
  [ALL_VALUE]: "Active + inactive",
  true: "Active only",
  false: "Inactive only",
};

const CJ_SKILL_SELECT_LABELS: Record<string, string> = {
  [ALL_VALUE]: "All CJ skills",
  ...CLINICAL_JUDGMENT_SKILL_LABELS,
};

interface QuestionFilterBarProps {
  filters: AdminQuestionFilters;
  searchInput: string;
  onSearchInputChange: (value: string) => void;
  onFiltersChange: (filters: AdminQuestionFilters) => void;
}

export function QuestionFilterBar({
  filters,
  searchInput,
  onSearchInputChange,
  onFiltersChange,
}: QuestionFilterBarProps) {
  const { data: taxonomy } = useTaxonomyOptions();

  const nursingSystemLabels: Record<string, string> = {
    [ALL_VALUE]: "All nursing systems",
    ...Object.fromEntries((taxonomy?.nursing_systems ?? []).map((s) => [s.id.toString(), s.name])),
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Input
        placeholder="Search stem..."
        value={searchInput}
        onChange={(e) => onSearchInputChange(e.target.value)}
        className="w-56"
      />

      <Select
        value={filters.question_type?.[0] ?? ALL_VALUE}
        onValueChange={(value) =>
          onFiltersChange({
            ...filters,
            question_type: value === ALL_VALUE ? undefined : [value as QuestionType],
          })
        }
      >
        <SelectTrigger className="w-44">
          <SelectValue>{(value: string) => QUESTION_TYPE_SELECT_LABELS[value] ?? value}</SelectValue>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL_VALUE}>All types</SelectItem>
          {[...SUPPORTED_QUESTION_TYPES, "NGN_CASE" as const].map((type) => (
            <SelectItem key={type} value={type}>
              {QUESTION_TYPE_LABELS[type]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.nursing_system?.[0]?.toString() ?? ALL_VALUE}
        onValueChange={(value) =>
          onFiltersChange({
            ...filters,
            nursing_system: value === ALL_VALUE ? undefined : [Number(value)],
          })
        }
      >
        <SelectTrigger className="w-48">
          <SelectValue>{(value: string) => nursingSystemLabels[value] ?? value}</SelectValue>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL_VALUE}>All nursing systems</SelectItem>
          {taxonomy?.nursing_systems.map((system) => (
            <SelectItem key={system.id} value={system.id.toString()}>
              {system.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.difficulty?.[0] ?? ALL_VALUE}
        onValueChange={(value) =>
          onFiltersChange({
            ...filters,
            difficulty: value === ALL_VALUE ? undefined : [value as "EASY" | "MEDIUM" | "HARD"],
          })
        }
      >
        <SelectTrigger className="w-36">
          <SelectValue>{(value: string) => DIFFICULTY_SELECT_LABELS[value] ?? value}</SelectValue>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL_VALUE}>All difficulties</SelectItem>
          {Object.entries(DIFFICULTY_LABELS).map(([value, label]) => (
            <SelectItem key={value} value={value}>
              {label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.is_active === undefined ? ALL_VALUE : String(filters.is_active)}
        onValueChange={(value) =>
          onFiltersChange({ ...filters, is_active: value === ALL_VALUE ? undefined : value === "true" })
        }
      >
        <SelectTrigger className="w-36">
          <SelectValue>{(value: string) => STATUS_SELECT_LABELS[value] ?? value}</SelectValue>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL_VALUE}>Active + inactive</SelectItem>
          <SelectItem value="true">Active only</SelectItem>
          <SelectItem value="false">Inactive only</SelectItem>
        </SelectContent>
      </Select>

      <Select
        value={filters.clinical_judgment_skill?.[0] ?? ALL_VALUE}
        onValueChange={(value) =>
          onFiltersChange({
            ...filters,
            clinical_judgment_skill: value === ALL_VALUE || value === null ? undefined : [value],
          })
        }
      >
        <SelectTrigger className="w-52">
          <SelectValue>{(value: string) => CJ_SKILL_SELECT_LABELS[value] ?? value}</SelectValue>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL_VALUE}>All CJ skills</SelectItem>
          {Object.entries(CLINICAL_JUDGMENT_SKILL_LABELS).map(([value, label]) => (
            <SelectItem key={value} value={value}>
              {label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
