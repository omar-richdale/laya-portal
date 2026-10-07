// Mirror the public request contract; OpenAPI remains the machine-readable source.
export type Model = "auto" | "english" | "multilingual" | "typed-decisions";
export type Question = {
  type: "choice" | "score" | "noul";
  instructions: string;
  criteria?: Record<string, string> | string[];
};
export type Prediction = {
  state: unknown;
  questions: Record<string, Question>;
  model?: Model;
  max_len?: number;
  head_max_len?: number;
  min_confidence?: number;
};
export type Runtime = {
  ready: boolean;
  phase: string;
  device: string | null;
  resident_model: Model | null;
  default_model: Model;
  outstanding_jobs: number;
  max_jobs: number;
  load_ms: number | null;
  loading_model?: string | null;
  versions: Record<string, string>;
  revision: string;
  last_error: { code: string; message: string } | null;
  gpu: {
    name: string;
    free_bytes: number;
    total_bytes: number;
    allocated_bytes: number;
    peak_allocated_bytes: number;
  } | null;
};
export type Result = {
  answers: Record<string, Record<string, unknown>>;
  routing: { model: string; reason: string; repo?: string };
  usage?: Record<string, unknown>;
  runtime: {
    device: string;
    elapsed_ms: number;
    load_ms: number;
    warnings: string[];
    revision: string;
  };
};
export type ModelInfo = {
  id: Model;
  title: string;
  description: string;
  context: number;
  head: number;
  downloaded: boolean;
  resident: boolean;
  revision: string;
};
