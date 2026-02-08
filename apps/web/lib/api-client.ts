const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface RequestOptions extends RequestInit {
  token?: string;
}

// Rate limit information from response headers
export interface RateLimitInfo {
  limit: number;
  remaining: number;
  resetAt: number;
  retryAfter?: number;
}

// Rate limit event listeners
type RateLimitListener = (info: RateLimitInfo) => void;
const rateLimitListeners: Set<RateLimitListener> = new Set();

export function onRateLimitExceeded(listener: RateLimitListener): () => void {
  rateLimitListeners.add(listener);
  return () => rateLimitListeners.delete(listener);
}

function notifyRateLimitExceeded(info: RateLimitInfo): void {
  rateLimitListeners.forEach((listener) => listener(info));
}

class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "APIError";
  }
}

export class RateLimitError extends APIError {
  constructor(
    message: string,
    public rateLimitInfo: RateLimitInfo
  ) {
    super(429, message);
    this.name = "RateLimitError";
  }
}

// Parse rate limit headers from response
function parseRateLimitHeaders(response: Response): RateLimitInfo | null {
  const limit = response.headers.get("X-RateLimit-Limit");
  const remaining = response.headers.get("X-RateLimit-Remaining");
  const resetAt = response.headers.get("X-RateLimit-Reset");
  const retryAfter = response.headers.get("Retry-After");

  if (!limit || !remaining || !resetAt) {
    return null;
  }

  return {
    limit: parseInt(limit, 10),
    remaining: parseInt(remaining, 10),
    resetAt: parseInt(resetAt, 10),
    retryAfter: retryAfter ? parseInt(retryAfter, 10) : undefined,
  };
}

