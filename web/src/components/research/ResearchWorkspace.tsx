"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Download, FileText, FolderOpen, Plus, RefreshCcw, Search } from "lucide-react";
import { WorkspacePageHeader } from "@/components/WorkspacePageHeader";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import type { LibraryReport, LibraryReportListItem } from "@/types/library";
import type { ResearchDossier } from "@/types/radar";

type StatusFilter = "all" | "ready" | "archived";
type ContentFilter = "all" | "documents" | "reports" | "dossiers";

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

export default function ResearchWorkspace() {
  const token = useToken();
  const [reports, setReports] = useState<LibraryReportListItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedReport, setSelectedReport] = useState<LibraryReport | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [contentFilter, setContentFilter] = useState<ContentFilter>("all");
  const [pdfPreviewUrl, setPdfPreviewUrl] = useState<string | null>(null);
  const [dossiers, setDossiers] = useState<ResearchDossier[]>([]);
  const [selectedDossierId, setSelectedDossierId] = useState<string | null>(null);
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
        `/api/v1/library/reports${params.toString() ? `?${params.toString()}` : ""}`,
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
      const report = await apiFetch<LibraryReport>(`/api/v1/library/reports/${reportId}`, {}, token);
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
    if (!token) return;
    apiFetch<ResearchDossier[]>("/api/v1/research/dossiers?include_archived=true&limit=50", {}, token)
      .then((items) => {
        const archived = items.filter((item) => (item.status || "active") === "archived");
        setDossiers(archived);
        setSelectedDossierId((current) => current ?? archived[0]?.dossier_id ?? null);
      })
      .catch(() => {});
  }, [token]);

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
        const res = await fetch(apiUrl(`/api/v1/library/reports/${selectedReport.id}/file`), {
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
      documents: reports.filter((report) => report.source_kind === "uploaded_pdf").length,
      reports: reports.filter((report) => report.source_kind !== "uploaded_pdf").length,
      dossiers: dossiers.length,
      ready: reports.filter((report) => report.status === "ready").length,
      archived: reports.filter((report) => report.status === "archived").length,
    }),
    [dossiers.length, reports]
  );

  const visibleReports = useMemo(() => {
    if (contentFilter === "documents") {
      return reports.filter((report) => report.source_kind === "uploaded_pdf");
    }
    if (contentFilter === "reports") {
      return reports.filter((report) => report.source_kind !== "uploaded_pdf");
    }
    return reports;
  }, [contentFilter, reports]);

  const selectedDossier = useMemo(
    () => dossiers.find((item) => item.dossier_id === selectedDossierId) ?? null,
    [dossiers, selectedDossierId]
  );

  const handleCreate = async () => {
    if (!token || createForm.prompt.trim().length < 10) return;
    setCreating(true);
    try {
      const created = await apiFetch<LibraryReport>(
        "/api/v1/library/reports",
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
      setCreateOpen(false);
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
        `/api/v1/library/reports/${selectedReport.id}`,
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
        `/api/v1/library/reports/${selectedReport.id}/refresh`,
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
        `/api/v1/library/reports/${selectedReport.id}/${endpoint}`,
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
      <WorkspacePageHeader
        eyebrow="Research"
        title="Research"
        description="Keep your durable documents, reports, and completed dossier outputs in one research workspace."
        actions={
          <Sheet open={createOpen} onOpenChange={setCreateOpen}>
            <SheetTrigger asChild>
              <Button>
                <Plus className="h-4 w-4" /> New report
              </Button>
            </SheetTrigger>
            <SheetContent className="w-full overflow-y-auto sm:max-w-lg">
              <SheetHeader>
                <SheetTitle>New report</SheetTitle>
                <SheetDescription>
                  Turn a prompt into a saved report, such as an industry crash course, overview, memo, or plan.
                </SheetDescription>
              </SheetHeader>
              <div className="mt-6 space-y-4 px-6 pb-6">
                <div className="space-y-1.5">
                  <Label>Prompt</Label>
                  <Textarea
                    rows={5}
                    placeholder="What should I know before meeting with a fintech founder?"
                    value={createForm.prompt}
                    onChange={(e) => setCreateForm((prev) => ({ ...prev, prompt: e.target.value }))}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Type</Label>
                  <Select
                    value={createForm.report_type}
                    onValueChange={(value) => setCreateForm((prev) => ({ ...prev, report_type: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {reportTypes.map(([value, label]) => (
                        <SelectItem key={value} value={value}>
                          {label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label>Collection</Label>
                  <Input
                    placeholder="e.g. Industries"
                    value={createForm.collection}
                    onChange={(e) => setCreateForm((prev) => ({ ...prev, collection: e.target.value }))}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Title (optional)</Label>
                  <Input
                    placeholder="e.g. Fintech landscape overview"
                    value={createForm.title}
                    onChange={(e) => setCreateForm((prev) => ({ ...prev, title: e.target.value }))}
                  />
                </div>
                <Button onClick={handleCreate} disabled={creating || createForm.prompt.trim().length < 10}>
                  {creating ? "Generating..." : "Generate report"}
                </Button>
              </div>
            </SheetContent>
          </Sheet>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[360px_minmax(0,1fr)]">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Browse research</CardTitle>
              <CardDescription>
                Filter by content type, search durable material, and jump back into the right workspace quickly.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Search research material"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <div className="flex flex-wrap gap-2">
                {([
                  ["all", `All ${counts.all}`],
                  ["documents", `Documents ${counts.documents}`],
                  ["reports", `Reports ${counts.reports}`],
                  ["dossiers", `Dossiers ${counts.dossiers}`],
                ] as const).map(([value, label]) => (
                  <Button
                    key={value}
                    size="sm"
                    variant={contentFilter === value ? "default" : "outline"}
                    onClick={() => setContentFilter(value)}
                  >
                    {label}
                  </Button>
                ))}
                <Button size="sm" variant="outline" asChild>
                  <Link href="/journal">Journal</Link>
                </Button>
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
                {contentFilter !== "dossiers" && loadingList && <p className="text-sm text-muted-foreground">Loading research items...</p>}
                {contentFilter === "dossiers" && dossiers.length === 0 && (
                  <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
                    No archived dossiers yet. Active dossiers live in Radar until you archive them to Research.
                  </div>
                )}
                {contentFilter !== "dossiers" && !loadingList && visibleReports.length === 0 && (
                  <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
                    No matching items yet. Upload a document or generate a report to start your research workspace.
                  </div>
                )}
                {contentFilter === "dossiers" &&
                  dossiers.map((dossier) => (
                    <button
                      key={dossier.dossier_id}
                      type="button"
                      onClick={() => setSelectedDossierId(dossier.dossier_id)}
                      className={`w-full rounded-lg border p-3 text-left transition ${
                        selectedDossierId === dossier.dossier_id ? "border-primary bg-muted/50" : "hover:bg-muted/40"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-medium">{dossier.topic}</span>
                            <Badge variant="outline" className="text-xs">archived dossier</Badge>
                          </div>
                          {dossier.latest_change_summary ? (
                            <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">{dossier.latest_change_summary}</p>
                          ) : null}
                        </div>
                      </div>
                    </button>
                  ))}
                {contentFilter !== "dossiers" && !loadingList &&
                  visibleReports.map((report) => (
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
            <CardTitle>{contentFilter === "dossiers" ? "Selected dossier" : "Selected report"}</CardTitle>
            <CardDescription>
              {contentFilter === "dossiers"
                ? "Completed dossier outputs stay here as reusable reference material."
                : "Edit the current version, refresh it from the original prompt, or archive it without losing the artifact."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {contentFilter === "dossiers" && !selectedDossier && (
              <div className="flex min-h-[420px] flex-col items-center justify-center gap-3 rounded-lg border border-dashed text-center">
                <FileText className="h-8 w-8 text-muted-foreground" />
                <div className="space-y-1">
                  <p className="font-medium">Pick a dossier</p>
                  <p className="text-sm text-muted-foreground">
                    Archived dossiers stay in Research once the active tracking work is done.
                  </p>
                </div>
              </div>
            )}
            {contentFilter !== "dossiers" && !selectedId && !loadingList && (
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
            {contentFilter !== "dossiers" && loadingDetail && <p className="text-sm text-muted-foreground">Loading report...</p>}
            {contentFilter === "dossiers" && selectedDossier && (
              <div className="space-y-4">
                <div className="space-y-1">
                  <h2 className="text-xl font-semibold">{selectedDossier.topic}</h2>
                  <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    <Badge variant="outline">archived dossier</Badge>
                    <span>Updated {formatDate(selectedDossier.last_updated || selectedDossier.updated || selectedDossier.created || "")}</span>
                    <span>{selectedDossier.update_count || 0} updates recorded</span>
                  </div>
                </div>

                <div className="rounded-lg border bg-muted/20 p-4 text-sm text-muted-foreground">
                  {selectedDossier.latest_change_summary || "No summary was captured for the latest change."}
                </div>

                {selectedDossier.open_questions?.length ? (
                  <div className="space-y-2">
                    <div className="text-sm font-medium">Open questions</div>
                    <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                      {selectedDossier.open_questions.map((question) => (
                        <li key={question}>{question}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                <div className="flex flex-wrap gap-2">
                  <Button variant="outline" asChild>
                    <Link href="/radar">Open Radar</Link>
                  </Button>
                  <Button variant="outline" asChild>
                    <Link href="/journal">Open Journal</Link>
                  </Button>
                </div>
              </div>
            )}
            {contentFilter !== "dossiers" && selectedReport && !loadingDetail && (
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
