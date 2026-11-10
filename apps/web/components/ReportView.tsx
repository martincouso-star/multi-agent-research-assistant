import ReactMarkdown from "react-markdown";

import { isHttpUrl } from "@/lib/api";
import type { ResearchReport } from "@/lib/types";

type ReportViewProps = {
  report: ResearchReport | null;
};

export function ReportView({ report }: ReportViewProps) {
  if (!report) {
    return (
      <section className="panel brief" id="brief">
        <h2>Brief</h2>
        <p className="hint">The cited brief shows up here when the critic finishes.</p>
      </section>
    );
  }

  const { critique } = report;
  return (
    <section className="panel brief" id="brief">
      <p className={critique.approved ? "status ok" : "status warn"}>
        {critique.approved ? "Critic approved the brief." : "Critic left the brief unapproved."}{" "}
        {critique.summary}
      </p>
      {report.revision_count > 0 ? (
        <p className="hint">
          Writer revisions: {report.revision_count}. Citation resolution:{" "}
          {critique.citation_score.toFixed(2)}.
        </p>
      ) : (
        <p className="hint">Citation resolution: {critique.citation_score.toFixed(2)}.</p>
      )}
      {critique.issues.length > 0 ? (
        <ul className="issues">
          {critique.issues.map((issue) => (
            <li key={issue}>{issue}</li>
          ))}
        </ul>
      ) : null}

      <h2>{report.question}</h2>
      <div className="markdown">
        <ReactMarkdown
          components={{
            h2: ({ children }) => <h3>{children}</h3>,
            h3: ({ children }) => <h4>{children}</h4>,
            a: ({ href, children }) => {
              const external = typeof href === "string" && isHttpUrl(href);
              return (
                <a
                  href={href}
                  target={external ? "_blank" : undefined}
                  rel={external ? "noreferrer" : undefined}
                >
                  {children}
                </a>
              );
            },
          }}
        >
          {report.markdown}
        </ReactMarkdown>
      </div>

      <h3>Sources</h3>
      <ol className="sources">
        {report.sources.map((source) => (
          <li key={source.id}>
            <div className="source-title">
              {isHttpUrl(source.url) ? (
                <a href={source.url} target="_blank" rel="noreferrer">
                  {source.title}
                </a>
              ) : (
                <span>{source.title}</span>
              )}
              <span className="origin">{source.origin}</span>
            </div>
            <p>{source.snippet}</p>
            <p className="source-url">{source.url}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
