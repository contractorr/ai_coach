"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Download, FileText, FolderOpen, RefreshCcw, Search } from "lucide-react";
import { useToken } from "@/hooks/useToken";
import { apiFetch, apiUrl } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { LibraryReport, LibraryReportListItem } from "@/types/library";

type StatusFilter = "all" | "ready" | "archived";

const reportTypes = [
  ["crash_course", "Crash course"],
  ["overview", "Overview"],
  ["memo", "Memo"],
  ["plan", "Plan"],
  ["custom", "Custom"],
] as const;

function formatDate(value: string) {
  if (!value) return "";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function formatFileSize(value?: number | null) {
  if (!value || value < 0) return "";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export default function LibraryPage() {
  const token = useToken();
  const [reports, setReports] = useState<LibraryReportListItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedReport, setSelectedReport] = useState<LibraryReport | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [creating, setCreating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [pdfPreviewUrl, setPdfPreviewUrl] = useState<string | null>(null);
  const [createForm, setCreateForm] = useState({
    prompt: "",
    report_type: "crash_course",
    title: "",
    collection: "",
  });
  const [draft, setDraft] = useState({ title: "", collection: "", content: "" });

  const loadReports = async () => {
    if (!token) {
      setLoadingList(false);
      return;
    }
    setLoadingList(true);
    try {
      const params = new URLSearchParams();
      if (search.trim()) params.set("search", search.trim());
      if (statusFilter !== "all") params.set("status", statusFilter);
      const data = await apiFetch<LibraryReportListItem[]>(
        `/api/library/reports${params.toString() ? `?${params.toString()}` : ""}`,
        {},
        token
      );
      setReports(data);
      setSelectedId((current) => {
        if (current && data.some((report) => report.id === current)) return current;
        return data[0]?.id ?? null;
      });
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setLoadingList(false);
    }
  };

  const loadReport = async (reportId: string) => {
    if (!token) return;
    setLoadingDetail(true);
    try {
      const report = await apiFetch<LibraryReport>(`/api/library/reports/${reportId}`, {}, token);
      setSelectedReport(report);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setLoadingDetail(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, [token, search, statusFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (selectedId) {
      loadReport(selectedId);
    } else {
      setSelectedReport(null);
    }
  }, [selectedId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!selectedReport) return;
    setDraft({
      title: selectedReport.title,
      collection: selectedReport.collection ?? "",
      content: selectedReport.content,
    });
  }, [selectedReport]);

  useEffect(() => {
    if (!token || !selectedReport?.has_attachment || selectedReport.source_kind !== "uploaded_pdf") {
      setPdfPreviewUrl((current) => {
        if (current) URL.revokeObjectURL(current);
        return null;
      });
      return;
    }

    let cancelled = false;

    const loadPreview = async () => {
      try {
        const res = await fetch(apiUrl(`/api/library/reports/${selectedReport.id}/file`), {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.detail || `API error ${res.status}`);
        }
        const blob = await res.blob();
        const nextUrl = URL.createObjectURL(blob);
        if (cancelled) {
          URL.revokeObjectURL(nextUrl);
          return;
        }
        setPdfPreviewUrl((current) => {
          if (current) URL.revokeObjectURL(current);
          return nextUrl;
        });
      } catch (e) {
        if (!cancelled) toast.error((e as Error).message);
      }
    };

    loadPreview();

    return () => {
      cancelled = true;
    };
  }, [selectedReport?.has_attachment, selectedReport?.id, selectedReport?.source_kind, token]);

  const counts = useMemo(
    () => ({
      all: reports.length,
      ready: reports.filter((report) => report.status === "ready").length,
      archived: reports.filter((report) => report.status === "archived").length,
    }),
    [reports]
  );

  const handleCreate = async () => {
    if (!token || createForm.prompt.trim().length < 10) return;
    setCreating(true);
    try {
      const created = await apiFetch<LibraryReport>(
        "/api/library/reports",
        {
          method: "POST",
          body: JSON.stringify({
            prompt: createForm.prompt.trim(),
            report_type: createForm.report_type,
            title: createForm.title.trim() || null,
            collection: createForm.collection.trim() || null,
          }),
        },
        token
      );
      toast.success("Report created");
      setCreateForm({ prompt: "", report_type: "crash_course", title: "", collection: "" });
      await loadReports();
      setSelectedId(created.id);
      setSelectedReport(created);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setCreating(false);
    }
  };

  const handleSave = async () => {
    if (!token || !selectedReport) return;
    setSaving(true);
    try {
      const updated = await apiFetch<LibraryReport>(
        `/api/library/reports/${selectedReport.id}`,
        {
          method: "PUT",
          body: JSON.stringify({
            title: draft.title.trim(),
            collection: draft.collection.trim() || null,
            content: draft.content,
          }),
        },
        token
      );
      setSelectedReport(updated);
      setReports((prev) => prev.map((report) => (report.id === updated.id ? updated : report)));
      toast.success("Report saved");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const handleRefresh = async () => {
    if (!token || !selectedReport) return;
    setRefreshing(true);
    try {
      const refreshed = await apiFetch<LibraryReport>(
        `/api/library/reports/${selectedReport.id}/refresh`,
        { method: "POST" },
        token
      );
      setSelectedReport(refreshed);
      setReports((prev) => prev.map((report) => (report.id === refreshed.id ? refreshed : report)));
      toast.success("Report refreshed");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setRefreshing(false);
    }
  };

  const handleToggleArchive = async () => {
    if (!token || !selectedReport) return;
    const endpoint = selectedReport.status === "archived" ? "restore" : "archive";
    try {
      const updated = await apiFetch<LibraryReport>(
        `/api/library/reports/${selectedReport.id}/${endpoint}`,
        { method: "POST" },
        token
      );
      setSelectedReport(updated);
      setReports((prev) => prev.map((report) => (report.id === updated.id ? updated : report)));
      toast.success(updated.status === "archived" ? "Report archived" : "Report restored");
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const handleDownloadAttachment = () => {
    if (!pdfPreviewUrl || !selectedReport?.has_attachment) return;
    const link = document.createElement("a");
    link.href = pdfPreviewUrl;
    link.download = selectedReport.file_name || `${selectedReport.title}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const isUploadedPdf = selectedReport?.source_kind === "uploaded_pdf";

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4 md:p-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold">Library</h1>
        <p className="text-sm text-muted-foreground">
          Generate durable reports from prompts and keep longer-form work outside the chat stream.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[360px_minmax(0,1fr)]">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Create report</CardTitle>
              <CardDescription>
                Turn a prompt into a saved report, such as an industry crash course, overview, memo, or plan.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <Label>Prompt</Label>
                <Textarea
                  rows={5}
                  placeholder="Give me a crash course on the insurance industry"
                  value={createForm.prompt}
                  onChange={(e) => setCreateForm((prev) => ({ ...prev, prompt: e.target.value }))}
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label>Type</Label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={createForm.report_type}
                    onChange={(e) => setCreateForm((prev) => ({ ...prev, report_type: e.target.value }))}
                  >
                    {reportTypes.map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <Label>Collection</Label>
                  <Input
                    placeholder="Industries"
                    value={createForm.collection}
                    onChange={(e) => setCreateForm((prev) => ({ ...prev, collection: e.target.value }))}
                  />
                </div>
              </div>
              <div className="space-y-1.5">
                <Label>Custom title (optional)</Label>
                <Input
                  placeholder="Insurance Industry Crash Course"
                  value={createForm.title}
                  onChange={(e) => setCreateForm((prev) => ({ ...prev, title: e.target.value }))}
                />
              </div>
              <Button onClick={handleCreate} disabled={creating || createForm.prompt.trim().length < 10}>
                {creating ? "Generating..." : "Generate report"}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Browse library</CardTitle>
              <CardDescription>
                Search saved reports, focus the list, and jump back into longer work quickly.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Search reports"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <div className="flex flex-wrap gap-2">
                {([
                  ["all", `All ${counts.all}`],
                  ["ready", `Ready ${counts.ready}`],
                  ["archived", `Archived ${counts.archived}`],
                ] as const).map(([value, label]) => (
                  <Button
                    key={value}
                    size="sm"
                    variant={statusFilter === value ? "default" : "outline"}
                    onClick={() => setStatusFilter(value)}
                  >
                    {label}
                  </Button>
                ))}
              </div>

              <div className="space-y-2">
                {loadingList && <p className="text-sm text-muted-foreground">Loading reports...</p>}
                {!loadingList && reports.length === 0 && (
                  <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
                    No reports yet. Generate your first long-form report to start your library.
                  </div>
                )}
                {!loadingList &&
                  reports.map((report) => (
                    <button
                      key={report.id}
                      type="button"
                      onClick={() => setSelectedId(report.id)}
                      className={`w-full rounded-lg border p-3 text-left transition ${
                        selectedId === report.id ? "border-primary bg-muted/50" : "hover:bg-muted/40"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-medium">{report.title}</span>
                            <Badge variant="secondary" className="text-xs">
                              {report.report_type.replace("_", " ")}
                            </Badge>
                            <Badge variant={report.status === "archived" ? "outline" : "default"} className="text-xs">
                              {report.status}
                            </Badge>
                          </div>
                          {report.collection && (
                            <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                              <FolderOpen className="h-3 w-3" />
                              {report.collection}
                            </p>
                          )}
                          {report.preview && (
                            <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">{report.preview}</p>
                          )}
                        </div>
                      </div>
                    </button>
                  ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="min-h-[680px]">
          <CardHeader>
            <CardTitle>Selected report</CardTitle>
            <CardDescription>
              Edit the current version, refresh it from the original prompt, or archive it without losing the artifact.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {!selectedId && !loadingList && (
              <div className="flex min-h-[420px] flex-col items-center justify-center gap-3 rounded-lg border border-dashed text-center">
                <FileText className="h-8 w-8 text-muted-foreground" />
                <div className="space-y-1">
                  <p className="font-medium">Pick a report or create one</p>
                  <p className="text-sm text-muted-foreground">
                    The right side becomes your working document once a report is selected.
                  </p>
                </div>
              </div>
            )}
            {loadingDetail && <p className="text-sm text-muted-foreground">Loading report...</p>}
            {selectedReport && !loadingDetail && (
              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label>Title</Label>
                    <Input value={draft.title} onChange={(e) => setDraft((prev) => ({ ...prev, title: e.target.value }))} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Collection</Label>
                    <Input
                      placeholder="Industries"
                      value={draft.collection}
                      onChange={(e) => setDraft((prev) => ({ ...prev, collection: e.target.value }))}
                    />
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  <Badge variant="secondary">{selectedReport.report_type.replace("_", " ")}</Badge>
                  <Badge variant={selectedReport.status === "archived" ? "outline" : "default"}>
                    {selectedReport.status}
                  </Badge>
                  <span>Updated {formatDate(selectedReport.updated)}</span>
                  <span>{isUploadedPdf ? "Added" : "Generated"} {formatDate(selectedReport.last_generated_at)}</span>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button onClick={handleSave} disabled={saving}>
                    {saving ? "Saving..." : isUploadedPdf ? "Save details" : "Save edits"}
                  </Button>
                  {!isUploadedPdf && (
                    <Button variant="outline" onClick={handleRefresh} disabled={refreshing}>
                      <RefreshCcw className="mr-2 h-4 w-4" />
                      {refreshing ? "Refreshing..." : "Refresh report"}
                    </Button>
                  )}
                  {isUploadedPdf && (
                    <Button variant="outline" onClick={handleDownloadAttachment} disabled={!pdfPreviewUrl}>
                      <Download className="mr-2 h-4 w-4" />
                      Download PDF
                    </Button>
                  )}
                  <Button variant="outline" onClick={handleToggleArchive}>
                    {selectedReport.status === "archived" ? "Restore report" : "Archive report"}
                  </Button>
                </div>

                {isUploadedPdf ? (
                  <>
                    <div className="space-y-1.5">
                      <Label>Uploaded file</Label>
                      <div className="rounded-md border bg-muted/40 px-3 py-3 text-sm text-muted-foreground">
                        <div className="font-medium text-foreground">{selectedReport.file_name || selectedReport.title}</div>
                        <div className="mt-1 flex flex-wrap gap-3 text-xs">
                          <span>{selectedReport.mime_type || "application/pdf"}</span>
                          {selectedReport.file_size ? <span>{formatFileSize(selectedReport.file_size)}</span> : null}
                        </div>
                      </div>
                    </div>
                    <div className="space-y-1.5">
                      <Label>Preview</Label>
                      <div className="overflow-hidden rounded-md border bg-white">
                        {pdfPreviewUrl ? (
                          <iframe
                            src={pdfPreviewUrl}
                            title={selectedReport.file_name || selectedReport.title}
                            className="h-[720px] w-full"
                          />
                        ) : (
                          <div className="flex h-[240px] items-center justify-center text-sm text-muted-foreground">
                            Loading PDF preview...
                          </div>
                        )}
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="space-y-1.5">
                      <Label>Original prompt</Label>
                      <div className="rounded-md border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
                        {selectedReport.prompt}
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      <Label>Content</Label>
                      <Textarea
                        rows={24}
                        value={draft.content}
                        onChange={(e) => setDraft((prev) => ({ ...prev, content: e.target.value }))}
                        placeholder="Generated report content appears here."
                      />
                    </div>
                  </>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
