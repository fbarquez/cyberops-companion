"""
OWASP Integration Module for CyberOps Companion.

Provides:
- OWASP Top 10 (2021) vulnerability categorization
- OWASP Cheat Sheet Series references for remediation
- Mapping to incident response phases
- Web application security guidance
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class OWASPCategory(Enum):
    """OWASP Top 10 2021 Categories."""
    A01_BROKEN_ACCESS_CONTROL = "A01:2021"
    A02_CRYPTOGRAPHIC_FAILURES = "A02:2021"
    A03_INJECTION = "A03:2021"
    A04_INSECURE_DESIGN = "A04:2021"
    A05_SECURITY_MISCONFIGURATION = "A05:2021"
    A06_VULNERABLE_COMPONENTS = "A06:2021"
    A07_AUTH_FAILURES = "A07:2021"
    A08_SOFTWARE_DATA_INTEGRITY = "A08:2021"
    A09_LOGGING_MONITORING_FAILURES = "A09:2021"
    A10_SSRF = "A10:2021"


@dataclass
class OWASPRisk:
    """Represents an OWASP Top 10 risk category."""
    id: str
    name: str
    description: str
    cwe_mapped: List[str]
    attack_vectors: List[str]
    impact: str
    prevention: List[str]
    cheat_sheets: List[str]
    detection_indicators: List[str]
    ir_phase_relevance: Dict[str, str]


@dataclass
class CheatSheet:
    """OWASP Cheat Sheet reference."""
    name: str
    url: str
    category: str
    summary: str
    key_points: List[str]


class OWASPIntegration:
    """
    OWASP Top 10 and Cheat Sheet Series integration.

    Provides vulnerability categorization, remediation guidance,
    and mapping to incident response activities.
    """

    def __init__(self):
        self._top_10 = self._load_owasp_top_10()
        self._cheat_sheets = self._load_cheat_sheets()
        self._phase_mappings = self._load_phase_mappings()

    def _load_owasp_top_10(self) -> Dict[str, OWASPRisk]:
        """Load OWASP Top 10 2021 definitions."""
        return {
            "A01:2021": OWASPRisk(
                id="A01:2021",
                name="Broken Access Control",
                description="Failures in enforcing proper access restrictions, allowing users to act outside their intended permissions.",
                cwe_mapped=["CWE-200", "CWE-201", "CWE-352", "CWE-284", "CWE-285", "CWE-639", "CWE-918"],
                attack_vectors=[
                    "URL/parameter manipulation",
                    "Insecure direct object references (IDOR)",
                    "Missing function-level access control",
                    "CORS misconfiguration",
                    "JWT token manipulation",
                    "Privilege escalation",
                ],
                impact="Unauthorized access to data, modification, or destruction. Full system compromise possible.",
                prevention=[
                    "Implement proper access control checks server-side",
                    "Deny by default except for public resources",
                    "Use role-based access control (RBAC)",
                    "Disable web server directory listing",
                    "Log access control failures and alert on repeated attempts",
                    "Rate limit API access",
                    "Invalidate JWT tokens on logout",
                ],
                cheat_sheets=[
                    "Authorization Cheat Sheet",
                    "Access Control Cheat Sheet",
                    "Cross-Site Request Forgery Prevention Cheat Sheet",
                    "JSON Web Token Cheat Sheet",
                ],
                detection_indicators=[
                    "Unusual access patterns to restricted resources",
                    "Failed authorization attempts in logs",
                    "Access to admin functions from non-admin users",
                    "IDOR exploitation attempts in URLs",
                ],
                ir_phase_relevance={
                    "detection": "Monitor for unauthorized access attempts and privilege escalation",
                    "analysis": "Analyze access logs for scope of unauthorized access",
                    "containment": "Revoke compromised credentials and sessions immediately",
                    "eradication": "Fix access control vulnerabilities, implement RBAC",
                    "recovery": "Audit all access controls before restoring services",
                },
            ),
            "A02:2021": OWASPRisk(
                id="A02:2021",
                name="Cryptographic Failures",
                description="Failures related to cryptography which often lead to exposure of sensitive data.",
                cwe_mapped=["CWE-259", "CWE-327", "CWE-331", "CWE-321", "CWE-322", "CWE-323", "CWE-328", "CWE-330"],
                attack_vectors=[
                    "Man-in-the-middle attacks",
                    "Data exfiltration of unencrypted data",
                    "Weak cipher exploitation",
                    "Password hash cracking",
                    "Key extraction",
                ],
                impact="Exposure of sensitive data including credentials, PII, financial data, health records.",
                prevention=[
                    "Classify and encrypt sensitive data at rest and in transit",
                    "Use strong, up-to-date algorithms (AES-256, RSA-2048+)",
                    "Enforce TLS 1.2+ with strong cipher suites",
                    "Use proper key management",
                    "Hash passwords with Argon2, bcrypt, or scrypt",
                    "Disable caching for sensitive data responses",
                ],
                cheat_sheets=[
                    "Cryptographic Storage Cheat Sheet",
                    "Transport Layer Security Cheat Sheet",
                    "Password Storage Cheat Sheet",
                    "Key Management Cheat Sheet",
                    "HTTP Strict Transport Security Cheat Sheet",
                ],
                detection_indicators=[
                    "Unencrypted data transmission detected",
                    "Weak cipher suites in use",
                    "Certificate errors or warnings",
                    "Plaintext passwords or sensitive data in logs",
                ],
                ir_phase_relevance={
                    "detection": "Monitor for unencrypted sensitive data transmission",
                    "analysis": "Identify what sensitive data was exposed and its encryption status",
                    "containment": "Force password resets, rotate compromised keys",
                    "eradication": "Implement proper encryption for all sensitive data",
                    "recovery": "Verify encryption is properly configured before restoration",
                },
            ),
            "A03:2021": OWASPRisk(
                id="A03:2021",
                name="Injection",
                description="Untrusted data sent to an interpreter as part of a command or query, including SQL, NoSQL, OS, LDAP injection.",
                cwe_mapped=["CWE-79", "CWE-89", "CWE-73", "CWE-74", "CWE-75", "CWE-77", "CWE-78", "CWE-88", "CWE-917"],
                attack_vectors=[
                    "SQL injection",
                    "NoSQL injection",
                    "OS command injection",
                    "LDAP injection",
                    "XPath injection",
                    "Cross-site scripting (XSS)",
                    "Template injection",
                ],
                impact="Data theft, data corruption, denial of service, complete host takeover.",
                prevention=[
                    "Use parameterized queries / prepared statements",
                    "Use ORM frameworks properly",
                    "Implement input validation with allowlists",
                    "Escape special characters for the specific interpreter",
                    "Use LIMIT in SQL queries to prevent mass disclosure",
                    "Implement Content Security Policy (CSP) for XSS",
                ],
                cheat_sheets=[
                    "SQL Injection Prevention Cheat Sheet",
                    "Query Parameterization Cheat Sheet",
                    "Cross Site Scripting Prevention Cheat Sheet",
                    "DOM based XSS Prevention Cheat Sheet",
                    "Injection Prevention Cheat Sheet",
                    "Input Validation Cheat Sheet",
                    "OS Command Injection Defense Cheat Sheet",
                    "LDAP Injection Prevention Cheat Sheet",
                ],
                detection_indicators=[
                    "SQL syntax in user inputs or logs",
                    "Error messages revealing database structure",
                    "Unusual database query patterns",
                    "Script tags or JavaScript in input fields",
                    "Shell commands in application logs",
                ],
                ir_phase_relevance={
                    "detection": "Monitor WAF logs for injection attempts, database errors",
                    "analysis": "Identify injection vectors and scope of data access",
                    "containment": "Block malicious IPs, disable vulnerable endpoints",
                    "eradication": "Patch injection vulnerabilities, implement parameterized queries",
                    "recovery": "Verify data integrity, restore from clean backups if needed",
                },
            ),
            "A04:2021": OWASPRisk(
                id="A04:2021",
                name="Insecure Design",
                description="Missing or ineffective control design. Flaws in the design and architecture of the application.",
                cwe_mapped=["CWE-209", "CWE-256", "CWE-501", "CWE-522", "CWE-656", "CWE-799", "CWE-840"],
                attack_vectors=[
                    "Business logic flaws",
                    "Missing rate limiting",
                    "Lack of tenant isolation",
                    "Trust boundary violations",
                    "Insufficient fraud controls",
                ],
                impact="Complete business logic bypass, fraud, data breach through design flaws.",
                prevention=[
                    "Establish secure development lifecycle (SDLC)",
                    "Use threat modeling for critical features",
                    "Integrate security in user stories",
                    "Implement defense in depth",
                    "Limit resource consumption per user/session",
                    "Separate tenants securely",
                ],
                cheat_sheets=[
                    "Threat Modeling Cheat Sheet",
                    "Secure Product Design Cheat Sheet",
                    "Attack Surface Analysis Cheat Sheet",
                    "Abuse Case Cheat Sheet",
                ],
                detection_indicators=[
                    "Unusual business logic patterns",
                    "Excessive resource consumption",
                    "Cross-tenant data access",
                    "Bypassed workflow steps",
                ],
                ir_phase_relevance={
                    "detection": "Monitor for business logic anomalies",
                    "analysis": "Identify design flaws that enabled the attack",
                    "containment": "Implement compensating controls",
                    "eradication": "Redesign vulnerable components with security in mind",
                    "recovery": "Conduct threat modeling before redeployment",
                },
            ),
            "A05:2021": OWASPRisk(
                id="A05:2021",
                name="Security Misconfiguration",
                description="Missing security hardening, improperly configured permissions, unnecessary features enabled, default credentials.",
                cwe_mapped=["CWE-16", "CWE-611", "CWE-614", "CWE-756", "CWE-776", "CWE-942", "CWE-1004"],
                attack_vectors=[
                    "Default credentials exploitation",
                    "Unnecessary services/features exploitation",
                    "Verbose error message information disclosure",
                    "Cloud storage misconfiguration",
                    "Missing security headers",
                    "XML External Entity (XXE) attacks",
                ],
                impact="System compromise, data exposure, full server access through misconfigurations.",
                prevention=[
                    "Implement repeatable hardening process",
                    "Remove unused features, frameworks, components",
                    "Review and update configurations regularly",
                    "Use infrastructure as code with security scanning",
                    "Implement proper security headers",
                    "Change all default credentials",
                    "Disable XML external entity processing",
                ],
                cheat_sheets=[
                    "Docker Security Cheat Sheet",
                    "Kubernetes Security Cheat Sheet",
                    "Server Side Request Forgery Prevention Cheat Sheet",
                    "XML External Entity Prevention Cheat Sheet",
                    "HTTP Headers Cheat Sheet",
                    "Database Security Cheat Sheet",
                    "Virtual Patching Cheat Sheet",
                ],
                detection_indicators=[
                    "Default credentials in use",
                    "Verbose error messages exposed",
                    "Unnecessary ports/services open",
                    "Missing security headers in responses",
                    "Public cloud storage buckets",
                ],
                ir_phase_relevance={
                    "detection": "Scan for misconfigurations, default credentials",
                    "analysis": "Identify all misconfigured components exploited",
                    "containment": "Disable unnecessary services, change credentials",
                    "eradication": "Apply security hardening across all systems",
                    "recovery": "Verify hardened configuration before restoration",
                },
            ),
            "A06:2021": OWASPRisk(
                id="A06:2021",
                name="Vulnerable and Outdated Components",
                description="Using components with known vulnerabilities or unsupported/outdated software.",
                cwe_mapped=["CWE-937", "CWE-1035", "CWE-1104"],
                attack_vectors=[
                    "Known CVE exploitation",
                    "Supply chain attacks",
                    "Dependency confusion",
                    "Outdated library exploitation",
                    "Unpatched system compromise",
                ],
                impact="Full system compromise through known vulnerabilities, supply chain breach.",
                prevention=[
                    "Remove unused dependencies",
                    "Continuously inventory component versions",
                    "Monitor CVE databases and security advisories",
                    "Use software composition analysis (SCA) tools",
                    "Obtain components from official sources only",
                    "Implement automated patching process",
                ],
                cheat_sheets=[
                    "Vulnerable Dependency Management Cheat Sheet",
                    "Third Party JavaScript Management Cheat Sheet",
                    "NPM Security Cheat Sheet",
                ],
                detection_indicators=[
                    "Outdated software versions in inventory",
                    "Known CVEs matching component versions",
                    "Exploitation attempts targeting known vulnerabilities",
                    "Suspicious package downloads",
                ],
                ir_phase_relevance={
                    "detection": "Monitor for exploitation of known CVEs",
                    "analysis": "Inventory all affected components and their CVEs",
                    "containment": "Isolate systems with critical unpatched vulnerabilities",
                    "eradication": "Patch or replace all vulnerable components",
                    "recovery": "Verify all components are updated before restoration",
                },
            ),
            "A07:2021": OWASPRisk(
                id="A07:2021",
                name="Identification and Authentication Failures",
                description="Failures in confirming user identity, authentication, and session management.",
                cwe_mapped=["CWE-255", "CWE-259", "CWE-287", "CWE-288", "CWE-290", "CWE-294", "CWE-295", "CWE-297", "CWE-300", "CWE-302", "CWE-304", "CWE-306", "CWE-307", "CWE-346", "CWE-384", "CWE-521", "CWE-613", "CWE-620", "CWE-640", "CWE-798", "CWE-940", "CWE-1216"],
                attack_vectors=[
                    "Credential stuffing",
                    "Brute force attacks",
                    "Session hijacking",
                    "Session fixation",
                    "Weak password policies",
                    "Missing MFA bypass",
                ],
                impact="Account takeover, identity theft, unauthorized access to systems and data.",
                prevention=[
                    "Implement multi-factor authentication (MFA)",
                    "Use strong password policies",
                    "Implement account lockout with increasing delays",
                    "Use secure session management",
                    "Generate new session ID on login",
                    "Implement proper logout functionality",
                    "Use secure password recovery mechanisms",
                ],
                cheat_sheets=[
                    "Authentication Cheat Sheet",
                    "Session Management Cheat Sheet",
                    "Forgot Password Cheat Sheet",
                    "Credential Stuffing Prevention Cheat Sheet",
                    "Multifactor Authentication Cheat Sheet",
                    "Password Storage Cheat Sheet",
                    "SAML Security Cheat Sheet",
                ],
                detection_indicators=[
                    "Multiple failed login attempts",
                    "Login from unusual locations/devices",
                    "Session anomalies",
                    "Password spray patterns",
                    "Credential stuffing traffic patterns",
                ],
                ir_phase_relevance={
                    "detection": "Monitor for authentication anomalies, brute force",
                    "analysis": "Identify compromised accounts and access scope",
                    "containment": "Force password resets, invalidate sessions, enable MFA",
                    "eradication": "Strengthen authentication mechanisms",
                    "recovery": "Verify all authentication is hardened before restoration",
                },
            ),
            "A08:2021": OWASPRisk(
                id="A08:2021",
                name="Software and Data Integrity Failures",
                description="Code and infrastructure that does not protect against integrity violations, including insecure CI/CD pipelines.",
                cwe_mapped=["CWE-345", "CWE-353", "CWE-426", "CWE-494", "CWE-502", "CWE-565", "CWE-784", "CWE-829", "CWE-830", "CWE-913"],
                attack_vectors=[
                    "Insecure deserialization",
                    "CI/CD pipeline compromise",
                    "Unsigned software updates",
                    "Supply chain attacks",
                    "Cache poisoning",
                ],
                impact="Remote code execution, supply chain compromise, malware injection.",
                prevention=[
                    "Use digital signatures for software and data",
                    "Verify software integrity (checksums, signatures)",
                    "Use trusted repositories with signature verification",
                    "Implement CI/CD pipeline security",
                    "Avoid insecure deserialization",
                    "Use integrity checks in CI/CD",
                ],
                cheat_sheets=[
                    "Deserialization Cheat Sheet",
                    "CI CD Security Cheat Sheet",
                    "Software Supply Chain Security Cheat Sheet",
                ],
                detection_indicators=[
                    "Unsigned or tampered software",
                    "CI/CD pipeline modifications",
                    "Unexpected code changes",
                    "Deserialization errors",
                    "Supply chain anomalies",
                ],
                ir_phase_relevance={
                    "detection": "Monitor CI/CD, verify software signatures",
                    "analysis": "Identify integrity violations and their source",
                    "containment": "Isolate compromised build systems",
                    "eradication": "Rebuild from verified clean sources",
                    "recovery": "Implement integrity verification before deployment",
                },
            ),
            "A09:2021": OWASPRisk(
                id="A09:2021",
                name="Security Logging and Monitoring Failures",
                description="Insufficient logging, detection, monitoring, and active response to breaches.",
                cwe_mapped=["CWE-117", "CWE-223", "CWE-532", "CWE-778"],
                attack_vectors=[
                    "Undetected attacks due to poor logging",
                    "Log injection",
                    "Log tampering",
                    "Alert fatigue exploitation",
                    "Delayed incident detection",
                ],
                impact="Attacks go undetected, extended breach duration, inability to perform forensics.",
                prevention=[
                    "Log all authentication and access control events",
                    "Ensure logs are in a format for log management",
                    "Implement real-time alerting",
                    "Establish incident response plan",
                    "Protect log integrity",
                    "Use centralized log management (SIEM)",
                ],
                cheat_sheets=[
                    "Logging Cheat Sheet",
                    "Application Logging Vocabulary Cheat Sheet",
                    "Logging Vocabulary Cheat Sheet",
                ],
                detection_indicators=[
                    "Missing or incomplete logs",
                    "Log gaps during suspicious periods",
                    "Disabled logging discovered",
                    "Log injection attempts",
                ],
                ir_phase_relevance={
                    "detection": "This IS detection - ensure comprehensive logging",
                    "analysis": "Review logs for attack timeline and scope",
                    "containment": "Preserve logs, enable enhanced logging",
                    "eradication": "Improve logging coverage and retention",
                    "recovery": "Verify logging is fully operational",
                },
            ),
            "A10:2021": OWASPRisk(
                id="A10:2021",
                name="Server-Side Request Forgery (SSRF)",
                description="Web application fetches a remote resource without validating the user-supplied URL.",
                cwe_mapped=["CWE-918"],
                attack_vectors=[
                    "Internal service scanning",
                    "Cloud metadata endpoint access",
                    "Internal API abuse",
                    "Firewall bypass",
                    "Remote code execution via SSRF chains",
                ],
                impact="Internal network reconnaissance, cloud credential theft, internal service compromise.",
                prevention=[
                    "Validate and sanitize all user-supplied URLs",
                    "Use allowlists for permitted domains/IPs",
                    "Block requests to internal/private IP ranges",
                    "Disable HTTP redirects",
                    "Use network segmentation",
                    "Block access to cloud metadata endpoints (169.254.169.254)",
                ],
                cheat_sheets=[
                    "Server Side Request Forgery Prevention Cheat Sheet",
                    "Unvalidated Redirects and Forwards Cheat Sheet",
                ],
                detection_indicators=[
                    "Requests to internal IP addresses",
                    "Requests to cloud metadata endpoints",
                    "URL parameters with internal URLs",
                    "Unusual outbound connections from web servers",
                ],
                ir_phase_relevance={
                    "detection": "Monitor for internal/metadata endpoint access",
                    "analysis": "Identify what internal resources were accessed",
                    "containment": "Block vulnerable endpoints, rotate cloud credentials",
                    "eradication": "Implement URL validation and allowlisting",
                    "recovery": "Verify network segmentation before restoration",
                },
            ),
        }

    def _load_cheat_sheets(self) -> Dict[str, CheatSheet]:
        """Load OWASP Cheat Sheet Series references."""
        base_url = "https://cheatsheetseries.owasp.org/cheatsheets"

        return {
            "Authentication Cheat Sheet": CheatSheet(
                name="Authentication Cheat Sheet",
                url=f"{base_url}/Authentication_Cheat_Sheet.html",
                category="Identity",
                summary="Best practices for implementing authentication mechanisms.",
                key_points=[
                    "Use secure password hashing (Argon2, bcrypt)",
                    "Implement MFA where possible",
                    "Use secure session management",
                    "Protect against brute force",
                    "Implement proper error messages",
                ],
            ),
            "Authorization Cheat Sheet": CheatSheet(
                name="Authorization Cheat Sheet",
                url=f"{base_url}/Authorization_Cheat_Sheet.html",
                category="Access Control",
                summary="Implementing proper authorization and access control.",
                key_points=[
                    "Centralize authorization logic",
                    "Deny by default",
                    "Validate on every request",
                    "Use role-based access control",
                    "Log authorization failures",
                ],
            ),
            "SQL Injection Prevention Cheat Sheet": CheatSheet(
                name="SQL Injection Prevention Cheat Sheet",
                url=f"{base_url}/SQL_Injection_Prevention_Cheat_Sheet.html",
                category="Injection",
                summary="Preventing SQL injection vulnerabilities.",
                key_points=[
                    "Use parameterized queries",
                    "Use stored procedures carefully",
                    "Validate input with allowlists",
                    "Escape user input as last resort",
                    "Use least privilege for DB accounts",
                ],
            ),
            "Cross Site Scripting Prevention Cheat Sheet": CheatSheet(
                name="Cross Site Scripting Prevention Cheat Sheet",
                url=f"{base_url}/Cross_Site_Scripting_Prevention_Cheat_Sheet.html",
                category="Injection",
                summary="Preventing XSS vulnerabilities in web applications.",
                key_points=[
                    "Encode output based on context",
                    "Use Content Security Policy (CSP)",
                    "Validate and sanitize input",
                    "Use HTTPOnly and Secure cookie flags",
                    "Avoid innerHTML, use textContent",
                ],
            ),
            "Session Management Cheat Sheet": CheatSheet(
                name="Session Management Cheat Sheet",
                url=f"{base_url}/Session_Management_Cheat_Sheet.html",
                category="Identity",
                summary="Secure session management implementation.",
                key_points=[
                    "Generate cryptographically secure session IDs",
                    "Regenerate session ID after login",
                    "Set proper session timeouts",
                    "Use Secure and HTTPOnly flags",
                    "Implement absolute session timeout",
                ],
            ),
            "Password Storage Cheat Sheet": CheatSheet(
                name="Password Storage Cheat Sheet",
                url=f"{base_url}/Password_Storage_Cheat_Sheet.html",
                category="Cryptography",
                summary="Secure password storage recommendations.",
                key_points=[
                    "Use Argon2id as first choice",
                    "bcrypt as second choice",
                    "Use appropriate work factors",
                    "Generate unique salt per password",
                    "Use pepper for additional security",
                ],
            ),
            "Logging Cheat Sheet": CheatSheet(
                name="Logging Cheat Sheet",
                url=f"{base_url}/Logging_Cheat_Sheet.html",
                category="Monitoring",
                summary="Security logging best practices.",
                key_points=[
                    "Log authentication events",
                    "Log access control failures",
                    "Include timestamp, user, action, resource",
                    "Protect logs from tampering",
                    "Don't log sensitive data",
                ],
            ),
            "Input Validation Cheat Sheet": CheatSheet(
                name="Input Validation Cheat Sheet",
                url=f"{base_url}/Input_Validation_Cheat_Sheet.html",
                category="Injection",
                summary="Proper input validation techniques.",
                key_points=[
                    "Validate on server side",
                    "Use allowlists over blocklists",
                    "Validate data type, length, format, range",
                    "Canonicalize before validation",
                    "Reject invalid input, don't sanitize",
                ],
            ),
            "Cryptographic Storage Cheat Sheet": CheatSheet(
                name="Cryptographic Storage Cheat Sheet",
                url=f"{base_url}/Cryptographic_Storage_Cheat_Sheet.html",
                category="Cryptography",
                summary="Secure cryptographic storage practices.",
                key_points=[
                    "Use AES-256-GCM for encryption",
                    "Use secure key management",
                    "Rotate keys regularly",
                    "Use authenticated encryption",
                    "Protect encryption keys",
                ],
            ),
            "Transport Layer Security Cheat Sheet": CheatSheet(
                name="Transport Layer Security Cheat Sheet",
                url=f"{base_url}/Transport_Layer_Security_Cheat_Sheet.html",
                category="Cryptography",
                summary="TLS configuration best practices.",
                key_points=[
                    "Use TLS 1.2 or 1.3 only",
                    "Use strong cipher suites",
                    "Enable HSTS",
                    "Use valid certificates",
                    "Disable compression",
                ],
            ),
            "Docker Security Cheat Sheet": CheatSheet(
                name="Docker Security Cheat Sheet",
                url=f"{base_url}/Docker_Security_Cheat_Sheet.html",
                category="Infrastructure",
                summary="Container security best practices.",
                key_points=[
                    "Use minimal base images",
                    "Don't run as root",
                    "Scan images for vulnerabilities",
                    "Use read-only filesystems",
                    "Limit resources and capabilities",
                ],
            ),
            "Kubernetes Security Cheat Sheet": CheatSheet(
                name="Kubernetes Security Cheat Sheet",
                url=f"{base_url}/Kubernetes_Security_Cheat_Sheet.html",
                category="Infrastructure",
                summary="Kubernetes cluster security.",
                key_points=[
                    "Enable RBAC",
                    "Use network policies",
                    "Enable pod security policies",
                    "Encrypt secrets at rest",
                    "Audit logging enabled",
                ],
            ),
            "Incident Response Cheat Sheet": CheatSheet(
                name="Incident Response Cheat Sheet",
                url=f"{base_url}/Incident_Response_Cheat_Sheet.html",
                category="Operations",
                summary="Web application incident response guidance.",
                key_points=[
                    "Have an IR plan before incidents",
                    "Preserve evidence properly",
                    "Communicate with stakeholders",
                    "Document everything",
                    "Conduct post-incident review",
                ],
            ),
        }

    def _load_phase_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Map OWASP resources to IR phases."""
        return {
            "detection": {
                "primary_risks": ["A09:2021", "A07:2021", "A01:2021"],
                "cheat_sheets": [
                    "Logging Cheat Sheet",
                    "Authentication Cheat Sheet",
                    "Authorization Cheat Sheet",
                ],
                "focus": "Ensure logging captures security events for detection",
            },
            "analysis": {
                "primary_risks": ["A03:2021", "A01:2021", "A06:2021", "A07:2021"],
                "cheat_sheets": [
                    "SQL Injection Prevention Cheat Sheet",
                    "Input Validation Cheat Sheet",
                    "Incident Response Cheat Sheet",
                ],
                "focus": "Identify vulnerability class and attack vector used",
            },
            "containment": {
                "primary_risks": ["A07:2021", "A01:2021", "A05:2021"],
                "cheat_sheets": [
                    "Session Management Cheat Sheet",
                    "Authentication Cheat Sheet",
                ],
                "focus": "Invalidate sessions, revoke access, isolate systems",
            },
            "eradication": {
                "primary_risks": ["A03:2021", "A05:2021", "A06:2021", "A04:2021"],
                "cheat_sheets": [
                    "SQL Injection Prevention Cheat Sheet",
                    "Cross Site Scripting Prevention Cheat Sheet",
                    "Input Validation Cheat Sheet",
                    "Docker Security Cheat Sheet",
                ],
                "focus": "Fix vulnerabilities following OWASP guidelines",
            },
            "recovery": {
                "primary_risks": ["A05:2021", "A02:2021", "A08:2021"],
                "cheat_sheets": [
                    "Cryptographic Storage Cheat Sheet",
                    "Transport Layer Security Cheat Sheet",
                ],
                "focus": "Verify security configuration before restoration",
            },
            "post_incident": {
                "primary_risks": ["A09:2021", "A04:2021"],
                "cheat_sheets": [
                    "Logging Cheat Sheet",
                    "Incident Response Cheat Sheet",
                ],
                "focus": "Improve detection and secure design based on lessons",
            },
        }

    def get_risk(self, risk_id: str) -> Optional[OWASPRisk]:
        """Get OWASP Top 10 risk by ID."""
        return self._top_10.get(risk_id)

    def get_all_risks(self) -> List[OWASPRisk]:
        """Get all OWASP Top 10 risks."""
        return list(self._top_10.values())

    def get_risks_list(self) -> List[Dict[str, Any]]:
        """Get all OWASP Top 10 risks as dictionaries."""
        return [
            {
                "id": risk.id,
                "name": risk.name,
                "description": risk.description,
                "cwe_mapped": risk.cwe_mapped,
                "attack_vectors": risk.attack_vectors,
                "impact": risk.impact,
                "prevention": risk.prevention,
                "cheat_sheets": risk.cheat_sheets,
                "detection_indicators": risk.detection_indicators,
                "ir_phase_relevance": risk.ir_phase_relevance,
            }
            for risk in self._top_10.values()
        ]

    def get_cheat_sheet(self, name: str) -> Optional[CheatSheet]:
        """Get a specific cheat sheet by name."""
        return self._cheat_sheets.get(name)

    def get_all_cheat_sheets(self) -> List[CheatSheet]:
        """Get all cheat sheets."""
        return list(self._cheat_sheets.values())

    def get_cheat_sheets_list(self) -> List[Dict[str, Any]]:
        """Get all cheat sheets as dictionaries."""
        return [
            {
                "name": sheet.name,
                "url": sheet.url,
                "category": sheet.category,
                "summary": sheet.summary,
                "key_points": sheet.key_points,
            }
            for sheet in self._cheat_sheets.values()
        ]

    def get_phase_recommendations(self, phase: str) -> Dict[str, Any]:
        """Get OWASP recommendations for an IR phase."""
        mapping = self._phase_mappings.get(phase, {})

        recommendations = {
            "phase": phase,
            "focus": mapping.get("focus", ""),
            "primary_risks": [],
            "cheat_sheets": [],
        }

        for risk_id in mapping.get("primary_risks", []):
            risk = self._top_10.get(risk_id)
            if risk:
                recommendations["primary_risks"].append({
                    "id": risk.id,
                    "name": risk.name,
                    "relevance": risk.ir_phase_relevance.get(phase, ""),
                    "prevention": risk.prevention[:3],
                })

        for sheet_name in mapping.get("cheat_sheets", []):
            sheet = self._cheat_sheets.get(sheet_name)
            if sheet:
                recommendations["cheat_sheets"].append({
                    "name": sheet.name,
                    "url": sheet.url,
                    "key_points": sheet.key_points[:3],
                })

        return recommendations

    def identify_risks_from_indicators(self, indicators: List[str]) -> List[Dict[str, Any]]:
        """
        Identify potential OWASP risks based on incident indicators.

        Args:
            indicators: List of observed indicators (log entries, error messages, etc.)

        Returns:
            List of matching OWASP risks as dictionaries
        """
        matched_risks = []
        indicator_text = " ".join(indicators).lower()

        # Keywords to risk mapping
        keyword_mapping = {
            "A01:2021": ["unauthorized", "access denied", "privilege", "idor", "cors", "jwt", "role", "permission"],
            "A02:2021": ["ssl", "tls", "certificate", "encryption", "hash", "password", "plaintext", "cipher"],
            "A03:2021": ["sql", "injection", "xss", "script", "ldap", "xpath", "command", "shell", "query"],
            "A04:2021": ["business logic", "workflow", "bypass", "fraud", "race condition"],
            "A05:2021": ["default", "misconfigur", "debug", "error message", "stack trace", "directory listing", "xxe"],
            "A06:2021": ["cve-", "outdated", "version", "patch", "vulnerable", "library", "dependency"],
            "A07:2021": ["login fail", "brute force", "credential", "session", "authentication", "mfa", "password"],
            "A08:2021": ["deserializ", "ci/cd", "pipeline", "unsigned", "integrity", "supply chain"],
            "A09:2021": ["log", "monitor", "alert", "audit", "detection"],
            "A10:2021": ["ssrf", "internal", "metadata", "169.254", "localhost", "127.0.0.1"],
        }

        matched_ids = set()
        for risk_id, keywords in keyword_mapping.items():
            for keyword in keywords:
                if keyword in indicator_text and risk_id not in matched_ids:
                    risk = self._top_10.get(risk_id)
                    if risk:
                        matched_ids.add(risk_id)
                        matched_risks.append({
                            "id": risk.id,
                            "name": risk.name,
                            "description": risk.description,
                            "attack_vectors": risk.attack_vectors,
                            "prevention": risk.prevention,
                        })
                    break

        return matched_risks

    def get_remediation_guidance(self, risk_id: str) -> Dict[str, Any]:
        """
        Get comprehensive remediation guidance for a specific OWASP risk.

        Returns prevention steps and relevant cheat sheets.
        """
        risk = self._top_10.get(risk_id)
        if not risk:
            return {}

        cheat_sheets = []
        for sheet_name in risk.cheat_sheets:
            sheet = self._cheat_sheets.get(sheet_name)
            if sheet:
                cheat_sheets.append({
                    "name": sheet.name,
                    "url": sheet.url,
                    "summary": sheet.summary,
                    "key_points": sheet.key_points,
                })

        return {
            "risk_id": risk.id,
            "risk_name": risk.name,
            "description": risk.description,
            "prevention_steps": risk.prevention,
            "cheat_sheets": cheat_sheets,
            "cwe_references": risk.cwe_mapped,
        }

    def validate_phase_compliance(
        self,
        phase: str,
        incident_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate incident response against OWASP best practices.

        Args:
            phase: Current IR phase
            incident_data: Incident details including indicators and actions

        Returns:
            Compliance assessment with recommendations
        """
        phase_recs = self.get_phase_recommendations(phase)

        # Identify risks from incident indicators
        indicators = incident_data.get("indicators", [])
        identified_risks = self.identify_risks_from_indicators(indicators)

        result = {
            "phase": phase,
            "phase_focus": phase_recs.get("focus", ""),
            "identified_risks": identified_risks,
            "recommended_actions": [],
            "cheat_sheets": phase_recs.get("cheat_sheets", []),
        }

        # Add risk-specific recommendations
        for risk in identified_risks:
            result["recommended_actions"].extend([
                f"[{risk['id']}] {action}"
                for action in risk.get("prevention", [])[:2]
            ])

        return result


# Singleton instance
_owasp_integration: Optional[OWASPIntegration] = None


def get_owasp_integration() -> OWASPIntegration:
    """Get the singleton OWASP integration instance."""
    global _owasp_integration
    if _owasp_integration is None:
        _owasp_integration = OWASPIntegration()
    return _owasp_integration
