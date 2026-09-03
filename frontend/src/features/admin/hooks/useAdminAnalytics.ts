import { useQuery } from "@tanstack/react-query";

import * as adminApi from "@/lib/api/admin";

export function useAdminAnalytics() {
  return useQuery({
    queryKey: ["admin", "analytics"],
    queryFn: adminApi.getAnalytics,
    staleTime: 60_000,
  });
}
