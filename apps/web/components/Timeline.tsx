import type { TraceStep } from "@/lib/types";

type TimelineProps = {
  steps: TraceStep[];
  running: boolean;
};

export function Timeline({ steps, running }: TimelineProps) {
  if (steps.length === 0 && !running) {
    return (
      <section className="panel empty-run">
        <h2>How a run moves</h2>
        <ol className="roles">
          <li>
            <strong>Planner</strong> splits the question into sub-questions.
          </li>
          <li>
            <strong>Researcher</strong> searches each one and writes cited findings.
          </li>
          <li>
            <strong>Writer</strong> drafts the brief from those findings.
          </li>
          <li>
            <strong>Critic</strong> checks the citations and can send the draft back once.
          </li>
        </ol>
      </section>
    );
  }

  return (
    <section className="panel" aria-live="polite">
      <h2>Run</h2>
      <ol className="timeline">
        {steps.map((step, index) => {
          const revision = step.title.toLowerCase().includes("revision");
          return (
            <li key={`${step.node}-${index}`} className={revision ? "warn" : undefined}>
              <span className="node">{step.node}</span>
              <div>
                <h3>{step.title}</h3>
                <p>{step.detail}</p>
                {step.items.length > 0 ? (
                  <ul>
                    {step.items.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            </li>
          );
        })}
        {running ? (
          <li className="pending">
            <span className="node">…</span>
            <div>
              <h3>Working</h3>
              <p>The next agent has not finished yet.</p>
            </div>
          </li>
        ) : null}
      </ol>
    </section>
  );
}
