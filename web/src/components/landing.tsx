import Link from "next/link";
import {
  BookOpen,
  Brain,
  Check,
  Code2,
  Github,
  MessageCircle,
  Newspaper,
  Rss,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FEATURES } from "@/lib/features";

const GITHUB_URL = "https://github.com/contractorr/stewardme";

const SOURCE_ICONS = [
  { name: "Hacker News", icon: Newspaper },
  { name: "GitHub", icon: Github },
  { name: "arXiv", icon: BookOpen },
  { name: "Reddit", icon: MessageCircle },
  { name: "RSS", icon: Rss },
];

const STEPS = [
  {
    number: "1",
    title: "Sign up",
    description: "Connect with GitHub or Google. No credit card.",
  },
  {
    number: "2",
    title: "Tell it what matters",
    description: "Add topics, goals, or paste your first journal entry.",
  },
  {
    number: "3",
    title: "Get briefed",
    description:
      "Your steward cross-references live intel with your journal and goals — then tells you what to do next and why.",
  },
];

const COMPARISON_ROWS = [
  { axis: "Your data stays local", detail: "SQLite + markdown files" },
  {
    axis: "Scans live sources for you",
    detail: "10 async scrapers (HN, arXiv, GitHub, Reddit, RSS, ...)",
  },
  {
    axis: "Learns from your feedback",
    detail: "Per-category scoring adjusts over time",
  },
  { axis: "Self-hosted", detail: "Docker one-liner or bare metal" },
  {
    axis: "Multi-provider LLM",
    detail: "Claude, OpenAI, Gemini (auto-detect)",
  },
  { axis: "Open source", detail: "AGPL-3.0" },
];

const TECH_STACK = [
  "Python",
  "FastAPI",
  "Next.js",
  "TypeScript",
  "ChromaDB",
  "SQLite",
  "Tailwind CSS",
];
export default function Landing() {
  return (
    <div className="flex min-h-screen flex-col items-center bg-muted/40">
      {/* Hero */}
      <section className="flex flex-col items-center px-4 pt-[15vh] pb-16 text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
          <Brain className="h-7 w-7 text-primary" />
        </div>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          Know what matters next
        </h1>
        <p className="mt-4 max-w-md text-lg text-muted-foreground">
          AI steward that scans the world, learns from your journal, and guides
          you through what&apos;s next.
        </p>
        <div className="mt-4 flex gap-2">
          <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer">
            <Badge variant="secondary">Open source</Badge>
          </a>
          <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer">
            <Badge variant="secondary">Self-hostable</Badge>
          </a>
        </div>
        <div className="mt-8 flex gap-3">
          <Button asChild>
            <Link href="/login">Get started</Link>
          </Button>
          <Button variant="outline" asChild>
            <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer">
              <Github className="mr-2 h-4 w-4" />
              View on GitHub
            </a>
          </Button>
        </div>
      </section>

      {/* Source logos */}
      <section className="flex flex-col items-center px-4 py-12">
        <p className="mb-6 text-sm text-muted-foreground">
          Scans the sources you care about
        </p>
        <div className="flex flex-wrap items-center justify-center gap-8">
          {SOURCE_ICONS.map(({ name, icon: Icon }) => (
            <div key={name} className="flex flex-col items-center gap-1">
              <Icon className="h-6 w-6 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">{name}</span>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="w-full max-w-3xl px-4 py-16">
        <h2 className="mb-8 text-center text-2xl font-semibold tracking-tight">
          How it works
        </h2>
        <div className="grid grid-cols-1 gap-8 sm:grid-cols-3">
          {STEPS.map(({ number, title, description }) => (
            <div key={number} className="flex flex-col items-center text-center">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground">
                {number}
              </div>
              <p className="text-sm font-semibold">{title}</p>
              <p className="mt-1 text-sm text-muted-foreground">{description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Why StewardMe? */}
      <section className="w-full max-w-3xl px-4 py-16">
        <p className="mb-6 text-center text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Why StewardMe?
        </p>
        <div className="overflow-x-auto rounded-xl border bg-card">
          <table className="min-w-[600px] w-full text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                <th className="px-4 py-3 font-medium" />
                <th className="px-4 py-3 font-medium">ChatGPT / Copilot</th>
                <th className="px-4 py-3 font-medium">Notion AI</th>
                <th className="px-4 py-3 font-medium">StewardMe</th>
              </tr>
            </thead>
            <tbody>
              {COMPARISON_ROWS.map(({ axis, detail }) => (
                <tr key={axis} className="border-b last:border-0">
                  <td className="px-4 py-3 font-medium">{axis}</td>
                  <td className="px-4 py-3 text-muted-foreground">—</td>
                  <td className="px-4 py-3 text-muted-foreground">—</td>
                  <td className="px-4 py-3">
                    <span className="flex items-center gap-1.5">
                      <Check className="h-4 w-4 shrink-0 text-primary" />
                      {detail}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Feature grid */}
      <section className="w-full max-w-[700px] px-4 py-12">
        <h2 className="mb-6 text-center text-2xl font-semibold tracking-tight">
          What you get
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {FEATURES.map(({ icon: Icon, title, description }) => (
            <div
              key={title}
              className="flex gap-3 rounded-xl border bg-card p-4"
            >
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/10">
                <Icon className="h-4 w-4 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium">{title}</p>
                <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">
                  {description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Built for developers */}
      <section className="flex w-full max-w-xl flex-col items-center px-4 py-16 text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
          <Code2 className="h-7 w-7 text-primary" />
        </div>
        <h2 className="text-2xl font-semibold tracking-tight">
          Open source and easy to extend
        </h2>
        <p className="mt-3 max-w-md text-sm leading-relaxed text-muted-foreground">
          RAG pipeline backed by Python + FastAPI, Next.js frontend, ChromaDB
          embeddings, SQLite intel storage. Add a scraper in under 50 lines.
        </p>
        <div className="mt-4 flex flex-wrap justify-center gap-2">
          {TECH_STACK.map((tech) => (
            <Badge key={tech} variant="secondary">
              {tech}
            </Badge>
          ))}
        </div>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Button variant="outline" asChild>
            <a
              href={`${GITHUB_URL}/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22`}
              target="_blank"
              rel="noopener noreferrer"
            >
              Good first issues
            </a>
          </Button>
          <Button variant="outline" asChild>
            <a
              href={`${GITHUB_URL}/blob/main/CONTRIBUTING.md`}
              target="_blank"
              rel="noopener noreferrer"
            >
              Contributing guide
            </a>
          </Button>
        </div>
      </section>

      {/* Footer CTA + links */}
      <section className="flex flex-col items-center px-4 py-16">
        <div className="flex gap-3">
          <Button asChild size="lg">
            <Link href="/login">Get started free</Link>
          </Button>
          <Button variant="outline" size="lg" asChild>
            <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer">
              <Github className="mr-2 h-4 w-4" />
              Explore the code
            </a>
          </Button>
        </div>
        <div className="mt-6 flex gap-3 text-xs text-muted-foreground">
          <Link href="/privacy" className="underline hover:text-foreground">
            Privacy Policy
          </Link>
          <span>&middot;</span>
          <Link href="/terms" className="underline hover:text-foreground">
            Terms of Service
          </Link>
          <span>&middot;</span>
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-foreground"
          >
            GitHub
          </a>
        </div>
      </section>
    </div>
  );
}
