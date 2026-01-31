import {
  AlertTriangle,
  Bug,
  Shield,
  Building2,
  FileCheck,
  Server,
  Target,
  Link2,
  Bell,
  BarChart3
} from "lucide-react";

const modules = [
  {
    icon: AlertTriangle,
    name: "Incident Response",
    description: "Manage the complete incident lifecycle from detection to lessons learned.",
    color: "bg-red-500/10 text-red-500"
  },
  {
    icon: Shield,
    name: "SOC Operations",
    description: "Centralized alert triage, case management, and investigation workflows.",
    color: "bg-blue-500/10 text-blue-500"
  },
  {
    icon: Bug,
    name: "Vulnerability Management",
    description: "Track, prioritize, and remediate vulnerabilities with NVD integration.",
    color: "bg-orange-500/10 text-orange-500"
  },
  {
    icon: Target,
    name: "Risk Management",
    description: "Identify, assess, and mitigate organizational risks systematically.",
    color: "bg-purple-500/10 text-purple-500"
  },
  {
    icon: Building2,
    name: "Third-Party Risk",
    description: "Evaluate and monitor vendor security posture continuously.",
    color: "bg-cyan-500/10 text-cyan-500"
  },
  {
    icon: FileCheck,
    name: "Compliance",
    description: "Map controls to frameworks and track audit evidence collection.",
    color: "bg-green-500/10 text-green-500"
  },
  {
    icon: Server,
    name: "CMDB",
    description: "Maintain an inventory of assets and their relationships.",
    color: "bg-slate-500/10 text-slate-500"
  },
  {
    icon: Target,
    name: "Threat Intelligence",
    description: "Track threats with MITRE ATT&CK mapping and IOC management.",
    color: "bg-pink-500/10 text-pink-500"
  },
  {
    icon: Link2,
    name: "Integrations",
    description: "Connect with SIEM, SOAR, ticketing, and security tools.",
    color: "bg-indigo-500/10 text-indigo-500"
  },
  {
    icon: BarChart3,
    name: "Reporting",
    description: "Generate executive dashboards and compliance reports.",
    color: "bg-amber-500/10 text-amber-500"
  }
];

export function ModulesSection() {
  return (
    <section id="modules" className="py-20 md:py-32">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Comprehensive Security Modules
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Every tool your security team needs, integrated into one cohesive platform.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {modules.map((module, index) => (
            <div
              key={index}
              className="group p-5 rounded-xl border bg-card hover:border-primary/50 hover:shadow-md transition-all cursor-pointer"
            >
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${module.color}`}>
                <module.icon className="h-5 w-5" />
              </div>
              <h3 className="font-semibold mb-1 group-hover:text-primary transition-colors">
                {module.name}
              </h3>
              <p className="text-sm text-muted-foreground">
                {module.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
