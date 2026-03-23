"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { ArrowLeft, BookOpen, Clock, Play } from "lucide-react";
import { useToken } from "@/hooks/useToken";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChapterList } from "@/components/curriculum/ChapterList";
import { DifficultyBadge } from "@/components/curriculum/DifficultyBadge";
import { ProgressRing } from "@/components/curriculum/ProgressRing";
import type { GuideDetail } from "@/types/curriculum";

function formatTime(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

export default function GuideDetailPage() {
  const token = useToken();
  const params = useParams();
  const guideId = params.guideId as string;

  const [guide, setGuide] = useState<GuideDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [enrolling, setEnrolling] = useState(false);

  useEffect(() => {
    if (!token || !guideId) return;
    setLoading(true);
    apiFetch<GuideDetail>(`/api/curriculum/guides/${guideId}`, {}, token)
      .then(setGuide)
      .catch((e) => toast.error((e as Error).message))
      .finally(() => setLoading(false));
  }, [token, guideId]);

  const handleEnroll = async () => {
    if (!token) return;
    setEnrolling(true);
    try {
      await apiFetch(`/api/curriculum/guides/${guideId}/enroll`, { method: "POST" }, token);
      // Reload
      const updated = await apiFetch<GuideDetail>(`/api/curriculum/guides/${guideId}`, {}, token);
      setGuide(updated);
      toast.success("Enrolled!");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setEnrolling(false);
    }
  };

  const firstUnread = guide?.chapters?.find((c) => c.status !== "completed");

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        <div className="h-40 animate-pulse rounded-lg bg-muted" />
      </div>
    );
  }

  if (!guide) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Guide not found</p>
        <Link href="/learn">
          <Button variant="ghost" className="mt-2">Back to guides</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Link href="/learn">
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight">{guide.title}</h1>
      </div>

      {/* Meta + actions */}
      <Card>
        <CardContent className="flex flex-wrap items-center justify-between gap-4 p-5">
          <div className="flex flex-wrap items-center gap-3">
            <DifficultyBadge level={guide.difficulty} />
            <span className="flex items-center gap-1 text-sm text-muted-foreground">
              <BookOpen className="h-3.5 w-3.5" />
              {guide.chapter_count} chapters
            </span>
            <span className="flex items-center gap-1 text-sm text-muted-foreground">
              <Clock className="h-3.5 w-3.5" />
              {formatTime(guide.total_reading_time_minutes)}
            </span>
            {guide.has_glossary && (
              <Badge variant="outline" className="text-[10px]">Glossary</Badge>
            )}
          </div>
          <div className="flex items-center gap-3">
            {guide.enrolled && (
              <ProgressRing progress={guide.progress_pct ?? 0} size={44} strokeWidth={4} />
            )}
            {!guide.enrolled && (
              <Button onClick={handleEnroll} disabled={enrolling}>
                {enrolling ? "Enrolling..." : "Enroll"}
              </Button>
            )}
            {firstUnread && (
              <Link href={`/learn/${guideId}/${firstUnread.id.split("/").pop()}`}>
                <Button>
                  <Play className="mr-1.5 h-3.5 w-3.5" />
                  {guide.chapters_completed ? "Continue" : "Start reading"}
                </Button>
              </Link>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Chapter list */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Chapters</CardTitle>
        </CardHeader>
        <CardContent>
          <ChapterList guideId={guideId} chapters={guide.chapters ?? []} />
        </CardContent>
      </Card>
    </div>
  );
}
