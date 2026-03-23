"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Link2 } from "lucide-react";
import { useToken } from "@/hooks/useToken";
import { apiFetch } from "@/lib/api";
import type { RelatedChapter } from "@/types/curriculum";

interface RelatedChaptersCardProps {
  chapterId: string;
}

export function RelatedChaptersCard({ chapterId }: RelatedChaptersCardProps) {
  const token = useToken();
  const [related, setRelated] = useState<RelatedChapter[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!token || !chapterId) return;
    apiFetch<{ related: RelatedChapter[] }>(
      `/api/curriculum/chapters/${chapterId}/related`,
      {},
      token
    )
      .then((data) => {
        setRelated(data.related ?? []);
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
  }, [token, chapterId]);

  if (!loaded || related.length === 0) return null;

  return (
    <div className="rounded-lg border p-4 space-y-3">
      <div className="flex items-center gap-2">
        <Link2 className="h-3.5 w-3.5 text-muted-foreground" />
        <p className="text-sm font-medium">Related from other guides</p>
      </div>
      <ul className="space-y-1.5">
        {related.map((r) => {
          const chapterStem = r.chapter_id.split("/").pop();
          return (
            <li key={r.chapter_id}>
              <Link
                href={`/learn/${r.guide_id}/${chapterStem}`}
                className="text-sm text-primary hover:underline"
              >
                {r.title} — <span className="text-muted-foreground">{r.guide_title}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
