export type TraceStep = {
  node: string;
  title: string;
  detail: string;
  items: string[];
};

export type Source = {
  id: string;
  citation_index: number;
  title: string;
  url: string;
  snippet: string;
  origin: string;
};

export type Critique = {
  approved: boolean;
  summary: string;
  issues: string[];
  revision_instructions: string;
  citation_score: number;
};

export type ResearchReport = {
  question: string;
  sub_questions: { id: string; text: string }[];
  sources: Source[];
  findings: { sub_question_id: string; claim: string; source_ids: string[]; excerpt: string }[];
  markdown: string;
  critique: Critique;
  revision_count: number;
  trace: TraceStep[];
  llm_provider: string;
  search_provider: string;
};

export type Health = {
  status: string;
  llm_provider: string;
  search_provider: string;
  llm_model: string;
  search_name: string;
};

export type SseEvent = {
  event: string;
  data: string;
};
