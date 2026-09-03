import { useQuery } from "@tanstack/react-query";

import * as adminApi from "@/lib/api/admin";

/** staleTime: Infinity — taxonomy is admin-managed reference data that essentially never changes mid-session. */
export function useTaxonomyOptions() {
  return useQuery({
    queryKey: ["admin", "taxonomy-options"],
    queryFn: adminApi.getTaxonomy,
    staleTime: Infinity,
  });
}
