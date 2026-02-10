-- Herd Operational Schema Initialization
-- Creates all 26 tables for the Herd MCP Server operational database

CREATE SCHEMA IF NOT EXISTS herd;

-- ============================================================================
-- ENTITY DEFINITIONS (12 tables)
-- ============================================================================

CREATE TABLE IF NOT EXISTS herd.initiative_def (
    initiative_code TEXT PRIMARY KEY,
    initiative_title TEXT NOT NULL,
    initiative_description TEXT,
    initiative_status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS herd.project_def (
    project_code TEXT PRIMARY KEY,
    initiative_code TEXT,
    project_title TEXT NOT NULL,
    project_description TEXT,
    project_status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS herd.agent_def (
    agent_code TEXT PRIMARY KEY,
    agent_role TEXT NOT NULL,
    agent_status TEXT NOT NULL,
    agent_branch_prefix TEXT NOT NULL,
    agent_email TEXT,
    default_model_code TEXT,
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS herd.model_def (
    model_code TEXT PRIMARY KEY,
    model_provider TEXT NOT NULL,
    model_context_window INTEGER NOT NULL,
    model_input_cost_per_m DECIMAL(10, 2) NOT NULL,
    model_output_cost_per_m DECIMAL(10, 2) NOT NULL,
    model_cache_read_cost_per_m DECIMAL(10, 2),
    model_cache_create_cost_per_m DECIMAL(10, 2),
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS herd.craft_def (
    craft_code TEXT PRIMARY KEY,
    craft_description TEXT,
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS herd.personality_def (
    personality_code TEXT PRIMARY KEY,
    personality_description TEXT,
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS herd.skillset_def (
    skillset_code TEXT PRIMARY KEY,
    skillset_description TEXT,
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS herd.sprint_def (
    sprint_code TEXT PRIMARY KEY,
    sprint_title TEXT NOT NULL,
    sprint_goal TEXT,
    sprint_started_at TIMESTAMP,
    sprint_planned_end_at TIMESTAMP,
    sprint_actual_end_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS herd.ticket_def (
    ticket_code TEXT PRIMARY KEY,
    project_code TEXT,
    ticket_title TEXT NOT NULL,
    ticket_description TEXT,
    ticket_tshirt_size TEXT,
    ticket_acceptance_criteria TEXT,
    ticket_current_status TEXT NOT NULL,
    current_sprint_code TEXT,
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS herd.pr_def (
    pr_code TEXT PRIMARY KEY,
    ticket_code TEXT,
    creator_agent_instance_code TEXT,
    pr_branch_name TEXT NOT NULL,
    pr_title TEXT NOT NULL,
    pr_lines_added INTEGER,
    pr_lines_deleted INTEGER,
    pr_files_changed INTEGER,
    pr_merged_at TIMESTAMP,
    pr_closed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS herd.review_def (
    review_code TEXT PRIMARY KEY,
    pr_code TEXT NOT NULL,
    reviewer_agent_instance_code TEXT NOT NULL,
    review_round INTEGER NOT NULL,
    review_verdict TEXT NOT NULL,
    review_duration_minutes DECIMAL(10, 2),
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS herd.review_finding (
    review_finding_code TEXT PRIMARY KEY,
    review_code TEXT NOT NULL,
    finding_category TEXT NOT NULL,
    finding_severity TEXT NOT NULL,
    finding_description TEXT NOT NULL,
    finding_file_path TEXT,
    finding_line_number INTEGER,
    finding_pattern_id TEXT,
    finding_outcome TEXT,
    created_at TIMESTAMP NOT NULL
);

-- ============================================================================
-- VERSIONED CONTENT (3 tables - IMMUTABLE)
-- ============================================================================

CREATE TABLE IF NOT EXISTS herd.craft_version (
    craft_version_code TEXT PRIMARY KEY,
    craft_code TEXT NOT NULL,
    craft_version_content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS herd.personality_version (
    personality_version_code TEXT PRIMARY KEY,
    personality_code TEXT NOT NULL,
    personality_version_content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS herd.skillset_version (
    skillset_version_code TEXT PRIMARY KEY,
    skillset_code TEXT NOT NULL,
    skillset_version_content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

-- ============================================================================
-- SKILLS (3 tables - individual fetchable skills composing into skillsets)
-- ============================================================================

CREATE TABLE IF NOT EXISTS herd.skill_def (
    skill_code TEXT PRIMARY KEY,
    skill_description TEXT,
    skill_source_url TEXT,
    skill_source_type TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS herd.skill_version (
    skill_version_code TEXT PRIMARY KEY,
    skill_code TEXT NOT NULL,
    skill_version_content TEXT NOT NULL,
    skill_source_url TEXT,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS herd.skill_skillset (
    skill_code TEXT NOT NULL,
    skillset_code TEXT NOT NULL,
    skill_order INTEGER,
    created_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP,
    PRIMARY KEY (skill_code, skillset_code)
);

-- ============================================================================
-- INSTANCE (1 table)
-- ============================================================================

CREATE TABLE IF NOT EXISTS herd.agent_instance (
    agent_instance_code TEXT PRIMARY KEY,
    agent_code TEXT NOT NULL,
    model_code TEXT NOT NULL,
    craft_version_code TEXT,
    personality_version_code TEXT,
    ticket_code TEXT,
    spawned_by_agent_instance_code TEXT,
    agent_instance_started_at TIMESTAMP NOT NULL,
    agent_instance_ended_at TIMESTAMP,
    agent_instance_outcome TEXT
);

-- ============================================================================
-- JUNCTION TABLES (2 tables)
-- ============================================================================

CREATE TABLE IF NOT EXISTS herd.agent_skillset (
    agent_code TEXT NOT NULL,
    skillset_code TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP,
    PRIMARY KEY (agent_code, skillset_code)
);

CREATE TABLE IF NOT EXISTS herd.agent_instance_skillset (
    agent_instance_code TEXT NOT NULL,
    skillset_version_code TEXT NOT NULL,
    PRIMARY KEY (agent_instance_code, skillset_version_code)
);

-- ============================================================================
-- ACTIVITY LEDGERS (5 tables - INSERT-ONLY)
-- ============================================================================

CREATE TABLE IF NOT EXISTS herd.agent_instance_lifecycle_activity (
    agent_instance_code TEXT NOT NULL,
    lifecycle_event_type TEXT NOT NULL,
    lifecycle_detail TEXT,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS herd.agent_instance_ticket_activity (
    agent_instance_code TEXT NOT NULL,
    ticket_code TEXT NOT NULL,
    ticket_event_type TEXT NOT NULL,
    ticket_status TEXT,
    sprint_code TEXT,
    blocker_ticket_code TEXT,
    blocker_description TEXT,
    handoff_to_agent_code TEXT,
    ticket_activity_comment TEXT,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS herd.agent_instance_pr_activity (
    agent_instance_code TEXT NOT NULL,
    pr_code TEXT NOT NULL,
    pr_event_type TEXT NOT NULL,
    pr_commit_hash TEXT,
    pr_push_lines_added INTEGER,
    pr_push_lines_deleted INTEGER,
    pr_activity_detail TEXT,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS herd.agent_instance_review_activity (
    agent_instance_code TEXT NOT NULL,
    review_code TEXT NOT NULL,
    pr_code TEXT NOT NULL,
    review_event_type TEXT NOT NULL,
    review_finding_code TEXT,
    review_activity_detail TEXT,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS herd.agent_instance_token_activity (
    agent_instance_code TEXT NOT NULL,
    model_code TEXT NOT NULL,
    token_input_count INTEGER,
    token_output_count INTEGER,
    token_cache_read_count INTEGER,
    token_cache_create_count INTEGER,
    token_cost_usd DECIMAL(10, 6),
    token_context_utilization_pct DECIMAL(5, 2),
    created_at TIMESTAMP NOT NULL
);

-- ============================================================================
-- REFLEXIVE LEARNING (2 tables - agent self-awareness and decision tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS herd.agent_observation (
    observation_id TEXT PRIMARY KEY,
    agent_code TEXT NOT NULL,
    session_code TEXT,
    observation_type TEXT NOT NULL,
    observation_content TEXT NOT NULL,
    confidence FLOAT,
    created_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS herd.decision_record (
    decision_id TEXT PRIMARY KEY,
    decision_type TEXT NOT NULL,
    context TEXT,
    decision TEXT NOT NULL,
    rationale TEXT,
    alternatives_considered TEXT,
    decided_by TEXT NOT NULL,
    ticket_code TEXT,
    created_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP
);
