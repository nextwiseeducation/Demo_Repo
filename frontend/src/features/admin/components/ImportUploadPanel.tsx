import { Upload } from "lucide-react";
import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import { ImportResultReport } from "@/features/admin/components/ImportResultReport";
import { useUploadImport } from "@/features/admin/hooks/useAdminImport";
import { normalizeApiError } from "@/lib/api/errors";

export function ImportUploadPanel() {
  const [file, setFile] = useState<File | null>(null);
  const [update, setUpdate] = useState(false);
  const [dryRun, setDryRun] = useState(false);
  const [uploadPercent, setUploadPercent] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadImport();

  function handleUpload() {
    if (!file) return;
    setUploadPercent(0);
    uploadMutation.mutate(
      { file, options: { update, dryRun, onUploadProgress: setUploadPercent } },
      {
        onSuccess: () => {
          setFile(null);
          if (fileInputRef.current) fileInputRef.current.value = "";
        },
      },
    );
  }

  const isUploading = uploadMutation.isPending;
  // onUploadProgress only measures bytes sent — once it hits 100% the
  // browser has finished sending the file, but the server is still
  // parsing/importing it. There's nothing to measure that phase against
  // (this is a synchronous endpoint, no row-by-row progress is reported),
  // so the bar goes indeterminate rather than sitting at a misleading 100%.
  const showIndeterminate = isUploading && uploadPercent >= 100;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Bulk import</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <p className="text-sm text-muted-foreground">
          Upload the standard NGN Item Bank workbook (.xlsx). A single CSV can't express the 6-sheet format this
          template uses, so only .xlsx/.xlsm files are accepted.
        </p>

        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xlsm"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="text-sm text-foreground file:mr-3 file:rounded-md file:border file:border-border file:bg-background file:px-3 file:py-1.5 file:text-sm"
        />

        <div className="flex flex-wrap gap-6">
          <div className="flex items-center gap-2">
            <Switch checked={update} onCheckedChange={setUpdate} />
            <Label className="text-sm text-foreground">Refresh existing questions (--update)</Label>
          </div>
          <div className="flex items-center gap-2">
            <Switch checked={dryRun} onCheckedChange={setDryRun} />
            <Label className="text-sm text-foreground">Dry run (validate only, write nothing)</Label>
          </div>
        </div>

        <Button onClick={handleUpload} disabled={!file || isUploading} className="w-fit">
          <Upload className="h-4 w-4" />
          {isUploading ? "Importing..." : "Upload and import"}
        </Button>

        {isUploading ? (
          <Progress value={showIndeterminate ? null : uploadPercent}>
            <p className="text-xs text-muted-foreground">
              {showIndeterminate ? "Importing... this can take a while for large files." : `Uploading... ${uploadPercent}%`}
            </p>
          </Progress>
        ) : null}

        {uploadMutation.isError ? (
          <p className="text-sm text-destructive">
            {normalizeApiError(uploadMutation.error).detail ??
              normalizeApiError(uploadMutation.error).fieldErrors?.file?.[0] ??
              "Couldn't import this file."}
          </p>
        ) : null}

        {uploadMutation.isSuccess ? <ImportResultReport result={uploadMutation.data} /> : null}
      </CardContent>
    </Card>
  );
}
