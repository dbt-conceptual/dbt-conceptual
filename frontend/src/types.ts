// TypeScript types for dbt-conceptual
// Based on Flask API contract and spec-application.md Section 3

export type ConceptStatus = 'stub' | 'draft' | 'complete' | 'deprecated';
export type RelationshipStatus = 'stub' | 'draft' | 'complete';
export type Cardinality = '1:1' | '1:N' | 'N:M';

export interface Domain {
  name: string;
  display_name: string;
  color?: string;
}

export interface Concept {
  name: string;
  domain?: string;
  owner?: string;
  definition?: string;
  status: ConceptStatus; // Derived at runtime
  color?: string;
  replaced_by?: string;
  bronze_models: string[];
  silver_models: string[];
  gold_models: string[];
}

export interface Relationship {
  name: string; // Derived or custom
  verb: string;
  from_concept: string;
  to_concept: string;
  cardinality?: Cardinality;
  domains: string[];
  owner?: string;
  definition?: string;
  custom_name?: string;
  status: RelationshipStatus; // Derived at runtime
  realized_by: string[];
}

export interface Position {
  x: number;
  y: number;
}

export interface ProjectState {
  domains: Record<string, Domain>;
  concepts: Record<string, Concept>;
  relationships: Record<string, Relationship>;
  positions: Record<string, Position>; // React Flow positions by concept ID
}

export interface Settings {
  domains: Record<string, Omit<Domain, 'display_name'>>;
  paths: {
    gold_paths: string[];
    silver_paths: string[];
    bronze_paths: string[];
  };
  conceptual_path: string;
}

export interface SyncResponse {
  success: boolean;
  created_stubs: string[];
  updated_counts: Record<string, { silver: number; gold: number; bronze: number }>;
  message: string;
}

// React Flow types
export interface ConceptNode {
  id: string;
  type: 'concept';
  position: Position;
  data: {
    concept: Concept;
  };
}

export interface RelationshipEdge {
  id: string;
  type: 'relationship';
  source: string;
  target: string;
  data: {
    relationship: Relationship;
  };
}

// Tool types
export type Tool = 'select' | 'concept' | 'relationship';
