import { EXAMPLE_QUESTIONS } from "@/lib/examples";

type QuestionFormProps = {
  question: string;
  notes: string;
  running: boolean;
  onQuestion: (value: string) => void;
  onNotes: (value: string) => void;
  onSubmit: () => void;
};

export function QuestionForm({
  question,
  notes,
  running,
  onQuestion,
  onNotes,
  onSubmit,
}: QuestionFormProps) {
  const ready = question.trim().length >= 8 && !running;

  return (
    <form
      className="panel composer"
      onSubmit={(event) => {
        event.preventDefault();
        if (ready) {
          onSubmit();
        }
      }}
    >
      <label htmlFor="question">Research question</label>
      <textarea
        id="question"
        name="question"
        value={question}
        maxLength={2000}
        rows={5}
        placeholder="Ask a question the agents can break apart and source."
        onChange={(event) => onQuestion(event.target.value)}
        onKeyDown={(event) => {
          if ((event.metaKey || event.ctrlKey) && event.key === "Enter" && ready) {
            event.preventDefault();
            onSubmit();
          }
        }}
      />
      <p className="hint">At least 8 characters. Press Cmd or Ctrl plus Enter to run.</p>

      <label htmlFor="notes">Notes (optional)</label>
      <textarea
        id="notes"
        name="notes"
        value={notes}
        maxLength={8000}
        rows={3}
        placeholder="Paste a passage to include as a local source."
        onChange={(event) => onNotes(event.target.value)}
      />

      <div className="examples" aria-label="Example questions">
        {EXAMPLE_QUESTIONS.map((example) => (
          <button
            key={example}
            type="button"
            className="example"
            onClick={() => onQuestion(example)}
          >
            {example}
          </button>
        ))}
      </div>
      <p className="hint">
        The default mock search uses a small local corpus. These questions match it.
      </p>

      <button type="submit" className="primary" disabled={!ready}>
        {running ? "Researching" : "Run research"}
      </button>
    </form>
  );
}
