"use client";

import { useEffect, useRef, useState } from "react";

import { apiBase } from "@/lib/api";
import { EXAMPLE_QUESTIONS } from "@/lib/examples";
import { parseSseBuffer } from "@/lib/sse";
import type { Health, ResearchReport, SseEvent, TraceStep } from "@/lib/types";

import { QuestionForm } from "./QuestionForm";
import { ReportView } from "./ReportView";
import { Timeline } from "./Timeline";

export function ResearchDesk() {
  const [question, setQuestion] = useState(EXAMPLE_QUESTIONS[0]);
  const [notes, setNotes] = useState("");
  const [running, setRunning] = useState(false);
  const [steps, setSteps] = useState<TraceStep[]>([]);
  const [report, setReport] = useState<ResearchReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const base = apiBase();
    fetch(`${base}/health`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Health check failed (${response.status})`);
        }
        setHealth((await response.json()) as Health);
      })
      .catch((cause: unknown) => {
        if (cause instanceof DOMException && cause.name === "AbortError") {
          return;
        }
        setHealthError(`Cannot reach the API at ${base}. Start it with make dev-api.`);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  async function runResearch() {
    const trimmed = question.trim();
    if (trimmed.length < 8 || running) {
      return;
    }
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setRunning(true);
    setError(null);
    setReport(null);
    setSteps([]);

    try {
      const response = await fetch(`${apiBase()}/api/research/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({ question: trimmed, notes: notes.trim() }),
        signal: controller.signal,
      });
      if (!response.ok || !response.body) {
        throw new Error(await readError(response));
      }
      await readStream(response.body, controller.signal, {
        onStep: (step) => setSteps((current) => [...current, step]),
        onReport: (next) => setReport(next),
        onError: (detail) => setError(detail),
      });
    } catch (cause) {
      if (cause instanceof DOMException && cause.name === "AbortError") {
        return;
      }
      setError(cause instanceof Error ? cause.message : "The research run failed.");
    } finally {
      if (abortRef.current === controller) {
        setRunning(false);
      }
    }
  }

  return (
    <>
      <a className="skip" href="#brief">
        Skip to brief
      </a>
      <header className="site-header">
        <div>
          <p className="eyebrow">Portfolio project</p>
          <h1>Multi-Agent Research Assistant</h1>
          <p className="lede">
            A planner, a researcher, a writer, and a critic turn one question into a cited brief.
          </p>
        </div>
        <div className="pills" aria-label="Configured providers">
          {health ? (
            <>
              <span>LLM {health.llm_provider}</span>
              <span>Model {health.llm_model}</span>
              <span>Search {health.search_provider}</span>
            </>
          ) : (
            <span>{healthError ?? "Checking the API"}</span>
          )}
        </div>
      </header>

      <main className="desk">
        <div className="stack">
          <QuestionForm
            question={question}
            notes={notes}
            running={running}
            onQuestion={setQuestion}
            onNotes={setNotes}
            onSubmit={() => {
              void runResearch();
            }}
          />
          {error ? (
            <p className="banner" role="alert">
              {error}
            </p>
          ) : null}
          <Timeline steps={steps} running={running} />
        </div>
        <ReportView report={report} />
      </main>
    </>
  );
}

async function readError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    // The body was not JSON.
  }
  return `Request failed (${response.status})`;
}

async function readStream(
  body: ReadableStream<Uint8Array>,
  signal: AbortSignal,
  handlers: {
    onStep: (step: TraceStep) => void;
    onReport: (report: ResearchReport) => void;
    onError: (detail: string) => void;
  },
) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (!signal.aborted) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const parsed = parseSseBuffer(buffer);
    buffer = parsed.rest;
    for (const event of parsed.events) {
      dispatchEvent(event, handlers);
    }
  }
}

function dispatchEvent(
  event: SseEvent,
  handlers: {
    onStep: (step: TraceStep) => void;
    onReport: (report: ResearchReport) => void;
    onError: (detail: string) => void;
  },
) {
  if (!event.data) {
    return;
  }
  const payload = JSON.parse(event.data) as unknown;
  if (event.event === "step") {
    handlers.onStep(payload as TraceStep);
  } else if (event.event === "report") {
    handlers.onReport(payload as ResearchReport);
  } else if (event.event === "error") {
    const detail = (payload as { detail?: string }).detail;
    handlers.onError(detail || "The research run failed.");
  }
}
