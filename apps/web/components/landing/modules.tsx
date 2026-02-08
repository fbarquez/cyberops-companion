import {
  AlertTriangle,
  Bug,
  Shield,
  Building2,
  FileCheck,
  Server,
  Target,
  Link2,
  Scale,
  BarChart3
} from "lucide-react";

const modules = [
  {
    icon: AlertTriangle,
    name: "Incident Management",
    description: "6-Phasen-Workflow nach NIST mit automatischer Nachweisverknüpfung zu A.5.24.",
    color: "bg-red-500/10 text-red-500"
  },
  {
    icon: Shield,
    name: "SOC-Modul",
    description: "Alert-Triage, Case Management und Playbooks — verknüpft mit A.8.16.",
    color: "bg-blue-500/10 text-blue-500"
  },
  {
    icon: Bug,
    name: "Vulnerability Management",
    description: "CVE-Tracking mit NVD/EPSS/KEV-Integration und Nachweis für A.8.8.",
    color: "bg-orange-500/10 text-orange-500"
  },
  {
    icon: Target,
    name: "Risikomanagement",
    description: "Risikoregister, Behandlungspläne und Heatmaps nach ISO 27005.",
    color: "bg-purple-500/10 text-purple-500"
  },
  {
    icon: Building2,
    name: "Lieferanten (TPRM)",
    description: "Lieferantenbewertung und Fragebögen für NIS2 Art. 21 Abs. 2d.",
    color: "bg-cyan-500/10 text-cyan-500"
  },
  {
    icon: Scale,
    name: "Compliance Hub",
    description: "ISO 27001, NIS2, DORA und BSI IT-Grundschutz in einer Oberfläche.",
    color: "bg-green-500/10 text-green-500"
  },
  {
    icon: Server,
    name: "CMDB",
    description: "Asset-Inventar mit Abhängigkeiten und Schutzbedarfsfeststellung.",
    color: "bg-slate-500/10 text-slate-500"
  },
  {
    icon: Target,
    name: "Threat Intelligence",
    description: "IOC-Verwaltung und MITRE ATT&CK Mapping für Bedrohungsanalyse.",
    color: "bg-pink-500/10 text-pink-500"
  },
  {
    icon: Link2,
    name: "Integrationen",
    description: "API und Webhooks für SIEM, Scanner und Ticketing-Systeme.",
    color: "bg-indigo-500/10 text-indigo-500"
  },
  {
    icon: BarChart3,
    name: "Dashboards",
    description: "Kontrollwirksamkeit, Gap-Status und Compliance-Übersichten.",
    color: "bg-amber-500/10 text-amber-500"
  }
];

export function ModulesSection() {
  return (
    <section id="modules" className="py-20 md:py-32">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Operative Module mit Compliance-Verknüpfung
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Jede operative Aktivität erzeugt automatisch Nachweise für Ihre ISMS-Kontrollen.
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
