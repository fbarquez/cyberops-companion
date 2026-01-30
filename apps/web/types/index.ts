// User types
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export type UserRole = "admin" | "manager" | "lead" | "analyst";

// Incident types
export interface Incident {
  id: string;
  title: string;
  description?: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  detection_source?: DetectionSource;
  initial_indicator?: string;
  current_phase: IRPhase;
  created_by: string;
  assigned_to?: string;
  analyst_name?: string;
  analyst_email?: string;
  created_at: string;
  updated_at?: string;
  detected_at?: string;
  contained_at?: string;
  eradicated_at?: string;
  closed_at?: string;
  affected_systems: AffectedSystem[];
  phase_history: Record<string, string>;
}

export type IncidentStatus = "draft" | "active" | "contained" | "eradicated" | "recovered" | "closed";
export type IncidentSeverity = "critical" | "high" | "medium" | "low" | "informational";
export type DetectionSource = "user_report" | "edr_alert" | "siem_alert" | "anomaly_detection" | "external_notification" | "scheduled_scan" | "other";
export type IRPhase = "detection" | "analysis" | "containment" | "eradication" | "recovery" | "post_incident";

export interface AffectedSystem {
  id: string;
  hostname: string;
  ip_address?: string;
  os_type?: string;
  department?: string;
  criticality: string;
  added_at: string;
  notes?: string;
}

// Evidence types
export interface EvidenceEntry {
  id: string;
  entry_id: string;
  incident_id: string;
  sequence_number: number;
  previous_hash?: string;
  entry_hash: string;
  entry_type: EvidenceType;
  phase: string;
  description: string;
  artifacts?: ArtifactReference[];
  decision_id?: string;
  decision_option?: string;
  decision_rationale?: string;
  operator: string;
  tags: string[];
  timestamp: string;
  created_by: string;
}

export type EvidenceType = "observation" | "action" | "decision" | "artifact" | "note" | "system";

export interface ArtifactReference {
  filename: string;
  original_path?: string;
  file_hash_sha256: string;
  file_size_bytes: number;
  collected_at: string;
  collection_method?: string;
  notes?: string;
}

// Checklist types
export interface ChecklistItem {
  id: string;
  item_id: string;
  phase: string;
  text: string;
  help_text?: string;
  warning?: string;
  mandatory: boolean;
  forensic_critical: boolean;
  order: number;
  depends_on: string[];
  blocks: string[];
  status: ChecklistStatus;
  completed_at?: string;
  completed_by?: string;
  notes?: string;
  skip_reason?: string;
  is_blocked: boolean;
  blockers: string[];
}

export type ChecklistStatus = "not_started" | "in_progress" | "completed" | "skipped" | "not_applicable";

export interface ChecklistPhase {
  incident_id: string;
  phase: string;
  items: ChecklistItem[];
  total_items: number;
  completed_items: number;
  mandatory_total: number;
  mandatory_completed: number;
  progress_percent: number;
  can_advance: boolean;
  blocked_items: string[];
}

// Decision types
export interface DecisionTree {
  id: string;
  tree_id: string;
  phase: string;
  name: string;
  description?: string;
  entry_node_id: string;
  current_node_id?: string;
  completed: boolean;
  path_taken: string[];
  total_nodes: number;
  completed_nodes: number;
}

export interface DecisionNode {
  id: string;
  node_id: string;
  tree_id: string;
  phase: string;
  title: string;
  question: string;
  context?: string;
  help_text?: string;
  options: DecisionOption[];
  is_entry_node: boolean;
  is_available: boolean;
  blocked_by: string[];
}

export interface DecisionOption {
  id: string;
  label: string;
  description?: string;
  confidence?: ConfidenceLevel;
  recommended: boolean;
  warning?: string;
  next_node_id?: string;
  next_phase?: string;
  checklist_items_to_complete: string[];
  modifies_evidence: boolean;
  requires_confirmation: boolean;
}

export type ConfidenceLevel = "high" | "medium" | "low";

export interface DecisionPath {
  id: string;
  incident_id: string;
  tree_id: string;
  node_id: string;
  selected_option_id: string;
  selected_option_label: string;
  confidence?: ConfidenceLevel;
  rationale?: string;
  decided_by: string;
  decided_at: string;
  next_node_id?: string;
  next_phase?: string;
  modifies_evidence: boolean;
  requires_confirmation: boolean;
  was_confirmed: boolean;
}

// Phase types
export interface PhaseProgress {
  incident_id: string;
  phase: IRPhase;
  status: PhaseStatus;
  checklist_total: number;
  checklist_completed: number;
  mandatory_total: number;
  mandatory_completed: number;
  decisions_required: number;
  decisions_made: number;
  evidence_count: number;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  progress_percent: number;
  can_advance: boolean;
}

export type PhaseStatus = "not_started" | "in_progress" | "completed" | "skipped";

// Compliance types
export interface ComplianceFramework {
  id: string;
  name: string;
  description: string;
  version: string;
  controls_count: number;
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}
