export type NormalizeResponse = {
  regex: string;
  normalized: string;
  alphabet: string[];
};

export type SyntaxTreeNode = {
  id: number;
  value: string;
  serial_number: number | null;
  left_id: number | null;
  right_id: number | null;
  nullable: boolean;
  first_pos: number[];
  last_pos: number[];
  follow_pos: number[];
};

export type SyntaxTreeResponse = {
  regex: string;
  normalized: string;
  alphabet: string[];
  root_id: number;
  nodes: SyntaxTreeNode[];
};

export type Transition = {
  src: string;
  symbol: string;
  dst: string[];
};

export type AutomatonResponse = {
  kind: string;
  states: string[];
  alphabet: string[];
  initial_state: string;
  final_states: string[];
  transitions: Transition[];
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      detail = data?.detail ?? detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

export function normalizeRegex(regex: string) {
  return postJson<NormalizeResponse>("/api/v1/regex/normalize", { regex });
}

export function syntaxTree(regex: string) {
  return postJson<SyntaxTreeResponse>("/api/v1/regex/syntax-tree", { regex });
}

export function toDfa(regex: string) {
  return postJson<AutomatonResponse>("/api/v1/regex/to-dfa", { regex });
}
