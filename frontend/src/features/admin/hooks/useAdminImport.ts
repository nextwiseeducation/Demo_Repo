import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as adminApi from "@/lib/api/admin";
import type { UploadImportOptions } from "@/lib/api/admin";

export function useImportLog(page: number) {
  return useQuery({
    queryKey: ["admin", "import-log", page],
    queryFn: () => adminApi.listImportLog(page),
  });
}

/** No onSuccess/onError toast here — ImportUploadPanel renders the full structured result (or error) inline, which carries more information than a toast could. */
export function useUploadImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ file, options }: { file: File; options?: UploadImportOptions }) =>
      adminApi.uploadImport(file, options),
    onSuccess: (result) => {
      if (result.dry_run) return;
      queryClient.invalidateQueries({ queryKey: ["admin", "questions"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "import-log"] });
    },
  });
}