async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { token, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  if (!response.ok) {
    // Handle rate limit error (429)
    if (response.status === 429) {
      const error = await response.json().catch(() => ({
        detail: "Rate limit exceeded",
        error: { limit: 0, retry_after: 60, reset_at: 0 },
      }));

      const rateLimitInfo: RateLimitInfo = {
        limit: error.error?.limit || 0,
        remaining: 0,
        resetAt: error.error?.reset_at || 0,
        retryAfter: error.error?.retry_after || 60,
      };

      // Notify listeners
      notifyRateLimitExceeded(rateLimitInfo);

      throw new RateLimitError(
        error.error?.message || "Too many requests. Please try again later.",
        rateLimitInfo
      );
    }

    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new APIError(response.status, error.detail || "Request failed");
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

// Auth
export const authAPI = {
  login: (email: string, password: string) =>
    request<{ access_token: string; refresh_token: string }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  register: (data: { email: string; password: string; full_name: string }) =>
    request("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  me: (token: string) =>
    request("/api/v1/auth/me", { token }),

  refresh: (refreshToken: string) =>
    request<{ access_token: string; refresh_token: string }>("/api/v1/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),
};

// SSO
export interface SSOProvider {
  slug: string;
  name: string;
  icon?: string;
  button_text?: string;
}

export interface SSOAuthorizeResponse {
  authorization_url: string;
  state: string;
}

export interface SSOCallbackResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    full_name: string;
    role: string;
    sso_provider?: string;
    is_new_user: boolean;
  };
}

export const ssoAPI = {
  getProviders: () =>
    request<{ providers: SSOProvider[] }>("/api/v1/auth/sso/providers"),

  getAuthorizeUrl: (provider: string, redirectUri?: string) => {
    const params = new URLSearchParams();
    if (redirectUri) params.set("redirect_uri", redirectUri);
    const query = params.toString();
    return request<SSOAuthorizeResponse>(
      `/api/v1/auth/sso/${provider}/authorize${query ? `?${query}` : ""}`
    );
  },

  callback: (provider: string, code: string, state: string) =>
    request<SSOCallbackResponse>(`/api/v1/auth/sso/${provider}/callback`, {
      method: "POST",
      body: JSON.stringify({ code, state }),
    }),

  unlink: (provider: string, token: string) =>
    request<{ message: string }>(`/api/v1/auth/sso/${provider}/unlink`, {
      method: "POST",
      token,
    }),
};

// Incidents
export const incidentsAPI = {
  list: (token: string, params?: { status?: string; page?: number; size?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    return request(`/api/v1/incidents?${query}`, { token });
  },

  get: (token: string, id: string) =>
    request(`/api/v1/incidents/${id}`, { token }),

  create: (token: string, data: any) =>
    request("/api/v1/incidents", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (token: string, id: string, data: any) =>
    request(`/api/v1/incidents/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    request(`/api/v1/incidents/${id}`, {
      method: "DELETE",
      token,
    }),

  addSystem: (token: string, id: string, data: any) =>
    request(`/api/v1/incidents/${id}/systems`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  advancePhase: (token: string, id: string, force: boolean = false) =>
    request(`/api/v1/incidents/${id}/advance-phase?force=${force}`, {
      method: "POST",
      token,
    }),

  getSummary: (token: string, id: string) =>
    request(`/api/v1/incidents/${id}/summary`, { token }),

  getTimeline: (token: string, id: string) =>
    request(`/api/v1/incidents/${id}/timeline`, { token }),
};

// Evidence
export const evidenceAPI = {
  list: (token: string, incidentId: string, params?: { phase?: string; entry_type?: string }) => {
    const query = new URLSearchParams();
    if (params?.phase) query.set("phase", params.phase);
    if (params?.entry_type) query.set("entry_type", params.entry_type);
    return request(`/api/v1/incidents/${incidentId}/evidence?${query}`, { token });
  },

  create: (token: string, incidentId: string, data: any) =>
    request(`/api/v1/incidents/${incidentId}/evidence`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getChain: (token: string, incidentId: string) =>
    request(`/api/v1/incidents/${incidentId}/evidence/chain`, { token }),

  verify: (token: string, incidentId: string) =>
    request(`/api/v1/incidents/${incidentId}/evidence/verify`, {
      method: "POST",
      token,
    }),

  export: (token: string, incidentId: string, format: string = "markdown") =>
    request(`/api/v1/incidents/${incidentId}/evidence/export?format=${format}`, { token }),
};

// Checklists
export const checklistsAPI = {
  get: (token: string, incidentId: string, phase: string) =>
    request(`/api/v1/incidents/${incidentId}/checklists/${phase}`, { token }),

  complete: (token: string, incidentId: string, phase: string, itemId: string, notes?: string) =>
    request(`/api/v1/incidents/${incidentId}/checklists/${phase}/items/${itemId}/complete`, {
      method: "POST",
      body: JSON.stringify({ notes }),
      token,
    }),

  skip: (token: string, incidentId: string, phase: string, itemId: string, reason: string) =>
    request(`/api/v1/incidents/${incidentId}/checklists/${phase}/items/${itemId}/skip`, {
      method: "POST",
      body: JSON.stringify({ skip_reason: reason }),
      token,
    }),

  canAdvance: (token: string, incidentId: string, phase: string) =>
    request(`/api/v1/incidents/${incidentId}/checklists/${phase}/can-advance`, {
      method: "POST",
      token,
    }),
};

// Decisions
export const decisionsAPI = {
  getTrees: (token: string, incidentId: string, phase: string, lang: string = "en") =>
    request(`/api/v1/incidents/${incidentId}/decisions/trees?phase=${phase}&lang=${lang}`, { token }),

  getTree: (token: string, incidentId: string, treeId: string, lang: string = "en") =>
    request(`/api/v1/incidents/${incidentId}/decisions/trees/${treeId}?lang=${lang}`, { token }),

  getCurrentNode: (token: string, incidentId: string, treeId: string, lang: string = "en") =>
    request(`/api/v1/incidents/${incidentId}/decisions/trees/${treeId}/current-node?lang=${lang}`, { token }),

  decide: (token: string, incidentId: string, treeId: string, optionId: string, rationale?: string, confirm: boolean = false) =>
    request(`/api/v1/incidents/${incidentId}/decisions/trees/${treeId}/decide`, {
      method: "POST",
      body: JSON.stringify({ option_id: optionId, rationale, confirm }),
      token,
    }),

  getHistory: (token: string, incidentId: string) =>
    request(`/api/v1/incidents/${incidentId}/decisions/history`, { token }),
};

// Compliance
export const complianceAPI = {
  getFrameworks: (token: string) =>
    request("/api/v1/compliance/frameworks", { token }),

  getFramework: (token: string, frameworkId: string) =>
    request(`/api/v1/compliance/frameworks/${frameworkId}`, { token }),

  validate: (token: string, incidentId: string, phase: string, frameworks: string[]) =>
    request("/api/v1/compliance/validate", {
      method: "POST",
      body: JSON.stringify({ incident_id: incidentId, phase, frameworks }),
      token,
    }),

  validateIncident: (token: string, incidentId: string, frameworks: string[]) =>
    request("/api/v1/compliance/validate/incident", {
      method: "POST",
      body: JSON.stringify({ incident_id: incidentId, frameworks }),
      token,
    }),

  getCrossMapping: (token: string, phase?: string) => {
    const query = phase ? `?phase=${phase}` : "";
    return request(`/api/v1/compliance/cross-mapping${query}`, { token });
  },

  getEquivalentControls: (token: string, controlId: string, framework: string) =>
    request(`/api/v1/compliance/cross-mapping/equivalent?control_id=${controlId}&framework=${framework}`, { token }),

  getControlDetails: (token: string, controlId: string, framework: string) =>
    request(`/api/v1/compliance/cross-mapping/control/${controlId}?framework=${framework}`, { token }),

  getReport: (token: string, incidentId: string, frameworks: string[]) =>
    request("/api/v1/compliance/report", {
      method: "POST",
      body: JSON.stringify({ incident_id: incidentId, frameworks }),
      token,
    }),

  exportReport: (token: string, incidentId: string, frameworks: string[], format: string = "markdown") =>
    request("/api/v1/compliance/report/export", {
      method: "POST",
      body: JSON.stringify({ incident_id: incidentId, frameworks, format }),
      token,
    }),

  // IOC Enrichment
  enrichIOC: (token: string, iocType: string, value: string) =>
    request("/api/v1/compliance/ioc/enrich", {
      method: "POST",
      body: JSON.stringify({ ioc_type: iocType, value }),
      token,
    }),

  enrichIOCBatch: (token: string, iocs: Array<{ type: string; value: string }>) =>
    request("/api/v1/compliance/ioc/enrich/batch", {
      method: "POST",
      body: JSON.stringify({ iocs }),
      token,
    }),

  getIOCTypes: (token: string) =>
    request("/api/v1/compliance/ioc/types", { token }),

  exportIOCResults: (token: string, iocs: Array<{ type: string; value: string }>, format: string = "json") =>
    request(`/api/v1/compliance/ioc/export?format=${format}`, {
      method: "POST",
      body: JSON.stringify({ iocs }),
      token,
    }),

  // BSI Meldung
  generateBSIMeldung: (token: string, data: {
    incident_id: string;
    incident_title: string;
    incident_description: string;
    incident_type: string;
    severity: string;
    detected_at: string;
    kritis_sector?: string;
    affected_systems?: Array<{ name: string; type: string; criticality: string }>;
    is_kritis?: boolean;
    contact_name?: string;
    contact_email?: string;
    contact_phone?: string;
    contact_organization?: string;
  }) =>
    request("/api/v1/compliance/bsi/generate", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getBSISectors: (token: string) =>
    request("/api/v1/compliance/bsi/sectors", { token }),

  getBSICategories: (token: string) =>
    request("/api/v1/compliance/bsi/categories", { token }),

  getBSIDeadlines: (token: string, detectedAt: string, isKritis: boolean = false) =>
    request(`/api/v1/compliance/bsi/deadlines?detected_at=${detectedAt}&is_kritis=${isKritis}`, { token }),

  // NIS2 Directive
  createNIS2Notification: (token: string, data: {
    incident_id: string;
    incident_title: string;
    incident_description: string;
    severity: string;
    detected_at: string;
    sector: string;
    member_state: string;
    entity_name: string;
    contact_name: string;
    contact_email: string;
    contact_phone?: string;
    contact_role?: string;
    affected_services?: string[];
    affected_users?: number;
    affected_countries?: string[];
    data_breach?: boolean;
    financial_impact?: number;
  }) =>
    request("/api/v1/compliance/nis2/notifications", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getNIS2Notification: (token: string, notificationId: string) =>
    request(`/api/v1/compliance/nis2/notifications/${notificationId}`, { token }),

  submitNIS2EarlyWarning: (token: string, notificationId: string, data: {
    initial_assessment: string;
    suspected_cause?: string;
    cross_border?: boolean;
  }) =>
    request(`/api/v1/compliance/nis2/notifications/${notificationId}/early-warning?initial_assessment=${encodeURIComponent(data.initial_assessment)}&cross_border=${data.cross_border || false}`, {
      method: "POST",
      token,
    }),

  submitNIS2IncidentNotification: (token: string, notificationId: string, data: {
    severity_assessment: string;
    root_cause?: string;
    mitigation_measures?: string[];
  }) =>
    request(`/api/v1/compliance/nis2/notifications/${notificationId}/incident-notification?severity_assessment=${encodeURIComponent(data.severity_assessment)}`, {
      method: "POST",
      token,
    }),

  submitNIS2FinalReport: (token: string, notificationId: string, data: {
    detailed_description: string;
    threat_type: string;
    root_cause_analysis: string;
    mitigation_applied: string[];
    lessons_learned: string[];
  }) =>
    request(`/api/v1/compliance/nis2/notifications/${notificationId}/final-report`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  exportNIS2Notification: (token: string, notificationId: string, format: string = "markdown") =>
    request(`/api/v1/compliance/nis2/notifications/${notificationId}/export?format=${format}`, { token }),

  getNIS2Sectors: (token: string) =>
    request("/api/v1/compliance/nis2/sectors", { token }),

  getNIS2MemberStates: (token: string) =>
    request("/api/v1/compliance/nis2/member-states", { token }),

  getNIS2Deadlines: (token: string, detectedAt: string) =>
    request(`/api/v1/compliance/nis2/deadlines?detected_at=${detectedAt}`, { token }),

  // OWASP Top 10
  getOWASPRisks: (token: string) =>
    request("/api/v1/compliance/owasp/risks", { token }),

  getOWASPRisk: (token: string, riskId: string) =>
    request(`/api/v1/compliance/owasp/risks/${riskId}`, { token }),

  getOWASPPhaseRecommendations: (token: string, phase: string) =>
    request(`/api/v1/compliance/owasp/phase/${phase}`, { token }),

  identifyOWASPRisks: (token: string, indicators: string[]) =>
    request("/api/v1/compliance/owasp/identify", {
      method: "POST",
      body: JSON.stringify({ indicators }),
      token,
    }),

  getOWASPRemediation: (token: string, riskId: string, context?: string) =>
    request("/api/v1/compliance/owasp/remediation", {
      method: "POST",
      body: JSON.stringify({ risk_id: riskId, context }),
      token,
    }),

  validateOWASPCompliance: (token: string, phase: string, incidentData: Record<string, unknown>) =>
    request(`/api/v1/compliance/owasp/validate/${phase}`, {
      method: "POST",
      body: JSON.stringify(incidentData),
      token,
    }),
};

// Tools
export const toolsAPI = {
  getPlaybookTypes: (token: string) =>
    request("/api/v1/tools/playbook/types", { token }),

  generatePlaybook: (token: string, data: any) =>
    request("/api/v1/tools/playbook/generate", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getTemplates: (token: string, lang: string = "en") =>
    request(`/api/v1/tools/templates?lang=${lang}`, { token }),

  getTemplate: (token: string, templateId: string, incidentId?: string) =>
    request(`/api/v1/tools/templates/${templateId}${incidentId ? `?incident_id=${incidentId}` : ""}`, { token }),

  getLessons: (token: string) =>
    request("/api/v1/tools/lessons", { token }),

  createLesson: (token: string, data: any) =>
    request("/api/v1/tools/lessons", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getMITRETechniques: (token: string, tactic?: string) => {
    const query = tactic ? `?tactic=${tactic}` : "";
    return request(`/api/v1/tools/mitre/techniques${query}`, { token });
  },

  getMITRETactics: (token: string) =>
    request("/api/v1/tools/mitre/tactics", { token }),

  getMITRETechnique: (token: string, techniqueId: string) =>
    request(`/api/v1/tools/mitre/techniques/${techniqueId}`, { token }),

  getRansomwareTechniques: (token: string) =>
    request("/api/v1/tools/mitre/ransomware-techniques", { token }),

  mapToMITRE: (token: string, incidentId: string, techniques: string[], notes?: string) =>
    request("/api/v1/tools/mitre/map", {
      method: "POST",
      body: JSON.stringify({ incident_id: incidentId, techniques, notes }),
      token,
    }),

  getSimulationScenarios: (token: string, difficulty?: string) => {
    const query = difficulty ? `?difficulty=${difficulty}` : "";
    return request(`/api/v1/tools/simulations/scenarios${query}`, { token });
  },

  getSimulationScenario: (token: string, scenarioId: string) =>
    request(`/api/v1/tools/simulations/scenarios/${scenarioId}`, { token }),

  startSimulation: (token: string, scenarioId: string) =>
    request(`/api/v1/tools/simulations/scenarios/${scenarioId}/start`, {
      method: "POST",
      token,
    }),

  getSimulationSession: (token: string, sessionId: string) =>
    request(`/api/v1/tools/simulations/sessions/${sessionId}`, { token }),

  completeSimulation: (token: string, sessionId: string) =>
    request(`/api/v1/tools/simulations/sessions/${sessionId}/complete`, {
      method: "POST",
      token,
    }),

  // Playbook
  getPlaybook: (token: string, playbookId: string) =>
    request(`/api/v1/tools/playbook/${playbookId}`, { token }),

  exportPlaybook: (token: string, playbookId: string, format: string = "markdown") =>
    request(`/api/v1/tools/playbook/${playbookId}/export?format=${format}`, { token }),
};

// Threat Intelligence
export const threatsAPI = {
  // IOCs
  listIOCs: (token: string, params?: {
    page?: number;
    page_size?: number;
    status?: string;
    type?: string;
    threat_level?: string;
    search?: string;
    incident_id?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    if (params?.status) query.set("status", params.status);
    if (params?.type) query.set("type", params.type);
    if (params?.threat_level) query.set("threat_level", params.threat_level);
    if (params?.search) query.set("search", params.search);
    if (params?.incident_id) query.set("incident_id", params.incident_id);
    return request(`/api/v1/threats/iocs?${query}`, { token });
  },

  getIOC: (token: string, id: string) =>
    request(`/api/v1/threats/iocs/${id}`, { token }),

  createIOC: (token: string, data: { value: string; type?: string; description?: string; tags?: string[]; source?: string }) =>
    request("/api/v1/threats/iocs", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  createIOCsBulk: (token: string, iocs: Array<{ value: string; type?: string; description?: string; tags?: string[] }>) =>
    request("/api/v1/threats/iocs/bulk", {
      method: "POST",
      body: JSON.stringify({ iocs }),
      token,
    }),

  updateIOC: (token: string, id: string, data: { status?: string; threat_level?: string; description?: string; tags?: string[] }) =>
    request(`/api/v1/threats/iocs/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      token,
    }),

  deleteIOC: (token: string, id: string) =>
    request(`/api/v1/threats/iocs/${id}`, {
      method: "DELETE",
      token,
    }),

  enrichIOC: (token: string, data: { value: string; type?: string; save?: boolean }) =>
    request("/api/v1/threats/iocs/enrich", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  enrichIOCsBatch: (token: string, iocs: string[], save: boolean = false) =>
    request("/api/v1/threats/iocs/enrich/batch", {
      method: "POST",
      body: JSON.stringify({ iocs, save }),
      token,
    }),

  reEnrichIOC: (token: string, id: string) =>
    request(`/api/v1/threats/iocs/${id}/re-enrich`, {
      method: "POST",
      token,
    }),

  // Threat Actors
  listActors: (token: string, params?: {
    is_active?: boolean;
    motivation?: string;
    sophistication?: string;
    search?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.is_active !== undefined) query.set("is_active", params.is_active.toString());
    if (params?.motivation) query.set("motivation", params.motivation);
    if (params?.sophistication) query.set("sophistication", params.sophistication);
    if (params?.search) query.set("search", params.search);
    return request(`/api/v1/threats/actors?${query}`, { token });
  },

  getActor: (token: string, id: string) =>
    request(`/api/v1/threats/actors/${id}`, { token }),

  createActor: (token: string, data: {
    name: string;
    aliases?: string[];
    motivation?: string;
    sophistication?: string;
    description?: string;
    country_of_origin?: string;
    target_sectors?: string[];
    mitre_techniques?: string[];
  }) =>
    request("/api/v1/threats/actors", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateActor: (token: string, id: string, data: any) =>
    request(`/api/v1/threats/actors/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      token,
    }),

  linkIOCToActor: (token: string, actorId: string, iocId: string) =>
    request(`/api/v1/threats/actors/${actorId}/iocs/${iocId}`, {
      method: "POST",
      token,
    }),

  // Campaigns
  listCampaigns: (token: string, params?: {
    is_active?: boolean;
    campaign_type?: string;
    search?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.is_active !== undefined) query.set("is_active", params.is_active.toString());
    if (params?.campaign_type) query.set("campaign_type", params.campaign_type);
    if (params?.search) query.set("search", params.search);
    return request(`/api/v1/threats/campaigns?${query}`, { token });
  },

  getCampaign: (token: string, id: string) =>
    request(`/api/v1/threats/campaigns/${id}`, { token }),

  createCampaign: (token: string, data: {
    name: string;
    campaign_type?: string;
    description?: string;
    target_sectors?: string[];
    mitre_techniques?: string[];
    actor_ids?: string[];
  }) =>
    request("/api/v1/threats/campaigns", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateCampaign: (token: string, id: string, data: any) =>
    request(`/api/v1/threats/campaigns/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      token,
    }),

  linkIOCToCampaign: (token: string, campaignId: string, iocId: string) =>
    request(`/api/v1/threats/campaigns/${campaignId}/iocs/${iocId}`, {
      method: "POST",
      token,
    }),

  // Stats
  getStats: (token: string) =>
    request("/api/v1/threats/stats", { token }),
};

// Vulnerability Management
export const vulnerabilitiesAPI = {
  // Assets
  listAssets: (token: string, params?: {
    page?: number;
    page_size?: number;
    search?: string;
    asset_type?: string;
    criticality?: string;
    environment?: string;
    is_active?: boolean;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    if (params?.search) query.set("search", params.search);
    if (params?.asset_type) query.set("asset_type", params.asset_type);
    if (params?.criticality) query.set("criticality", params.criticality);
    if (params?.environment) query.set("environment", params.environment);
    if (params?.is_active !== undefined) query.set("is_active", params.is_active.toString());
    return request(`/api/v1/vulnerabilities/assets?${query}`, { token });
  },

  getAsset: (token: string, id: string) =>
    request(`/api/v1/vulnerabilities/assets/${id}`, { token }),

  createAsset: (token: string, data: {
    name: string;
    asset_type: string;
    hostname?: string;
    ip_address?: string;
    criticality?: string;
    environment?: string;
    owner?: string;
    operating_system?: string;
    tags?: string[];
  }) =>
    request("/api/v1/vulnerabilities/assets", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateAsset: (token: string, id: string, data: any) =>
    request(`/api/v1/vulnerabilities/assets/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      token,
    }),

  deleteAsset: (token: string, id: string) =>
    request(`/api/v1/vulnerabilities/assets/${id}`, {
      method: "DELETE",
      token,
    }),

  // Vulnerabilities
  listVulnerabilities: (token: string, params?: {
    page?: number;
    page_size?: number;
    search?: string;
    severity?: string;
    status?: string;
    asset_id?: string;
    scan_id?: string;
    assigned_to?: string;
    overdue_only?: boolean;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    if (params?.search) query.set("search", params.search);
    if (params?.severity) query.set("severity", params.severity);
    if (params?.status) query.set("status", params.status);
    if (params?.asset_id) query.set("asset_id", params.asset_id);
    if (params?.scan_id) query.set("scan_id", params.scan_id);
    if (params?.assigned_to) query.set("assigned_to", params.assigned_to);
    if (params?.overdue_only) query.set("overdue_only", params.overdue_only.toString());
    return request(`/api/v1/vulnerabilities?${query}`, { token });
  },

  getVulnerability: (token: string, id: string) =>
    request(`/api/v1/vulnerabilities/${id}`, { token }),

  createVulnerability: (token: string, data: {
    title: string;
    description?: string;
    severity: string;
    cvss_score?: number;
    vulnerability_type?: string;
    affected_component?: string;
    remediation_steps?: string;
    asset_ids?: string[];
    cve_ids?: string[];
    tags?: string[];
  }) =>
    request("/api/v1/vulnerabilities", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateVulnerability: (token: string, id: string, data: any) =>
    request(`/api/v1/vulnerabilities/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      token,
    }),

  updateVulnerabilityStatus: (token: string, id: string, data: {
    status: string;
    comment?: string;
    risk_acceptance_reason?: string;
    risk_acceptance_expiry?: string;
  }) =>
    request(`/api/v1/vulnerabilities/${id}/status`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  addComment: (token: string, vulnId: string, data: { content: string; comment_type?: string }) =>
    request(`/api/v1/vulnerabilities/${vulnId}/comments`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  deleteVulnerability: (token: string, id: string) =>
    request(`/api/v1/vulnerabilities/${id}`, {
      method: "DELETE",
      token,
    }),

  // Scans
  listScans: (token: string, params?: {
    page?: number;
    page_size?: number;
    scan_type?: string;
    status?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    if (params?.scan_type) query.set("scan_type", params.scan_type);
    if (params?.status) query.set("status", params.status);
    return request(`/api/v1/vulnerabilities/scans?${query}`, { token });
  },

  getScan: (token: string, id: string) =>
    request(`/api/v1/vulnerabilities/scans/${id}`, { token }),

  createScan: (token: string, data: {
    name: string;
    scan_type: string;
    scanner: string;
    target_scope?: string;
    target_asset_id?: string;
    scan_config?: Record<string, any>;
  }) =>
    request("/api/v1/vulnerabilities/scans", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  startScan: (token: string, id: string) =>
    request(`/api/v1/vulnerabilities/scans/${id}/start`, {
      method: "POST",
      token,
    }),

  cancelScan: (token: string, id: string) =>
    request(`/api/v1/vulnerabilities/scans/${id}/cancel`, {
      method: "POST",
      token,
    }),

  // Import
  importVulnerabilities: (token: string, data: {
    scanner: string;
    scan_date?: string;
    findings: Array<{
      title: string;
      description?: string;
      severity: string;
      cvss_score?: number;
      affected_component?: string;
      remediation?: string;
    }>;
  }) =>
    request("/api/v1/vulnerabilities/import", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  // Stats
  getStats: (token: string) =>
    request("/api/v1/vulnerabilities/stats", { token }),
};

// Risk Management
export const risksAPI = {
  // Risks
  listRisks: (token: string, params?: {
    page?: number;
    page_size?: number;
    search?: string;
    category?: string;
    status?: string;
    risk_level?: string;
    risk_owner?: string;
    department?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    if (params?.search) query.set("search", params.search);
    if (params?.category) query.set("category", params.category);
    if (params?.status) query.set("status", params.status);
    if (params?.risk_level) query.set("risk_level", params.risk_level);
    if (params?.risk_owner) query.set("risk_owner", params.risk_owner);
    if (params?.department) query.set("department", params.department);
    return request(`/api/v1/risks?${query}`, { token });
  },

  getRisk: (token: string, id: string) =>
    request(`/api/v1/risks/${id}`, { token }),

  createRisk: (token: string, data: {
    title: string;
    description?: string;
    category: string;
    risk_source?: string;
    threat_scenario?: string;
    department?: string;
    inherent_likelihood?: string;
    inherent_impact?: string;
    financial_impact?: number;
    operational_impact?: string;
    treatment_type?: string;
    treatment_plan?: string;
    treatment_deadline?: string;
    risk_owner?: string;
    affected_assets?: string[];
    affected_processes?: string[];
    compliance_frameworks?: string[];
    tags?: string[];
    incident_id?: string;
  }) =>
    request("/api/v1/risks", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateRisk: (token: string, id: string, data: any) =>
    request(`/api/v1/risks/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deleteRisk: (token: string, id: string) =>
    request(`/api/v1/risks/${id}`, {
      method: "DELETE",
      token,
    }),

  // Assessments
  assessRisk: (token: string, riskId: string, data: {
    likelihood: string;
    impact: string;
    assessment_type?: string;
    assessment_notes?: string;
    assumptions?: string;
  }) =>
    request(`/api/v1/risks/${riskId}/assess`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getAssessments: (token: string, riskId: string) =>
    request(`/api/v1/risks/${riskId}/assessments`, { token }),

  // Acceptance
  acceptRisk: (token: string, riskId: string, data: {
    acceptance_reason: string;
    acceptance_expiry?: string;
  }) =>
    request(`/api/v1/risks/${riskId}/accept`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  // Close
  closeRisk: (token: string, riskId: string, closureReason?: string) =>
    request(`/api/v1/risks/${riskId}/close?closure_reason=${closureReason || ""}`, {
      method: "POST",
      token,
    }),

  // Controls
  listControls: (token: string, params?: {
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    return request(`/api/v1/risks/controls?${query}`, { token });
  },

  getControl: (token: string, id: string) =>
    request(`/api/v1/risks/controls/${id}`, { token }),

  createControl: (token: string, data: {
    name: string;
    description?: string;
    control_type: string;
    implementation_details?: string;
    effectiveness_rating?: number;
    implementation_cost?: number;
    annual_cost?: number;
    control_owner?: string;
    compliance_frameworks?: string[];
    compliance_control_ids?: string[];
  }) =>
    request("/api/v1/risks/controls", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateControl: (token: string, id: string, data: any) =>
    request(`/api/v1/risks/controls/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deleteControl: (token: string, id: string) =>
    request(`/api/v1/risks/controls/${id}`, {
      method: "DELETE",
      token,
    }),

  linkControlToRisk: (token: string, riskId: string, controlId: string) =>
    request(`/api/v1/risks/${riskId}/controls/${controlId}`, {
      method: "POST",
      token,
    }),

  unlinkControlFromRisk: (token: string, riskId: string, controlId: string) =>
    request(`/api/v1/risks/${riskId}/controls/${controlId}`, {
      method: "DELETE",
      token,
    }),

  // Treatment Actions
  createTreatmentAction: (token: string, riskId: string, data: {
    title: string;
    description?: string;
    priority?: string;
    assigned_to?: string;
    due_date?: string;
    estimated_cost?: number;
    expected_risk_reduction?: string;
  }) =>
    request(`/api/v1/risks/${riskId}/treatments`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getTreatmentActions: (token: string, riskId: string) =>
    request(`/api/v1/risks/${riskId}/treatments`, { token }),

  updateTreatmentAction: (token: string, actionId: string, data: any) =>
    request(`/api/v1/risks/treatments/${actionId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deleteTreatmentAction: (token: string, actionId: string) =>
    request(`/api/v1/risks/treatments/${actionId}`, {
      method: "DELETE",
      token,
    }),

  // Risk Appetite
  getRiskAppetite: (token: string) =>
    request("/api/v1/risks/appetite", { token }),

  setRiskAppetite: (token: string, data: {
    category: string;
    appetite_level: string;
    tolerance_threshold?: number;
    description?: string;
    max_single_loss?: number;
    max_annual_loss?: number;
    requires_board_approval?: boolean;
    requires_executive_approval?: boolean;
  }) =>
    request("/api/v1/risks/appetite", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  // Matrix
  getRiskMatrix: (token: string) =>
    request("/api/v1/risks/matrix", { token }),

  // Stats
  getStats: (token: string) =>
    request("/api/v1/risks/statistics", { token }),
};

// CMDB (Asset & Configuration Management)
export const cmdbAPI = {
  // Configuration Items
  listCIs: (token: string, params?: {
    page?: number;
    page_size?: number;
    ci_type?: string;
    status?: string;
    department?: string;
    business_service?: string;
    search?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    if (params?.ci_type) query.set("ci_type", params.ci_type);
    if (params?.status) query.set("status", params.status);
    if (params?.department) query.set("department", params.department);
    if (params?.business_service) query.set("business_service", params.business_service);
    if (params?.search) query.set("search", params.search);
    return request(`/api/v1/cmdb/configuration-items?${query}`, { token });
  },

  getCI: (token: string, id: string) =>
    request(`/api/v1/cmdb/configuration-items/${id}`, { token }),

  createCI: (token: string, data: {
    name: string;
    ci_type: string;
    environment?: string;
    department?: string;
    business_service?: string;
    owner?: string;
    description?: string;
    attributes?: Record<string, unknown>;
    tags?: string[];
  }) =>
    request("/api/v1/cmdb/configuration-items", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateCI: (token: string, id: string, data: any) =>
    request(`/api/v1/cmdb/configuration-items/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deleteCI: (token: string, id: string) =>
    request(`/api/v1/cmdb/configuration-items/${id}`, {
      method: "DELETE",
      token,
    }),

  // Software Items
  listSoftware: (token: string, params?: {
    page?: number;
    page_size?: number;
    category?: string;
    is_approved?: boolean;
    is_prohibited?: boolean;
    search?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    if (params?.category) query.set("category", params.category);
    if (params?.is_approved !== undefined) query.set("is_approved", params.is_approved.toString());
    if (params?.is_prohibited !== undefined) query.set("is_prohibited", params.is_prohibited.toString());
    if (params?.search) query.set("search", params.search);
    return request(`/api/v1/cmdb/software?${query}`, { token });
  },

  getSoftware: (token: string, id: string) =>
    request(`/api/v1/cmdb/software/${id}`, { token }),

  createSoftware: (token: string, data: {
    name: string;
    vendor: string;
    category: string;
    latest_version?: string;
    is_approved?: boolean;
    is_prohibited?: boolean;
    description?: string;
    security_rating?: number;
    end_of_life_date?: string;
    tags?: string[];
  }) =>
    request("/api/v1/cmdb/software", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateSoftware: (token: string, id: string, data: any) =>
    request(`/api/v1/cmdb/software/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  // Software Installations
  createInstallation: (token: string, data: {
    software_id: string;
    asset_id?: string;
    ci_id?: string;
    installed_version?: string;
    installation_path?: string;
    installation_date?: string;
    license_id?: string;
    discovery_source?: string;
  }) =>
    request("/api/v1/cmdb/installations", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getAssetSoftware: (token: string, assetId: string) =>
    request(`/api/v1/cmdb/assets/${assetId}/software`, { token }),

  // Licenses
  listLicenses: (token: string, params?: {
    page?: number;
    page_size?: number;
    expiring_soon?: boolean;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    if (params?.expiring_soon) query.set("expiring_soon", params.expiring_soon.toString());
    return request(`/api/v1/cmdb/licenses?${query}`, { token });
  },

  createLicense: (token: string, data: {
    software_id: string;
    license_type: string;
    license_key?: string;
    total_licenses: number;
    purchase_date?: string;
    expiration_date?: string;
    cost?: number;
    vendor_contact?: string;
    notes?: string;
  }) =>
    request("/api/v1/cmdb/licenses", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  // Hardware Specs
  getHardwareSpec: (token: string, assetId: string) =>
    request(`/api/v1/cmdb/assets/${assetId}/hardware`, { token }),

  createHardwareSpec: (token: string, data: {
    asset_id: string;
    manufacturer?: string;
    model?: string;
    serial_number?: string;
    cpu?: string;
    cpu_cores?: number;
    ram_gb?: number;
    storage_type?: string;
    storage_gb?: number;
    warranty_start?: string;
    warranty_end?: string;
    purchase_date?: string;
    purchase_cost?: number;
  }) =>
    request("/api/v1/cmdb/hardware", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateHardwareSpec: (token: string, assetId: string, data: any) =>
    request(`/api/v1/cmdb/assets/${assetId}/hardware`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  // Lifecycle
  getAssetLifecycle: (token: string, assetId: string) =>
    request(`/api/v1/cmdb/assets/${assetId}/lifecycle`, { token }),

  createAssetLifecycle: (token: string, data: {
    asset_id: string;
    current_stage: string;
    procurement_date?: string;
    deployment_date?: string;
    expected_retirement?: string;
    notes?: string;
  }) =>
    request("/api/v1/cmdb/lifecycle", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateAssetLifecycle: (token: string, assetId: string, data: any) =>
    request(`/api/v1/cmdb/assets/${assetId}/lifecycle`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  // Relationships
  getAssetRelationships: (token: string, assetId: string, direction?: string) => {
    const query = direction ? `?direction=${direction}` : "";
    return request(`/api/v1/cmdb/assets/${assetId}/relationships${query}`, { token });
  },

  createRelationship: (token: string, data: {
    source_asset_id: string;
    target_asset_id: string;
    relationship_type: string;
    description?: string;
    is_critical?: boolean;
    valid_from?: string;
    valid_to?: string;
  }) =>
    request("/api/v1/cmdb/relationships", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  deleteRelationship: (token: string, id: string) =>
    request(`/api/v1/cmdb/relationships/${id}`, {
      method: "DELETE",
      token,
    }),

  // Changes
  listChanges: (token: string, params?: {
    asset_id?: string;
    ci_id?: string;
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.asset_id) query.set("asset_id", params.asset_id);
    if (params?.ci_id) query.set("ci_id", params.ci_id);
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    return request(`/api/v1/cmdb/changes?${query}`, { token });
  },

  getAssetChanges: (token: string, assetId: string, params?: { page?: number; page_size?: number }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    return request(`/api/v1/cmdb/assets/${assetId}/changes?${query}`, { token });
  },

  recordChange: (token: string, data: {
    asset_id?: string;
    ci_id?: string;
    change_type: string;
    field_changed?: string;
    old_value?: string;
    new_value?: string;
    change_reason?: string;
    change_ticket?: string;
    changed_by?: string;
  }) =>
    request("/api/v1/cmdb/changes", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  // Dependency Map
  getDependencyMap: (token: string, assetId: string, depth?: number) => {
    const query = depth ? `?depth=${depth}` : "";
    return request(`/api/v1/cmdb/assets/${assetId}/dependencies${query}`, { token });
  },

  // Statistics
  getStats: (token: string) =>
    request("/api/v1/cmdb/statistics", { token }),
};

// SOC (Security Operations Center)
export const socAPI = {
  // Alerts
  listAlerts: (token: string, params?: {
    page?: number;
    page_size?: number;
    severity?: string;
    status?: string;
    source?: string;
    assigned_to?: string;
    unassigned?: boolean;
    search?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    if (params?.severity) query.set("severity", params.severity);
    if (params?.status) query.set("status", params.status);
    if (params?.source) query.set("source", params.source);
    if (params?.assigned_to) query.set("assigned_to", params.assigned_to);
    if (params?.unassigned) query.set("unassigned", params.unassigned.toString());
    if (params?.search) query.set("search", params.search);
    return request(`/api/v1/soc/alerts?${query}`, { token });
  },

  getAlert: (token: string, id: string) =>
    request(`/api/v1/soc/alerts/${id}`, { token }),

  createAlert: (token: string, data: {
    title: string;
    description?: string;
    severity?: string;
    source?: string;
    source_ref?: string;
    detection_rule?: string;
    mitre_tactics?: string[];
    mitre_techniques?: string[];
    affected_assets?: string[];
    source_ip?: string;
    destination_ip?: string;
    risk_score?: number;
    tags?: string[];
  }) =>
    request("/api/v1/soc/alerts", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateAlert: (token: string, id: string, data: any) =>
    request(`/api/v1/soc/alerts/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  assignAlert: (token: string, id: string, data: { assigned_to: string; notes?: string }) =>
    request(`/api/v1/soc/alerts/${id}/assign`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  acknowledgeAlert: (token: string, id: string, analyst: string) =>
    request(`/api/v1/soc/alerts/${id}/acknowledge?analyst=${encodeURIComponent(analyst)}`, {
      method: "POST",
      token,
    }),

  resolveAlert: (token: string, id: string, data: {
    resolution_notes: string;
    is_false_positive?: boolean;
    false_positive_reason?: string;
  }) =>
    request(`/api/v1/soc/alerts/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  addAlertComment: (token: string, alertId: string, data: { content: string; is_internal?: boolean }, author: string) =>
    request(`/api/v1/soc/alerts/${alertId}/comments?author=${encodeURIComponent(author)}`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  // Cases
  listCases: (token: string, params?: {
    page?: number;
    page_size?: number;
    status?: string;
    priority?: string;
    assigned_to?: string;
    assigned_team?: string;
    overdue?: boolean;
    search?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    if (params?.status) query.set("status", params.status);
    if (params?.priority) query.set("priority", params.priority);
    if (params?.assigned_to) query.set("assigned_to", params.assigned_to);
    if (params?.assigned_team) query.set("assigned_team", params.assigned_team);
    if (params?.overdue) query.set("overdue", params.overdue.toString());
    if (params?.search) query.set("search", params.search);
    return request(`/api/v1/soc/cases?${query}`, { token });
  },

  getCase: (token: string, id: string) =>
    request(`/api/v1/soc/cases/${id}`, { token }),

  createCase: (token: string, data: {
    title: string;
    description?: string;
    priority?: string;
    case_type?: string;
    assigned_to?: string;
    assigned_team?: string;
    due_date?: string;
    alert_ids?: string[];
    tags?: string[];
  }, created_by?: string) => {
    const query = created_by ? `?created_by=${encodeURIComponent(created_by)}` : "";
    return request(`/api/v1/soc/cases${query}`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    });
  },

  updateCase: (token: string, id: string, data: any) =>
    request(`/api/v1/soc/cases/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  escalateCase: (token: string, id: string, data: { escalated_to: string; reason: string }, escalated_by?: string) => {
    const query = escalated_by ? `?escalated_by=${encodeURIComponent(escalated_by)}` : "";
    return request(`/api/v1/soc/cases/${id}/escalate${query}`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    });
  },

  resolveCase: (token: string, id: string, data: {
    resolution_summary: string;
    root_cause?: string;
    lessons_learned?: string;
  }, resolved_by?: string) => {
    const query = resolved_by ? `?resolved_by=${encodeURIComponent(resolved_by)}` : "";
    return request(`/api/v1/soc/cases/${id}/resolve${query}`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    });
  },

  linkAlertToCase: (token: string, caseId: string, alertId: string) =>
    request(`/api/v1/soc/cases/${caseId}/alerts/${alertId}`, {
      method: "POST",
      token,
    }),

  // Case Tasks
  createCaseTask: (token: string, caseId: string, data: {
    title: string;
    description?: string;
    priority?: string;
    assigned_to?: string;
    due_date?: string;
  }, created_by?: string) => {
    const query = created_by ? `?created_by=${encodeURIComponent(created_by)}` : "";
    return request(`/api/v1/soc/cases/${caseId}/tasks${query}`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    });
  },

  updateCaseTask: (token: string, taskId: string, data: any) =>
    request(`/api/v1/soc/cases/tasks/${taskId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  // Case Timeline
  addCaseTimeline: (token: string, caseId: string, data: {
    event_time: string;
    event_type: string;
    description: string;
    evidence_ids?: string[];
  }, author?: string) => {
    const query = author ? `?author=${encodeURIComponent(author)}` : "";
    return request(`/api/v1/soc/cases/${caseId}/timeline${query}`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    });
  },

  // Playbooks
  listPlaybooks: (token: string, params?: {
    page?: number;
    page_size?: number;
    status?: string;
    trigger_type?: string;
    is_enabled?: boolean;
    category?: string;
    search?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    if (params?.status) query.set("status", params.status);
    if (params?.trigger_type) query.set("trigger_type", params.trigger_type);
    if (params?.is_enabled !== undefined) query.set("is_enabled", params.is_enabled.toString());
    if (params?.category) query.set("category", params.category);
    if (params?.search) query.set("search", params.search);
    return request(`/api/v1/soc/playbooks?${query}`, { token });
  },

  getPlaybook: (token: string, id: string) =>
    request(`/api/v1/soc/playbooks/${id}`, { token }),

  createPlaybook: (token: string, data: {
    name: string;
    description?: string;
    trigger_type?: string;
    trigger_conditions?: Record<string, any>;
    actions: Array<{
      action_type: string;
      name: string;
      description?: string;
      parameters?: Record<string, any>;
      timeout_seconds?: number;
      require_approval?: boolean;
    }>;
    is_enabled?: boolean;
    run_automatically?: boolean;
    require_approval?: boolean;
    category?: string;
    tags?: string[];
  }, created_by?: string) => {
    const query = created_by ? `?created_by=${encodeURIComponent(created_by)}` : "";
    return request(`/api/v1/soc/playbooks${query}`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    });
  },

  updatePlaybook: (token: string, id: string, data: any) =>
    request(`/api/v1/soc/playbooks/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  executePlaybook: (token: string, id: string, data: {
    alert_id?: string;
    case_id?: string;
    trigger_reason?: string;
  }, executed_by?: string) => {
    const query = executed_by ? `?executed_by=${encodeURIComponent(executed_by)}` : "";
    return request(`/api/v1/soc/playbooks/${id}/execute${query}`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    });
  },

  approveExecution: (token: string, executionId: string, approved_by: string) =>
    request(`/api/v1/soc/playbooks/executions/${executionId}/approve?approved_by=${encodeURIComponent(approved_by)}`, {
      method: "POST",
      token,
    }),

  // Dashboard
  getDashboard: (token: string) =>
    request("/api/v1/soc/dashboard", { token }),

  // Shift Handover
  createHandover: (token: string, data: {
    shift_type?: string;
    summary: string;
    open_alerts?: string[];
    open_cases?: string[];
    pending_actions?: string[];
    important_notes?: string;
    escalations?: string;
  }, analyst: string) =>
    request(`/api/v1/soc/handover?analyst=${encodeURIComponent(analyst)}`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  acknowledgeHandover: (token: string, id: string, analyst: string) =>
    request(`/api/v1/soc/handover/${id}/acknowledge?analyst=${encodeURIComponent(analyst)}`, {
      method: "POST",
      token,
    }),

  getLatestHandover: (token: string) =>
    request("/api/v1/soc/handover/latest", { token }),
};

// Third-Party Risk Management
export const tprmAPI = {
  // Dashboard
  getDashboard: (token: string) =>
    request("/api/v1/tprm/dashboard", { token }),

  // Vendors
  listVendors: (token: string, params?: {
    page?: number;
    size?: number;
    status?: string;
    tier?: string;
    risk_rating?: string;
    search?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.status) query.set("status", params.status);
    if (params?.tier) query.set("tier", params.tier);
    if (params?.risk_rating) query.set("risk_rating", params.risk_rating);
    if (params?.search) query.set("search", params.search);
    return request(`/api/v1/tprm/vendors?${query}`, { token });
  },

  getVendor: (token: string, id: string) =>
    request(`/api/v1/tprm/vendors/${id}`, { token }),

  createVendor: (token: string, data: {
    name: string;
    legal_name?: string;
    description?: string;
    tier?: string;
    category?: string;
    website?: string;
    primary_contact_name?: string;
    primary_contact_email?: string;
    primary_contact_phone?: string;
    address?: string;
    country?: string;
    services_provided?: string;
    data_types_shared?: string[];
    has_pii_access?: boolean;
    has_phi_access?: boolean;
    has_pci_access?: boolean;
    has_network_access?: boolean;
    has_physical_access?: boolean;
    certifications?: string[];
    compliance_frameworks?: string[];
    business_owner?: string;
    risk_owner?: string;
    notes?: string;
    tags?: string[];
  }) =>
    request("/api/v1/tprm/vendors", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateVendor: (token: string, id: string, data: any) =>
    request(`/api/v1/tprm/vendors/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deleteVendor: (token: string, id: string) =>
    request(`/api/v1/tprm/vendors/${id}`, {
      method: "DELETE",
      token,
    }),

  onboardVendor: (token: string, id: string) =>
    request(`/api/v1/tprm/vendors/${id}/onboard`, {
      method: "POST",
      token,
    }),

  offboardVendor: (token: string, id: string) =>
    request(`/api/v1/tprm/vendors/${id}/offboard`, {
      method: "POST",
      token,
    }),

  // Assessments
  listAssessments: (token: string, params?: {
    page?: number;
    size?: number;
    vendor_id?: string;
    status?: string;
    assessment_type?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.vendor_id) query.set("vendor_id", params.vendor_id);
    if (params?.status) query.set("status", params.status);
    if (params?.assessment_type) query.set("assessment_type", params.assessment_type);
    return request(`/api/v1/tprm/assessments?${query}`, { token });
  },

  getAssessment: (token: string, id: string) =>
    request(`/api/v1/tprm/assessments/${id}`, { token }),

  createAssessment: (token: string, data: {
    vendor_id: string;
    title: string;
    description?: string;
    assessment_type?: string;
    questionnaire_template?: string;
    questionnaire_due_date?: string;
    assessor?: string;
    reviewer?: string;
  }) =>
    request("/api/v1/tprm/assessments", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateAssessment: (token: string, id: string, data: any) =>
    request(`/api/v1/tprm/assessments/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  sendQuestionnaire: (token: string, id: string) =>
    request(`/api/v1/tprm/assessments/${id}/send-questionnaire`, {
      method: "POST",
      token,
    }),

  completeAssessment: (token: string, id: string, residual_risk: string, review_notes?: string) =>
    request(`/api/v1/tprm/assessments/${id}/complete?residual_risk=${residual_risk}${review_notes ? `&review_notes=${encodeURIComponent(review_notes)}` : ""}`, {
      method: "POST",
      token,
    }),

  acceptAssessmentRisk: (token: string, id: string, expiry_days?: number) =>
    request(`/api/v1/tprm/assessments/${id}/accept-risk?expiry_days=${expiry_days || 365}`, {
      method: "POST",
      token,
    }),

  // Findings
  listFindings: (token: string, params?: {
    page?: number;
    size?: number;
    vendor_id?: string;
    assessment_id?: string;
    severity?: string;
    status?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.vendor_id) query.set("vendor_id", params.vendor_id);
    if (params?.assessment_id) query.set("assessment_id", params.assessment_id);
    if (params?.severity) query.set("severity", params.severity);
    if (params?.status) query.set("status", params.status);
    return request(`/api/v1/tprm/findings?${query}`, { token });
  },

  getFinding: (token: string, id: string) =>
    request(`/api/v1/tprm/findings/${id}`, { token }),

  createFinding: (token: string, data: {
    assessment_id: string;
    vendor_id: string;
    title: string;
    description?: string;
    severity?: string;
    control_domain?: string;
    control_reference?: string;
    risk_description?: string;
    business_impact?: string;
    likelihood?: number;
    impact?: number;
    recommendation?: string;
  }) =>
    request("/api/v1/tprm/findings", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateFinding: (token: string, id: string, data: any) =>
    request(`/api/v1/tprm/findings/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  remediateFinding: (token: string, id: string, remediation_notes?: string) =>
    request(`/api/v1/tprm/findings/${id}/remediate${remediation_notes ? `?remediation_notes=${encodeURIComponent(remediation_notes)}` : ""}`, {
      method: "POST",
      token,
    }),

  acceptFindingRisk: (token: string, id: string, justification: string, expiry_days?: number) =>
    request(`/api/v1/tprm/findings/${id}/accept?justification=${encodeURIComponent(justification)}&expiry_days=${expiry_days || 365}`, {
      method: "POST",
      token,
    }),

  // Contracts
  listContracts: (token: string, params?: {
    page?: number;
    size?: number;
    vendor_id?: string;
    status?: string;
    expiring_within_days?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.vendor_id) query.set("vendor_id", params.vendor_id);
    if (params?.status) query.set("status", params.status);
    if (params?.expiring_within_days) query.set("expiring_within_days", params.expiring_within_days.toString());
    return request(`/api/v1/tprm/contracts?${query}`, { token });
  },

  getContract: (token: string, id: string) =>
    request(`/api/v1/tprm/contracts/${id}`, { token }),

  createContract: (token: string, data: {
    vendor_id: string;
    title: string;
    description?: string;
    contract_type?: string;
    effective_date?: string;
    expiration_date?: string;
    renewal_date?: string;
    auto_renewal?: boolean;
    notice_period_days?: number;
    contract_value?: number;
    annual_value?: number;
    currency?: string;
    has_security_addendum?: boolean;
    has_dpa?: boolean;
    has_sla?: boolean;
    has_nda?: boolean;
    has_right_to_audit?: boolean;
    has_breach_notification?: boolean;
    breach_notification_hours?: number;
    has_data_deletion_clause?: boolean;
    has_subprocessor_restrictions?: boolean;
    cyber_insurance_required?: boolean;
    cyber_insurance_minimum?: number;
    contract_owner?: string;
    legal_reviewer?: string;
    security_reviewer?: string;
    document_url?: string;
    related_documents?: string[];
    notes?: string;
  }) =>
    request("/api/v1/tprm/contracts", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateContract: (token: string, id: string, data: any) =>
    request(`/api/v1/tprm/contracts/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  activateContract: (token: string, id: string) =>
    request(`/api/v1/tprm/contracts/${id}/activate`, {
      method: "POST",
      token,
    }),

  terminateContract: (token: string, id: string) =>
    request(`/api/v1/tprm/contracts/${id}/terminate`, {
      method: "POST",
      token,
    }),

  // Questionnaire Templates
  listQuestionnaireTemplates: (token: string, active_only: boolean = true) =>
    request(`/api/v1/tprm/questionnaire-templates?active_only=${active_only}`, { token }),

  getQuestionnaireTemplate: (token: string, id: string) =>
    request(`/api/v1/tprm/questionnaire-templates/${id}`, { token }),

  createQuestionnaireTemplate: (token: string, data: {
    name: string;
    description?: string;
    version?: string;
    sections: Array<{
      name: string;
      description?: string;
      questions: Array<{
        id: string;
        question: string;
        type: string;
        required?: boolean;
        weight?: number;
        options?: string[];
        control_reference?: string;
      }>;
    }>;
    applicable_tiers?: string[];
    applicable_categories?: string[];
    passing_score?: number;
  }) =>
    request("/api/v1/tprm/questionnaire-templates", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateQuestionnaireTemplate: (token: string, id: string, data: any) =>
    request(`/api/v1/tprm/questionnaire-templates/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),
};

// Integration Hub
export const integrationsAPI = {
  // Dashboard
  getDashboard: (token: string) =>
    request("/api/v1/integrations/dashboard", { token }),

  // Templates
  listTemplates: (token: string, category?: string) => {
    const query = category ? `?category=${category}` : "";
    return request(`/api/v1/integrations/templates${query}`, { token });
  },

  getTemplate: (token: string, integrationType: string) =>
    request(`/api/v1/integrations/templates/${integrationType}`, { token }),

  seedTemplates: (token: string) =>
    request("/api/v1/integrations/templates/seed", {
      method: "POST",
      token,
    }),

  // Integrations CRUD
  listIntegrations: (token: string, params?: {
    page?: number;
    size?: number;
    category?: string;
    status?: string;
    is_enabled?: boolean;
    search?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.category) query.set("category", params.category);
    if (params?.status) query.set("status", params.status);
    if (params?.is_enabled !== undefined) query.set("is_enabled", params.is_enabled.toString());
    if (params?.search) query.set("search", params.search);
    return request(`/api/v1/integrations?${query}`, { token });
  },

  getIntegration: (token: string, id: string) =>
    request(`/api/v1/integrations/${id}`, { token }),

  createIntegration: (token: string, data: {
    name: string;
    description?: string;
    integration_type: string;
    category: string;
    base_url?: string;
    api_key?: string;
    api_secret?: string;
    username?: string;
    password?: string;
    config?: Record<string, any>;
    sync_direction?: string;
    sync_frequency?: string;
    data_mappings?: Record<string, any>;
    sync_filters?: Record<string, any>;
  }) =>
    request("/api/v1/integrations", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateIntegration: (token: string, id: string, data: any) =>
    request(`/api/v1/integrations/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deleteIntegration: (token: string, id: string) =>
    request(`/api/v1/integrations/${id}`, {
      method: "DELETE",
      token,
    }),

  enableIntegration: (token: string, id: string) =>
    request(`/api/v1/integrations/${id}/enable`, {
      method: "POST",
      token,
    }),

  disableIntegration: (token: string, id: string) =>
    request(`/api/v1/integrations/${id}/disable`, {
      method: "POST",
      token,
    }),

  // Test Connection
  testConnection: (token: string, data: {
    integration_type: string;
    base_url?: string;
    api_key?: string;
    api_secret?: string;
    username?: string;
    password?: string;
    config?: Record<string, any>;
  }) =>
    request("/api/v1/integrations/test-connection", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  // Sync Operations
  triggerSync: (token: string, id: string, syncType?: string) =>
    request(`/api/v1/integrations/${id}/sync`, {
      method: "POST",
      body: JSON.stringify({ sync_type: syncType || "incremental" }),
      token,
    }),

  getSyncLogs: (token: string, id: string, params?: { page?: number; size?: number }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    return request(`/api/v1/integrations/${id}/sync-logs?${query}`, { token });
  },

  // Webhook Events
  getWebhookEvents: (token: string, id: string, params?: {
    page?: number;
    size?: number;
    processed?: boolean;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.processed !== undefined) query.set("processed", params.processed.toString());
    return request(`/api/v1/integrations/${id}/webhooks?${query}`, { token });
  },

  // Security Awareness Metrics
  getAwarenessMetrics: (token: string, id: string) =>
    request(`/api/v1/integrations/${id}/awareness-metrics`, { token }),

  getAggregatedAwarenessMetrics: (token: string) =>
    request("/api/v1/integrations/awareness/aggregated", { token }),
};

// Reporting & Analytics
export const reportingAPI = {
  // Executive Dashboard
  getExecutiveDashboard: (token: string) =>
    request("/api/v1/reporting/executive-dashboard", { token }),

  // Templates
  listTemplates: (token: string, reportType?: string) => {
    const query = reportType ? `?report_type=${reportType}` : "";
    return request(`/api/v1/reporting/templates${query}`, { token });
  },

  createTemplate: (token: string, data: any) =>
    request("/api/v1/reporting/templates", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  seedTemplates: (token: string) =>
    request("/api/v1/reporting/templates/seed", {
      method: "POST",
      token,
    }),

  getTemplate: (token: string, templateId: string) =>
    request(`/api/v1/reporting/templates/${templateId}`, { token }),

  // Report Generation
  generateReport: (token: string, data: {
    template_id?: string;
    report_type?: string;
    name?: string;
    format?: string;
    period_start?: string;
    period_end?: string;
    period_days?: number;
    filters?: Record<string, any>;
  }) =>
    request("/api/v1/reporting/reports/generate", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  listReports: (token: string, params?: {
    page?: number;
    size?: number;
    report_type?: string;
    status?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.report_type) query.set("report_type", params.report_type);
    if (params?.status) query.set("status", params.status);
    return request(`/api/v1/reporting/reports?${query}`, { token });
  },

  getReport: (token: string, reportId: string) =>
    request(`/api/v1/reporting/reports/${reportId}`, { token }),

  getReportData: (token: string, reportId: string) =>
    request(`/api/v1/reporting/reports/${reportId}/data`, { token }),

  downloadReport: (token: string, reportId: string) =>
    request(`/api/v1/reporting/reports/${reportId}/download`, { token }),

  // Schedules
  createSchedule: (token: string, data: any) =>
    request("/api/v1/reporting/schedules", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  listSchedules: (token: string, params?: { page?: number; size?: number }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    return request(`/api/v1/reporting/schedules?${query}`, { token });
  },

  // Dashboards
  createDashboard: (token: string, data: any) =>
    request("/api/v1/reporting/dashboards", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  listDashboards: (token: string, params?: { page?: number; size?: number }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    return request(`/api/v1/reporting/dashboards?${query}`, { token });
  },

  getDashboard: (token: string, dashboardId: string) =>
    request(`/api/v1/reporting/dashboards/${dashboardId}`, { token }),

  addWidget: (token: string, dashboardId: string, data: any) =>
    request(`/api/v1/reporting/dashboards/${dashboardId}/widgets`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  // Metrics
  getMetricTrend: (token: string, metricName: string, params?: {
    period_days?: number;
    aggregation?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.period_days) query.set("period_days", params.period_days.toString());
    if (params?.aggregation) query.set("aggregation", params.aggregation);
    return request(`/api/v1/reporting/metrics/${metricName}/trend?${query}`, { token });
  },
};

// Notifications
export const notificationsAPI = {
  // Notifications
  listNotifications: (token: string, params?: {
    page?: number;
    size?: number;
    unread_only?: boolean;
    include_archived?: boolean;
    notification_type?: string;
    priority?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.unread_only) query.set("unread_only", "true");
    if (params?.include_archived) query.set("include_archived", "true");
    if (params?.notification_type) query.set("notification_type", params.notification_type);
    if (params?.priority) query.set("priority", params.priority);
    return request(`/api/v1/notifications?${query}`, { token });
  },

  getNotification: (token: string, id: string) =>
    request(`/api/v1/notifications/${id}`, { token }),

  getStats: (token: string) =>
    request("/api/v1/notifications/stats", { token }),

  markAsRead: (token: string, data: { notification_ids?: string[]; mark_all?: boolean }) =>
    request("/api/v1/notifications/mark-read", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  archiveNotification: (token: string, id: string) =>
    request(`/api/v1/notifications/${id}/archive`, {
      method: "POST",
      token,
    }),

  deleteNotification: (token: string, id: string) =>
    request(`/api/v1/notifications/${id}`, {
      method: "DELETE",
      token,
    }),

  // Preferences
  getPreferences: (token: string) =>
    request("/api/v1/notifications/preferences/me", { token }),

  updatePreferences: (token: string, data: any) =>
    request("/api/v1/notifications/preferences/me", {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  // Webhooks
  listWebhooks: (token: string, params?: { page?: number; size?: number; active_only?: boolean }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.active_only) query.set("active_only", "true");
    return request(`/api/v1/notifications/webhooks?${query}`, { token });
  },

  getWebhook: (token: string, id: string) =>
    request(`/api/v1/notifications/webhooks/${id}`, { token }),

  createWebhook: (token: string, data: any) =>
    request("/api/v1/notifications/webhooks", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateWebhook: (token: string, id: string, data: any) =>
    request(`/api/v1/notifications/webhooks/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deleteWebhook: (token: string, id: string) =>
    request(`/api/v1/notifications/webhooks/${id}`, {
      method: "DELETE",
      token,
    }),

  testWebhook: (token: string, data: {
    url: string;
    method?: string;
    headers?: Record<string, string>;
    auth_type?: string;
    auth_config?: any;
    test_payload?: any;
  }) =>
    request("/api/v1/notifications/webhooks/test", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),
};

// User Management
export const userManagementAPI = {
  // Users
  listUsers: (token: string, params?: {
    page?: number;
    size?: number;
    search?: string;
    role?: string;
    is_active?: boolean;
    team_id?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.search) query.set("search", params.search);
    if (params?.role) query.set("role", params.role);
    if (params?.is_active !== undefined) query.set("is_active", params.is_active.toString());
    if (params?.team_id) query.set("team_id", params.team_id);
    return request(`/api/v1/users?${query}`, { token });
  },

  getUser: (token: string, userId: string) =>
    request(`/api/v1/users/${userId}`, { token }),

  getCurrentUser: (token: string) =>
    request("/api/v1/users/me", { token }),

  updateCurrentUser: (token: string, data: any) =>
    request("/api/v1/users/me", {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  updateUser: (token: string, userId: string, data: any) =>
    request(`/api/v1/users/${userId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deactivateUser: (token: string, userId: string) =>
    request(`/api/v1/users/${userId}/deactivate`, {
      method: "POST",
      token,
    }),

  activateUser: (token: string, userId: string) =>
    request(`/api/v1/users/${userId}/activate`, {
      method: "POST",
      token,
    }),

  getStats: (token: string) =>
    request("/api/v1/users/stats", { token }),

  // Teams
  listTeams: (token: string, params?: { page?: number; size?: number; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.search) query.set("search", params.search);
    return request(`/api/v1/users/teams/list?${query}`, { token });
  },

  createTeam: (token: string, data: any) =>
    request("/api/v1/users/teams", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getTeam: (token: string, teamId: string) =>
    request(`/api/v1/users/teams/${teamId}`, { token }),

  updateTeam: (token: string, teamId: string, data: any) =>
    request(`/api/v1/users/teams/${teamId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deleteTeam: (token: string, teamId: string) =>
    request(`/api/v1/users/teams/${teamId}`, {
      method: "DELETE",
      token,
    }),

  getTeamMembers: (token: string, teamId: string) =>
    request(`/api/v1/users/teams/${teamId}/members`, { token }),

  addTeamMember: (token: string, teamId: string, data: { user_id: string; role: string }) =>
    request(`/api/v1/users/teams/${teamId}/members`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  removeTeamMember: (token: string, teamId: string, userId: string) =>
    request(`/api/v1/users/teams/${teamId}/members/${userId}`, {
      method: "DELETE",
      token,
    }),

  // Roles
  listRoles: (token: string, params?: { page?: number; size?: number }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    return request(`/api/v1/users/roles/list?${query}`, { token });
  },

  createRole: (token: string, data: any) =>
    request("/api/v1/users/roles", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getRole: (token: string, roleId: string) =>
    request(`/api/v1/users/roles/${roleId}`, { token }),

  updateRole: (token: string, roleId: string, data: any) =>
    request(`/api/v1/users/roles/${roleId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deleteRole: (token: string, roleId: string) =>
    request(`/api/v1/users/roles/${roleId}`, {
      method: "DELETE",
      token,
    }),

  // Permissions
  listPermissions: (token: string, category?: string) => {
    const query = category ? `?category=${category}` : "";
    return request(`/api/v1/users/permissions/list${query}`, { token });
  },

  seedPermissions: (token: string) =>
    request("/api/v1/users/permissions/seed", {
      method: "POST",
      token,
    }),

  // Sessions
  getMySessions: (token: string) =>
    request("/api/v1/users/sessions/me", { token }),

  revokeSession: (token: string, sessionId: string) =>
    request(`/api/v1/users/sessions/${sessionId}`, {
      method: "DELETE",
      token,
    }),

  revokeAllSessions: (token: string) =>
    request("/api/v1/users/sessions/revoke-all", {
      method: "POST",
      token,
    }),

  // Invitations
  listInvitations: (token: string, params?: { page?: number; size?: number; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.status) query.set("status", params.status);
    return request(`/api/v1/users/invitations/list?${query}`, { token });
  },

  createInvitation: (token: string, data: any) =>
    request("/api/v1/users/invitations", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  revokeInvitation: (token: string, invitationId: string) =>
    request(`/api/v1/users/invitations/${invitationId}`, {
      method: "DELETE",
      token,
    }),

  // Activity Logs
  listActivityLogs: (token: string, params?: {
    page?: number;
    size?: number;
    user_id?: string;
    action?: string;
    resource_type?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.user_id) query.set("user_id", params.user_id);
    if (params?.action) query.set("action", params.action);
    if (params?.resource_type) query.set("resource_type", params.resource_type);
    return request(`/api/v1/users/activity/list?${query}`, { token });
  },

  // API Keys
  listAPIKeys: (token: string) =>
    request("/api/v1/users/api-keys/me", { token }),

  createAPIKey: (token: string, data: { name: string; scopes?: string[]; expires_in_days?: number }) =>
    request("/api/v1/users/api-keys", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  revokeAPIKey: (token: string, keyId: string) =>
    request(`/api/v1/users/api-keys/${keyId}`, {
      method: "DELETE",
      token,
    }),
};

// Attachments
export const attachmentsAPI = {
  list: (token: string, entityType: string, entityId: string, category?: string) => {
    const query = category ? `?category=${category}` : "";
    return request(`/api/v1/attachments/${entityType}/${entityId}${query}`, { token });
  },

  upload: async (
    token: string,
    entityType: string,
    entityId: string,
    file: File,
    category?: string,
    description?: string
  ) => {
    const formData = new FormData();
    formData.append("file", file);
    if (category) formData.append("category", category);
    if (description) formData.append("description", description);

    const response = await fetch(
      `${API_BASE_URL}/api/v1/attachments/upload/${entityType}/${entityId}`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Upload failed" }));
      throw new APIError(response.status, error.detail || "Upload failed");
    }

    return response.json();
  },

  download: async (token: string, attachmentId: string): Promise<{ blob: Blob; filename: string }> => {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/attachments/download/${attachmentId}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Download failed" }));
      throw new APIError(response.status, error.detail || "Download failed");
    }

    const blob = await response.blob();
    const contentDisposition = response.headers.get("content-disposition");
    let filename = "download";
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="(.+)"/);
      if (match) filename = match[1];
    }

    return { blob, filename };
  },

  getMetadata: (token: string, attachmentId: string) =>
    request(`/api/v1/attachments/metadata/${attachmentId}`, { token }),

  delete: (token: string, attachmentId: string, permanent = false) =>
    request(`/api/v1/attachments/${attachmentId}?permanent=${permanent}`, {
      method: "DELETE",
      token,
    }),

  bulkDelete: (token: string, attachmentIds: string[], permanent = false) =>
    request("/api/v1/attachments/bulk-delete", {
      method: "POST",
      body: JSON.stringify({ attachment_ids: attachmentIds, permanent }),
      token,
    }),

  verify: (token: string, attachmentId: string) =>
    request(`/api/v1/attachments/verify/${attachmentId}`, {
      method: "POST",
      token,
    }),

  getCount: (token: string, entityType: string, entityId: string) =>
    request(`/api/v1/attachments/count/${entityType}/${entityId}`, { token }),
};

// Analytics API
export const analyticsAPI = {
  // Trends
  getTrend: (token: string, entity: string, metric: string, periodDays = 30, aggregation = "daily") =>
    request(`/api/v1/analytics/trends/${entity}/${metric}?period_days=${periodDays}&aggregation=${aggregation}`, { token }),

  getPeriodComparison: (token: string, entity: string, periodDays = 30) =>
    request(`/api/v1/analytics/trends/${entity}/comparison?period_days=${periodDays}`, { token }),

  // Distribution
  getDistribution: (token: string, entity: string, groupBy: string) =>
    request(`/api/v1/analytics/distribution/${entity}/${groupBy}`, { token }),

  // Heatmaps
  getHeatmap: (token: string, type: string) =>
    request(`/api/v1/analytics/heatmap/${type}`, { token }),

  // Security Score
  getSecurityScore: (token: string) =>
    request("/api/v1/analytics/security-score", { token }),

  getSecurityScoreHistory: (token: string, periodDays = 30) =>
    request(`/api/v1/analytics/security-score/history?period_days=${periodDays}`, { token }),

  // SLA
  getSLACompliance: (token: string, type: string, periodDays = 30) =>
    request(`/api/v1/analytics/sla/compliance/${type}?period_days=${periodDays}`, { token }),

  getSLABreaches: (token: string, periodDays = 30) =>
    request(`/api/v1/analytics/sla/breaches?period_days=${periodDays}`, { token }),

  // Analyst Metrics
  getAnalystMetrics: (token: string, periodDays = 30) =>
    request(`/api/v1/analytics/analysts/metrics?period_days=${periodDays}`, { token }),

  getAnalystLeaderboard: (token: string, periodDays = 30, limit = 10) =>
    request(`/api/v1/analytics/analysts/leaderboard?period_days=${periodDays}&limit=${limit}`, { token }),

  // Vulnerability Aging
  getVulnerabilityAging: (token: string) =>
    request("/api/v1/analytics/vulnerabilities/aging", { token }),

  // Risk Trends
  getRiskTrends: (token: string, periodDays = 30) =>
    request(`/api/v1/analytics/risks/trends?period_days=${periodDays}`, { token }),
};

// Audit API
export const auditAPI = {
  // List audit logs with filters
  list: (
    token: string,
    params?: {
      user_id?: string;
      action?: string;
      action_category?: string;
      resource_type?: string;
      resource_id?: string;
      start_date?: string;
      end_date?: string;
      success?: boolean;
      severity?: string;
      search?: string;
      page?: number;
      size?: number;
    }
  ) => {
    const query = new URLSearchParams();
    if (params?.user_id) query.set("user_id", params.user_id);
    if (params?.action) query.set("action", params.action);
    if (params?.action_category) query.set("action_category", params.action_category);
    if (params?.resource_type) query.set("resource_type", params.resource_type);
    if (params?.resource_id) query.set("resource_id", params.resource_id);
    if (params?.start_date) query.set("start_date", params.start_date);
    if (params?.end_date) query.set("end_date", params.end_date);
    if (params?.success !== undefined) query.set("success", params.success.toString());
    if (params?.severity) query.set("severity", params.severity);
    if (params?.search) query.set("search", params.search);
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    return request(`/api/v1/audit/logs?${query}`, { token });
  },

  // Get single audit log with full details
  get: (token: string, logId: string) =>
    request(`/api/v1/audit/logs/${logId}`, { token }),

  // Get audit statistics
  getStats: (token: string) =>
    request("/api/v1/audit/stats", { token }),

  // Export audit logs
  export: async (
    token: string,
    params: {
      format?: string;
      user_id?: string;
      action?: string;
      resource_type?: string;
      start_date?: string;
      end_date?: string;
      severity?: string;
    }
  ) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/audit/export`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      throw new APIError(response.status, "Export failed");
    }

    const blob = await response.blob();
    const contentDisposition = response.headers.get("Content-Disposition");
    const filenameMatch = contentDisposition?.match(/filename="(.+)"/);
    const filename = filenameMatch ? filenameMatch[1] : `audit_logs.${params.format || "csv"}`;

    return { blob, filename };
  },

  // Get available actions and filters
  getActions: (token: string) =>
    request("/api/v1/audit/actions", { token }),
};

// ISO 27001:2022 Compliance
export const iso27001API = {
  // Reference Data
  getThemes: (token: string) =>
    request("/api/v1/iso27001/themes", { token }),

  getControls: (token: string, params?: {
    theme?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.theme) query.set("theme", params.theme);
    if (params?.search) query.set("search", params.search);
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    return request(`/api/v1/iso27001/controls?${query}`, { token });
  },

  getControl: (token: string, controlId: string) =>
    request(`/api/v1/iso27001/controls/${controlId}`, { token }),

  // Dashboard
  getDashboard: (token: string) =>
    request("/api/v1/iso27001/dashboard", { token }),

  // Assessment CRUD
  createAssessment: (token: string, data: { name: string; description?: string }) =>
    request("/api/v1/iso27001/assessments", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  listAssessments: (token: string, params?: {
    status?: string;
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    return request(`/api/v1/iso27001/assessments?${query}`, { token });
  },

  getAssessment: (token: string, assessmentId: string) =>
    request(`/api/v1/iso27001/assessments/${assessmentId}`, { token }),

  deleteAssessment: (token: string, assessmentId: string) =>
    request(`/api/v1/iso27001/assessments/${assessmentId}`, {
      method: "DELETE",
      token,
    }),

  // Wizard Steps
  updateScope: (token: string, assessmentId: string, data: {
    scope_description?: string;
    scope_systems?: string[];
    scope_locations?: string[];
    scope_processes?: string[];
    risk_appetite?: string;
  }) =>
    request(`/api/v1/iso27001/assessments/${assessmentId}/scope`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  getWizardState: (token: string, assessmentId: string) =>
    request(`/api/v1/iso27001/assessments/${assessmentId}/wizard-state`, { token }),

  // Statement of Applicability
  getSoAEntries: (token: string, assessmentId: string, theme?: string) => {
    const query = theme ? `?theme=${theme}` : "";
    return request(`/api/v1/iso27001/assessments/${assessmentId}/soa${query}`, { token });
  },

  updateSoAEntry: (token: string, assessmentId: string, controlCode: string, data: {
    applicability?: string;
    justification?: string;
    status?: string;
    implementation_level?: number;
    evidence?: string;
    implementation_notes?: string;
    gap_description?: string;
    remediation_plan?: string;
    remediation_owner?: string;
    remediation_due_date?: string;
    priority?: number;
  }) =>
    request(`/api/v1/iso27001/assessments/${assessmentId}/soa/${controlCode}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  bulkUpdateSoAEntries: (token: string, assessmentId: string, entries: Record<string, any>) =>
    request(`/api/v1/iso27001/assessments/${assessmentId}/soa`, {
      method: "PUT",
      body: JSON.stringify({ entries }),
      token,
    }),

  // Analysis & Reports
  getOverview: (token: string, assessmentId: string) =>
    request(`/api/v1/iso27001/assessments/${assessmentId}/overview`, { token }),

  getGapAnalysis: (token: string, assessmentId: string) =>
    request(`/api/v1/iso27001/assessments/${assessmentId}/gaps`, { token }),

  getCrossFrameworkMapping: (token: string, assessmentId: string) =>
    request(`/api/v1/iso27001/assessments/${assessmentId}/mapping`, { token }),

  getReport: (token: string, assessmentId: string, params?: {
    format?: string;
    include_gaps?: boolean;
    include_evidence?: boolean;
    language?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.format) query.set("format", params.format);
    if (params?.include_gaps !== undefined) query.set("include_gaps", params.include_gaps.toString());
    if (params?.include_evidence !== undefined) query.set("include_evidence", params.include_evidence.toString());
    if (params?.language) query.set("language", params.language);
    return request(`/api/v1/iso27001/assessments/${assessmentId}/report?${query}`, { token });
  },

  completeAssessment: (token: string, assessmentId: string, notes?: string) =>
    request(`/api/v1/iso27001/assessments/${assessmentId}/complete`, {
      method: "POST",
      body: JSON.stringify({ confirm: true, notes }),
      token,
    }),
};

// BCM (Business Continuity Management)
export const bcmAPI = {
  // Dashboard
  getDashboard: (token: string) =>
    request("/api/v1/bcm/dashboard", { token }),

  // Processes
  listProcesses: (token: string, params?: {
    criticality?: string;
    status?: string;
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.criticality) query.set("criticality", params.criticality);
    if (params?.status) query.set("status", params.status);
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    return request(`/api/v1/bcm/processes?${query}`, { token });
  },

  createProcess: (token: string, data: {
    process_id: string;
    name: string;
    description?: string;
    owner: string;
    department?: string;
    criticality?: string;
    internal_dependencies?: string[];
    external_dependencies?: string[];
    it_systems?: string[];
    key_personnel?: string[];
  }) =>
    request("/api/v1/bcm/processes", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getProcess: (token: string, processId: string) =>
    request(`/api/v1/bcm/processes/${processId}`, { token }),

  updateProcess: (token: string, processId: string, data: Record<string, unknown>) =>
    request(`/api/v1/bcm/processes/${processId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deleteProcess: (token: string, processId: string) =>
    request(`/api/v1/bcm/processes/${processId}`, {
      method: "DELETE",
      token,
    }),

  // BIA
  getProcessBIA: (token: string, processId: string) =>
    request(`/api/v1/bcm/processes/${processId}/bia`, { token }),

  // Alias for getProcessBIA
  getBIA: (token: string, processId: string) =>
    request(`/api/v1/bcm/processes/${processId}/bia`, { token }),

  createOrUpdateBIA: (token: string, processId: string, data: Record<string, unknown>) =>
    request(`/api/v1/bcm/processes/${processId}/bia`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getBIASummary: (token: string) =>
    request("/api/v1/bcm/bia/summary", { token }),

  // Scenarios
  listScenarios: (token: string, params?: {
    category?: string;
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.category) query.set("category", params.category);
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    return request(`/api/v1/bcm/scenarios?${query}`, { token });
  },

  createScenario: (token: string, data: Record<string, unknown>) =>
    request("/api/v1/bcm/scenarios", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getScenario: (token: string, scenarioId: string) =>
    request(`/api/v1/bcm/scenarios/${scenarioId}`, { token }),

  updateScenario: (token: string, scenarioId: string, data: Record<string, unknown>) =>
    request(`/api/v1/bcm/scenarios/${scenarioId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deleteScenario: (token: string, scenarioId: string) =>
    request(`/api/v1/bcm/scenarios/${scenarioId}`, {
      method: "DELETE",
      token,
    }),

  getRiskMatrix: (token: string) =>
    request("/api/v1/bcm/scenarios/risk-matrix", { token }),

  // Strategies
  listProcessStrategies: (token: string, processId: string) =>
    request(`/api/v1/bcm/processes/${processId}/strategies`, { token }),

  // Alias for listProcessStrategies
  listStrategies: (token: string, processId: string) =>
    request(`/api/v1/bcm/processes/${processId}/strategies`, { token }),

  createStrategy: (token: string, processId: string, data: Record<string, unknown>) =>
    request(`/api/v1/bcm/processes/${processId}/strategies`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateStrategy: (token: string, strategyId: string, data: Record<string, unknown>) =>
    request(`/api/v1/bcm/strategies/${strategyId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deleteStrategy: (token: string, strategyId: string) =>
    request(`/api/v1/bcm/strategies/${strategyId}`, {
      method: "DELETE",
      token,
    }),

  // Emergency Plans
  listPlans: (token: string, params?: {
    plan_type?: string;
    status?: string;
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.plan_type) query.set("plan_type", params.plan_type);
    if (params?.status) query.set("status", params.status);
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    return request(`/api/v1/bcm/plans?${query}`, { token });
  },

  createPlan: (token: string, data: Record<string, unknown>) =>
    request("/api/v1/bcm/plans", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getPlan: (token: string, planId: string) =>
    request(`/api/v1/bcm/plans/${planId}`, { token }),

  updatePlan: (token: string, planId: string, data: Record<string, unknown>) =>
    request(`/api/v1/bcm/plans/${planId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deletePlan: (token: string, planId: string) =>
    request(`/api/v1/bcm/plans/${planId}`, {
      method: "DELETE",
      token,
    }),

  approvePlan: (token: string, planId: string, approvedBy?: string) =>
    request(`/api/v1/bcm/plans/${planId}/approve`, {
      method: "POST",
      body: JSON.stringify({ approved_by: approvedBy }),
      token,
    }),

  exportPlan: (token: string, planId: string, format: string = "pdf") =>
    request(`/api/v1/bcm/plans/${planId}/export?format=${format}`, { token }),

  // Alias for PDF export
  exportPlanPdf: (token: string, planId: string) =>
    request(`/api/v1/bcm/plans/${planId}/export?format=pdf`, { token }),

  // Contacts
  listContacts: (token: string) =>
    request("/api/v1/bcm/contacts", { token }),

  createContact: (token: string, data: Record<string, unknown>) =>
    request("/api/v1/bcm/contacts", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateContact: (token: string, contactId: string, data: Record<string, unknown>) =>
    request(`/api/v1/bcm/contacts/${contactId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deleteContact: (token: string, contactId: string) =>
    request(`/api/v1/bcm/contacts/${contactId}`, {
      method: "DELETE",
      token,
    }),

  // Exercises
  listExercises: (token: string, params?: {
    status?: string;
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    return request(`/api/v1/bcm/exercises?${query}`, { token });
  },

  createExercise: (token: string, data: Record<string, unknown>) =>
    request("/api/v1/bcm/exercises", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getExercise: (token: string, exerciseId: string) =>
    request(`/api/v1/bcm/exercises/${exerciseId}`, { token }),

  updateExercise: (token: string, exerciseId: string, data: Record<string, unknown>) =>
    request(`/api/v1/bcm/exercises/${exerciseId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deleteExercise: (token: string, exerciseId: string) =>
    request(`/api/v1/bcm/exercises/${exerciseId}`, {
      method: "DELETE",
      token,
    }),

  completeExercise: (token: string, exerciseId: string, data: {
    actual_date: string;
    actual_duration_hours: number;
    results_summary: string;
    objectives_met?: Record<string, boolean>;
    issues_identified?: string[];
    lessons_learned?: string;
    action_items?: Array<Record<string, unknown>>;
  }) =>
    request(`/api/v1/bcm/exercises/${exerciseId}/complete`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  // Assessments
  listAssessments: (token: string, params?: {
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    return request(`/api/v1/bcm/assessments?${query}`, { token });
  },

  createAssessment: (token: string, data: { name: string; description?: string }) =>
    request("/api/v1/bcm/assessments", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getAssessment: (token: string, assessmentId: string) =>
    request(`/api/v1/bcm/assessments/${assessmentId}`, { token }),

  deleteAssessment: (token: string, assessmentId: string) =>
    request(`/api/v1/bcm/assessments/${assessmentId}`, {
      method: "DELETE",
      token,
    }),

  getWizardState: (token: string, assessmentId: string) =>
    request(`/api/v1/bcm/assessments/${assessmentId}/wizard-state`, { token }),

  completeAssessment: (token: string, assessmentId: string) =>
    request(`/api/v1/bcm/assessments/${assessmentId}/complete`, {
      method: "POST",
      body: JSON.stringify({ confirm: true }),
      token,
    }),

  getAssessmentReport: (token: string, assessmentId: string, format: string = "json") =>
    request(`/api/v1/bcm/assessments/${assessmentId}/report?format=${format}`, { token }),
};

// Attack Path Analysis
export const attackPathsAPI = {
  // Dashboard
  getDashboard: (token: string) =>
    request("/api/v1/attack-paths/dashboard", { token }),

  getChokepoints: (token: string, limit: number = 10) =>
    request(`/api/v1/attack-paths/chokepoints?limit=${limit}`, { token }),

  // Attack Graphs
  listGraphs: (token: string, params?: {
    page?: number;
    page_size?: number;
    status?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    if (params?.status) query.set("status", params.status);
    return request(`/api/v1/attack-paths/graphs?${query}`, { token });
  },

  createGraph: (token: string, data: {
    name: string;
    description?: string;
    scope_type?: string;
    scope_filter?: Record<string, unknown>;
  }) =>
    request("/api/v1/attack-paths/graphs", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getGraph: (token: string, graphId: string) =>
    request(`/api/v1/attack-paths/graphs/${graphId}`, { token }),

  updateGraph: (token: string, graphId: string, data: {
    name?: string;
    description?: string;
    scope_type?: string;
    scope_filter?: Record<string, unknown>;
  }) =>
    request(`/api/v1/attack-paths/graphs/${graphId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deleteGraph: (token: string, graphId: string) =>
    request(`/api/v1/attack-paths/graphs/${graphId}`, {
      method: "DELETE",
      token,
    }),

  refreshGraph: (token: string, graphId: string) =>
    request(`/api/v1/attack-paths/graphs/${graphId}/refresh`, {
      method: "POST",
      token,
    }),

  // Attack Paths
  listPaths: (token: string, graphId: string, params?: {
    page?: number;
    page_size?: number;
    min_risk_score?: number;
    status?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    if (params?.min_risk_score !== undefined) query.set("min_risk_score", params.min_risk_score.toString());
    if (params?.status) query.set("status", params.status);
    return request(`/api/v1/attack-paths/graphs/${graphId}/paths?${query}`, { token });
  },

  getPath: (token: string, pathId: string) =>
    request(`/api/v1/attack-paths/paths/${pathId}`, { token }),

  updatePathStatus: (token: string, pathId: string, data: {
    status: string;
    reason?: string;
  }) =>
    request(`/api/v1/attack-paths/paths/${pathId}/status`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  // Crown Jewels
  listCrownJewels: (token: string, params?: {
    page?: number;
    page_size?: number;
    jewel_type?: string;
    is_active?: boolean;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    if (params?.jewel_type) query.set("jewel_type", params.jewel_type);
    if (params?.is_active !== undefined) query.set("is_active", params.is_active.toString());
    return request(`/api/v1/attack-paths/crown-jewels?${query}`, { token });
  },

  createCrownJewel: (token: string, data: {
    asset_id: string;
    jewel_type: string;
    business_impact?: string;
    data_classification?: string;
    description: string;
    business_owner: string;
    data_types?: string[];
    compliance_scope?: string[];
    estimated_value?: number;
  }) =>
    request("/api/v1/attack-paths/crown-jewels", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getCrownJewel: (token: string, jewelId: string) =>
    request(`/api/v1/attack-paths/crown-jewels/${jewelId}`, { token }),

  updateCrownJewel: (token: string, jewelId: string, data: {
    jewel_type?: string;
    business_impact?: string;
    data_classification?: string;
    description?: string;
    business_owner?: string;
    data_types?: string[];
    compliance_scope?: string[];
    estimated_value?: number;
    is_active?: boolean;
  }) =>
    request(`/api/v1/attack-paths/crown-jewels/${jewelId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deleteCrownJewel: (token: string, jewelId: string) =>
    request(`/api/v1/attack-paths/crown-jewels/${jewelId}`, {
      method: "DELETE",
      token,
    }),

  // Entry Points
  listEntryPoints: (token: string, params?: {
    page?: number;
    page_size?: number;
    entry_type?: string;
    is_active?: boolean;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    if (params?.entry_type) query.set("entry_type", params.entry_type);
    if (params?.is_active !== undefined) query.set("is_active", params.is_active.toString());
    return request(`/api/v1/attack-paths/entry-points?${query}`, { token });
  },

  createEntryPoint: (token: string, data: {
    asset_id: string;
    entry_type: string;
    exposure_level?: string;
    protocols_exposed?: string[];
    ports_exposed?: number[];
    authentication_required?: boolean;
    mfa_enabled?: boolean;
    description: string;
    last_pentest_date?: string;
  }) =>
    request("/api/v1/attack-paths/entry-points", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getEntryPoint: (token: string, pointId: string) =>
    request(`/api/v1/attack-paths/entry-points/${pointId}`, { token }),

  updateEntryPoint: (token: string, pointId: string, data: {
    entry_type?: string;
    exposure_level?: string;
    protocols_exposed?: string[];
    ports_exposed?: number[];
    authentication_required?: boolean;
    mfa_enabled?: boolean;
    description?: string;
    last_pentest_date?: string;
    is_active?: boolean;
  }) =>
    request(`/api/v1/attack-paths/entry-points/${pointId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deleteEntryPoint: (token: string, pointId: string) =>
    request(`/api/v1/attack-paths/entry-points/${pointId}`, {
      method: "DELETE",
      token,
    }),

  // Simulations
  listSimulations: (token: string, params?: {
    graph_id?: string;
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.graph_id) query.set("graph_id", params.graph_id);
    if (params?.page) query.set("page", params.page.toString());
    if (params?.page_size) query.set("page_size", params.page_size.toString());
    return request(`/api/v1/attack-paths/simulations?${query}`, { token });
  },

  createSimulation: (token: string, data: {
    name: string;
    description?: string;
    graph_id: string;
    simulation_type: string;
    parameters: Record<string, unknown>;
  }) =>
    request("/api/v1/attack-paths/simulations", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getSimulation: (token: string, simulationId: string) =>
    request(`/api/v1/attack-paths/simulations/${simulationId}`, { token }),

  deleteSimulation: (token: string, simulationId: string) =>
    request(`/api/v1/attack-paths/simulations/${simulationId}`, {
      method: "DELETE",
      token,
    }),

  // Export
  exportGraphReport: async (token: string, graphId: string, params?: {
    include_paths?: boolean;
    include_assets?: boolean;
    include_recommendations?: boolean;
  }): Promise<Blob> => {
    const query = new URLSearchParams();
    if (params?.include_paths !== undefined) query.set("include_paths", params.include_paths.toString());
    if (params?.include_assets !== undefined) query.set("include_assets", params.include_assets.toString());
    if (params?.include_recommendations !== undefined) query.set("include_recommendations", params.include_recommendations.toString());

    const response = await fetch(`${API_BASE_URL}/api/v1/attack-paths/graphs/${graphId}/export?${query}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    return response.blob();
  },
};

// Document & Policy Management
export const documentsAPI = {
  // Dashboard
  getDashboard: (token: string) =>
    request("/api/v1/documents/dashboard", { token }),

  getStats: (token: string) =>
    request("/api/v1/documents/stats", { token }),

  // Documents CRUD
  list: (token: string, params?: {
    page?: number;
    size?: number;
    category?: string;
    status?: string;
    framework?: string;
    owner_id?: string;
    search?: string;
    tag?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.category) query.set("category", params.category);
    if (params?.status) query.set("status", params.status);
    if (params?.framework) query.set("framework", params.framework);
    if (params?.owner_id) query.set("owner_id", params.owner_id);
    if (params?.search) query.set("search", params.search);
    if (params?.tag) query.set("tag", params.tag);
    return request(`/api/v1/documents?${query}`, { token });
  },

  get: (token: string, documentId: string) =>
    request(`/api/v1/documents/${documentId}`, { token }),

  create: (token: string, data: {
    title: string;
    description?: string;
    category: string;
    content?: string;
    attachment_id?: string;
    owner_id?: string;
    department?: string;
    review_frequency_days?: number;
    frameworks?: string[];
    control_references?: string[];
    requires_acknowledgment?: boolean;
    acknowledgment_due_days?: number;
    approval_type?: string;
    tags?: string[];
    custom_metadata?: Record<string, unknown>;
  }) =>
    request("/api/v1/documents", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (token: string, documentId: string, data: {
    title?: string;
    description?: string;
    category?: string;
    content?: string;
    attachment_id?: string;
    owner_id?: string;
    department?: string;
    review_frequency_days?: number;
    frameworks?: string[];
    control_references?: string[];
    requires_acknowledgment?: boolean;
    acknowledgment_due_days?: number;
    approval_type?: string;
    tags?: string[];
    custom_metadata?: Record<string, unknown>;
  }) =>
    request(`/api/v1/documents/${documentId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, documentId: string) =>
    request(`/api/v1/documents/${documentId}`, {
      method: "DELETE",
      token,
    }),

  // Workflow
  submitForReview: (token: string, documentId: string, data: {
    approvers: Array<{ user_id: string; approval_order?: number }>;
    comments?: string;
  }) =>
    request(`/api/v1/documents/${documentId}/submit-review`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  approve: (token: string, documentId: string, comments?: string) =>
    request(`/api/v1/documents/${documentId}/approve`, {
      method: "POST",
      body: JSON.stringify({ comments }),
      token,
    }),

  reject: (token: string, documentId: string, comments: string) =>
    request(`/api/v1/documents/${documentId}/reject`, {
      method: "POST",
      body: JSON.stringify({ comments }),
      token,
    }),

  requestChanges: (token: string, documentId: string, comments: string) =>
    request(`/api/v1/documents/${documentId}/request-changes`, {
      method: "POST",
      body: JSON.stringify({ comments }),
      token,
    }),

  publish: (token: string, documentId: string, data?: {
    assign_acknowledgments_to?: string[];
    notify_subscribers?: boolean;
  }) =>
    request(`/api/v1/documents/${documentId}/publish`, {
      method: "POST",
      body: JSON.stringify(data || {}),
      token,
    }),

  archive: (token: string, documentId: string) =>
    request(`/api/v1/documents/${documentId}/archive`, {
      method: "POST",
      token,
    }),

  // Versions
  listVersions: (token: string, documentId: string) =>
    request(`/api/v1/documents/${documentId}/versions`, { token }),

  createVersion: (token: string, documentId: string, data: {
    change_summary: string;
    change_details?: string;
    version_type?: string;
    content?: string;
    attachment_id?: string;
  }) =>
    request(`/api/v1/documents/${documentId}/versions`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getVersion: (token: string, documentId: string, versionId: string) =>
    request(`/api/v1/documents/${documentId}/versions/${versionId}`, { token }),

  compareVersions: (token: string, documentId: string, versionA: string, versionB: string) =>
    request(`/api/v1/documents/${documentId}/versions/${versionA}/compare/${versionB}`, { token }),

  // Approvals
  getApprovalChain: (token: string, documentId: string) =>
    request(`/api/v1/documents/${documentId}/approvals`, { token }),

  getMyPendingApprovals: (token: string) =>
    request("/api/v1/documents/approvals/pending", { token }),

  // Acknowledgments
  listAcknowledgments: (token: string, documentId: string) =>
    request(`/api/v1/documents/${documentId}/acknowledgments`, { token }),

  assignAcknowledgments: (token: string, documentId: string, data: {
    user_ids: string[];
    due_date?: string;
  }) =>
    request(`/api/v1/documents/${documentId}/acknowledgments`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  acknowledge: (token: string, documentId: string) =>
    request(`/api/v1/documents/${documentId}/acknowledge`, {
      method: "POST",
      token,
    }),

  declineAcknowledgment: (token: string, documentId: string, reason: string) =>
    request(`/api/v1/documents/${documentId}/decline?reason=${encodeURIComponent(reason)}`, {
      method: "POST",
      token,
    }),

  getMyPendingAcknowledgments: (token: string) =>
    request("/api/v1/documents/acknowledgments/pending", { token }),

  sendAcknowledgmentReminder: (token: string, acknowledgmentId: string) =>
    request(`/api/v1/documents/acknowledgments/${acknowledgmentId}/remind`, {
      method: "POST",
      token,
    }),

  // Reviews
  listReviews: (token: string, documentId: string) =>
    request(`/api/v1/documents/${documentId}/reviews`, { token }),

  recordReview: (token: string, documentId: string, data: {
    outcome: string;
    review_notes?: string;
    action_items?: Array<Record<string, unknown>>;
    next_review_date?: string;
  }) =>
    request(`/api/v1/documents/${documentId}/reviews`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getDueForReview: (token: string, daysAhead: number = 30) =>
    request(`/api/v1/documents/due-for-review?days_ahead=${daysAhead}`, { token }),

  // Reports
  getComplianceReport: (token: string, params?: {
    start_date?: string;
    end_date?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.start_date) query.set("start_date", params.start_date);
    if (params?.end_date) query.set("end_date", params.end_date);
    return request(`/api/v1/documents/compliance-report?${query}`, { token });
  },
};

// Security Awareness & Training
export const trainingAPI = {
  // Dashboard
  getDashboard: (token: string) =>
    request("/api/v1/training/dashboard", { token }),

  // Course Catalog
  getCatalog: (token: string, params?: {
    page?: number;
    size?: number;
    category?: string;
    difficulty?: string;
    search?: string;
    framework?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.category) query.set("category", params.category);
    if (params?.difficulty) query.set("difficulty", params.difficulty);
    if (params?.search) query.set("search", params.search);
    if (params?.framework) query.set("framework", params.framework);
    return request(`/api/v1/training/catalog?${query}`, { token });
  },

  // Courses CRUD
  listCourses: (token: string, params?: {
    page?: number;
    size?: number;
    status?: string;
    category?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.status) query.set("status", params.status);
    if (params?.category) query.set("category", params.category);
    return request(`/api/v1/training/courses?${query}`, { token });
  },

  getCourse: (token: string, courseId: string) =>
    request(`/api/v1/training/courses/${courseId}`, { token }),

  createCourse: (token: string, data: {
    title: string;
    description?: string;
    category: string;
    difficulty?: string;
    estimated_duration_minutes?: number;
    passing_score?: number;
    certificate_enabled?: boolean;
    is_mandatory?: boolean;
    objectives?: string[];
    target_roles?: string[];
    target_departments?: string[];
    compliance_frameworks?: string[];
    control_references?: string[];
    tags?: string[];
  }) =>
    request("/api/v1/training/courses", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateCourse: (token: string, courseId: string, data: {
    title?: string;
    description?: string;
    category?: string;
    difficulty?: string;
    status?: string;
    estimated_duration_minutes?: number;
    passing_score?: number;
    certificate_enabled?: boolean;
    is_mandatory?: boolean;
    objectives?: string[];
    target_roles?: string[];
    target_departments?: string[];
    compliance_frameworks?: string[];
    control_references?: string[];
    tags?: string[];
  }) =>
    request(`/api/v1/training/courses/${courseId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deleteCourse: (token: string, courseId: string) =>
    request(`/api/v1/training/courses/${courseId}`, {
      method: "DELETE",
      token,
    }),

  publishCourse: (token: string, courseId: string) =>
    request(`/api/v1/training/courses/${courseId}/publish`, {
      method: "POST",
      token,
    }),

  // Course Modules
  getCourseModules: (token: string, courseId: string) =>
    request(`/api/v1/training/courses/${courseId}/modules`, { token }),

  createModule: (token: string, courseId: string, data: {
    title: string;
    description?: string;
    module_type: string;
    content?: string;
    video_url?: string;
    external_url?: string;
    attachment_id?: string;
    estimated_duration_minutes?: number;
  }) =>
    request(`/api/v1/training/courses/${courseId}/modules`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getModule: (token: string, moduleId: string) =>
    request(`/api/v1/training/modules/${moduleId}`, { token }),

  updateModule: (token: string, moduleId: string, data: {
    title?: string;
    description?: string;
    module_type?: string;
    content?: string;
    video_url?: string;
    external_url?: string;
    attachment_id?: string;
    estimated_duration_minutes?: number;
    order_index?: number;
  }) =>
    request(`/api/v1/training/modules/${moduleId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deleteModule: (token: string, moduleId: string) =>
    request(`/api/v1/training/modules/${moduleId}`, {
      method: "DELETE",
      token,
    }),

  reorderModules: (token: string, courseId: string, moduleIds: string[]) =>
    request(`/api/v1/training/courses/${courseId}/modules/reorder`, {
      method: "POST",
      body: JSON.stringify({ module_ids: moduleIds }),
      token,
    }),

  // Enrollment
  enrollInCourse: (token: string, courseId: string) =>
    request(`/api/v1/training/enroll/${courseId}`, {
      method: "POST",
      token,
    }),

  bulkEnroll: (token: string, courseId: string, data: {
    user_ids?: string[];
    role?: string;
    department?: string;
    deadline?: string;
  }) =>
    request(`/api/v1/training/courses/${courseId}/bulk-enroll`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getMyLearning: (token: string) =>
    request("/api/v1/training/my-learning", { token }),

  // Progress Tracking
  getModuleProgress: (token: string, moduleId: string) =>
    request(`/api/v1/training/modules/${moduleId}/progress`, { token }),

  updateModuleProgress: (token: string, moduleId: string, data: {
    progress_percent: number;
    time_spent_seconds?: number;
    bookmark?: Record<string, unknown>;
  }) =>
    request(`/api/v1/training/modules/${moduleId}/progress`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  completeModule: (token: string, moduleId: string) =>
    request(`/api/v1/training/modules/${moduleId}/complete`, {
      method: "POST",
      token,
    }),

  // Quizzes
  getQuiz: (token: string, quizId: string) =>
    request(`/api/v1/training/quizzes/${quizId}`, { token }),

  getQuizQuestions: (token: string, quizId: string) =>
    request(`/api/v1/training/quizzes/${quizId}/questions`, { token }),

  startQuiz: (token: string, quizId: string) =>
    request(`/api/v1/training/quizzes/${quizId}/start`, {
      method: "POST",
      token,
    }),

  submitQuiz: (token: string, attemptId: string, data: {
    answers: Array<{ question_id: string; selected_options?: number[]; text_answer?: string }>;
  }) =>
    request(`/api/v1/training/quizzes/attempts/${attemptId}/submit`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getQuizAttempt: (token: string, attemptId: string) =>
    request(`/api/v1/training/quizzes/attempts/${attemptId}`, { token }),

  getMyQuizAttempts: (token: string, quizId: string) =>
    request(`/api/v1/training/quizzes/${quizId}/my-attempts`, { token }),

  // Gamification
  getLeaderboard: (token: string, params?: {
    period?: string;
    limit?: number;
    department?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.period) query.set("period", params.period);
    if (params?.limit) query.set("limit", params.limit.toString());
    if (params?.department) query.set("department", params.department);
    return request(`/api/v1/training/leaderboard?${query}`, { token });
  },

  getMyStats: (token: string) =>
    request("/api/v1/training/my-stats", { token }),

  getMyBadges: (token: string) =>
    request("/api/v1/training/my-badges", { token }),

  // Badges (Admin)
  listBadges: (token: string, params?: {
    page?: number;
    size?: number;
    category?: string;
    is_active?: boolean;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.category) query.set("category", params.category);
    if (params?.is_active !== undefined) query.set("is_active", params.is_active.toString());
    return request(`/api/v1/training/badges?${query}`, { token });
  },

  createBadge: (token: string, data: {
    name: string;
    description?: string;
    category: string;
    icon?: string;
    color?: string;
    points_value?: number;
    criteria: Record<string, unknown>;
  }) =>
    request("/api/v1/training/badges", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  awardBadge: (token: string, userId: string, badgeId: string) =>
    request(`/api/v1/training/users/${userId}/badges/${badgeId}`, {
      method: "POST",
      token,
    }),

  // Phishing Campaigns
  listPhishingCampaigns: (token: string, params?: {
    page?: number;
    size?: number;
    status?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.status) query.set("status", params.status);
    return request(`/api/v1/phishing/campaigns?${query}`, { token });
  },

  createPhishingCampaign: (token: string, data: {
    name: string;
    description?: string;
    template_id: string;
    scheduled_start?: string;
    scheduled_end?: string;
    target_users?: string[];
    target_groups?: string[];
    target_roles?: string[];
    target_departments?: string[];
    sending_profile?: Record<string, unknown>;
  }) =>
    request("/api/v1/phishing/campaigns", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getPhishingCampaign: (token: string, campaignId: string) =>
    request(`/api/v1/phishing/campaigns/${campaignId}`, { token }),

  launchPhishingCampaign: (token: string, campaignId: string) =>
    request(`/api/v1/phishing/campaigns/${campaignId}/launch`, {
      method: "POST",
      token,
    }),

  getPhishingCampaignResults: (token: string, campaignId: string) =>
    request(`/api/v1/phishing/campaigns/${campaignId}/results`, { token }),

  // Phishing Templates
  listPhishingTemplates: (token: string, params?: {
    page?: number;
    size?: number;
    difficulty?: string;
    category?: string;
    is_active?: boolean;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.difficulty) query.set("difficulty", params.difficulty);
    if (params?.category) query.set("category", params.category);
    if (params?.is_active !== undefined) query.set("is_active", params.is_active.toString());
    return request(`/api/v1/phishing/templates?${query}`, { token });
  },

  createPhishingTemplate: (token: string, data: {
    name: string;
    description?: string;
    category: string;
    difficulty: string;
    subject: string;
    sender_name: string;
    sender_email: string;
    html_content: string;
    text_content?: string;
    landing_page_html?: string;
    indicators?: string[];
    training_content?: string;
  }) =>
    request("/api/v1/phishing/templates", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getPhishingTemplate: (token: string, templateId: string) =>
    request(`/api/v1/phishing/templates/${templateId}`, { token }),

  // Compliance Report
  getComplianceReport: (token: string, params?: {
    course_id?: string;
    department?: string;
    role?: string;
    start_date?: string;
    end_date?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.course_id) query.set("course_id", params.course_id);
    if (params?.department) query.set("department", params.department);
    if (params?.role) query.set("role", params.role);
    if (params?.start_date) query.set("start_date", params.start_date);
    if (params?.end_date) query.set("end_date", params.end_date);
    return request(`/api/v1/training/compliance-report?${query}`, { token });
  },
};

// BSI IT-Grundschutz API
export interface BSIAnforderung {
  id: string;
  anforderung_id: string;
  baustein_id: string;
  titel: string;
  typ: "MUSS" | "SOLLTE" | "KANN";
  beschreibung?: string;
  umsetzungshinweise?: string;
  cross_references?: Record<string, string[]>;
  compliance_status?: string;
  notes?: string;
}

export interface BSIBaustein {
  id: string;
  baustein_id: string;
  kategorie: string;
  titel: string;
  title_en?: string;
  beschreibung?: string;
  version?: string;
  ir_phases?: string[];
}

export const bsiGrundschutzAPI = {
  getBaustein: (token: string, bausteinId: string, schutzbedarf?: string) => {
    const query = schutzbedarf ? `?schutzbedarf=${schutzbedarf}` : "";
    return request<{
      baustein: BSIBaustein;
      anforderungen: BSIAnforderung[];
      anforderungen_count: { total: number; muss: number; sollte: number; kann: number };
    }>(`/api/v1/bsi/grundschutz/bausteine/${encodeURIComponent(bausteinId)}${query}`, { token });
  },

  getBausteinScore: (token: string, bausteinId: string, params?: { schutzbedarf?: string }) => {
    const query = params?.schutzbedarf ? `?schutzbedarf=${params.schutzbedarf}` : "";
    return request<{
      score_percent: number;
      compliant: number;
      partial: number;
      gap: number;
      not_evaluated: number;
      not_applicable: number;
    }>(`/api/v1/bsi/grundschutz/compliance/score/${encodeURIComponent(bausteinId)}${query}`, { token });
  },

  updateComplianceStatus: (token: string, data: { anforderung_id: string; status: string; notes?: string }) =>
    request("/api/v1/bsi/grundschutz/compliance/status", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  getKategorien: (token: string) =>
    request<{ kategorien: Array<{ kategorie: string; name_de: string; name_en: string; baustein_count: number }> }>(
      "/api/v1/bsi/grundschutz/kategorien",
      { token }
    ),

  getBausteine: (token: string, params?: { kategorie?: string; search?: string; size?: number }) => {
    const query = new URLSearchParams();
    if (params?.kategorie) query.set("kategorie", params.kategorie);
    if (params?.search) query.set("search", params.search);
    if (params?.size) query.set("size", params.size.toString());
    return request<{ bausteine: BSIBaustein[] }>(`/api/v1/bsi/grundschutz/bausteine?${query}`, { token });
  },

  getComplianceOverview: (token: string, schutzbedarf?: string) => {
    const query = schutzbedarf ? `?schutzbedarf=${schutzbedarf}` : "";
    return request<{
      overall_score_percent: number;
      compliant: number;
      partial: number;
      gap: number;
      not_evaluated: number;
    }>(`/api/v1/bsi/grundschutz/compliance/overview${query}`, { token });
  },
};

export { APIError };
