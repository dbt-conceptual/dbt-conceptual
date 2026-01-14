export interface Domain {
  name: string;
  display_name: string;
  color?: string;
}

export interface Concept {
  name: string;
  description?: string;  // Markdown description
  domain?: string;
  owner?: string;
  status?: 'draft' | 'complete' | 'stub' | 'deprecated';
  color?: string;  // Optional color override (defaults to domain color)
  bronze_models: string[];  // Source dependencies from manifest.json
  silver_models: string[];
  gold_models: string[];
}

export interface Relationship {
  name: string;
  from_concept: string;
  to_concept: string;
  cardinality?: string;
  description?: string;  // Markdown description
  realized_by: string[];
}

export interface State {
  domains: Record<string, Domain>;
  concepts: Record<string, Concept>;
  relationships: Record<string, Relationship>;
}
