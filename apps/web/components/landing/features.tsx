import {
  Link2,
  Shield,
  FileCheck,
  Scale,
  Building2,
  Sparkles
} from "lucide-react";

const features = [
  {
    icon: Link2,
    title: "ISMS ↔ SOC Bridge",
    description: "Automatische Verknüpfung operativer Aktivitäten mit Compliance-Kontrollen. Incidents, Alerts und Scans erzeugen Nachweise."
  },
  {
    icon: Scale,
    title: "NIS2 & DORA Ready",
    description: "Geführte Wizards für NIS2-Einstufung und DORA-Assessment. Gap-Analyse und Maßnahmenplanung inklusive."
  },
  {
    icon: Shield,
    title: "BSI IT-Grundschutz",
    description: "Vollständiges Baustein-Mapping und Schutzbedarfsfeststellung nach BSI-Methodik 200-2."
  },
  {
    icon: FileCheck,
    title: "Nachweisführung",
    description: "Evidenz-Management mit SHA-256 Integrität, Versionierung und Kontrollen-Zuordnung für Audits."
  },
  {
    icon: Building2,
    title: "Multi-Tenancy",
    description: "Mandantenfähig ab Community Edition. Ideal für Berater und MSSPs mit mehreren Kunden."
  },
  {
    icon: Sparkles,
    title: "AI Copilot",
    description: "KI-Unterstützung für Risikoanalyse und Dokumentation. Multi-LLM mit Ollama-Option für lokale Nutzung."
  }
];

export function FeaturesSection() {
  return (
    <section id="features" className="py-20 md:py-32 bg-muted/30">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Compliance trifft Operations
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            ISORA verbindet ISMS-Dokumentation mit operativem Sicherheitsbetrieb —
            für nachvollziehbare Kontrollwirksamkeit.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-card p-6 rounded-xl border hover:shadow-lg transition-shadow"
            >
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <feature.icon className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
              <p className="text-muted-foreground">{feature.description}</p>
            </div>
          ))}
        </div>

        {/* ISMS ↔ SOC Bridge Diagram */}
        <div className="mt-16 max-w-4xl mx-auto">
          <div className="bg-card border rounded-xl p-8">
            <h3 className="text-xl font-semibold mb-6 text-center">So funktioniert die Evidence Bridge</h3>
            <div className="grid md:grid-cols-3 gap-4 text-center">
              <div className="p-4 bg-blue-500/10 rounded-lg">
                <div className="text-2xl mb-2">🔧</div>
                <div className="font-medium text-blue-700 dark:text-blue-300">Operative Aktivität</div>
                <div className="text-sm text-muted-foreground mt-1">Incident abgeschlossen</div>
              </div>
              <div className="p-4 bg-primary/10 rounded-lg flex flex-col justify-center">
                <div className="text-2xl mb-2">→</div>
                <div className="font-medium text-primary">Automatisch verknüpft</div>
                <div className="text-sm text-muted-foreground mt-1">A.5.24 Incident Management</div>
              </div>
              <div className="p-4 bg-green-500/10 rounded-lg">
                <div className="text-2xl mb-2">✓</div>
                <div className="font-medium text-green-700 dark:text-green-300">Nachweis dokumentiert</div>
                <div className="text-sm text-muted-foreground mt-1">Reaktionszeit, Lösungsweg</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
