import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Shield,
  ArrowRight,
  CheckCircle2,
  Github,
  Scale
} from "lucide-react";

export function HeroSection() {
  return (
    <section className="relative pt-32 pb-20 md:pt-40 md:pb-32 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-secondary/10 -z-10" />
      <div className="absolute top-20 left-10 w-72 h-72 bg-primary/10 rounded-full blur-3xl -z-10" />
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-secondary/10 rounded-full blur-3xl -z-10" />

      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto text-center">
          {/* Badges */}
          <div className="flex flex-wrap justify-center gap-2 mb-8">
            <Badge variant="outline" className="px-3 py-1 text-sm">
              <Github className="h-3.5 w-3.5 mr-1.5" />
              Open Source (AGPL-3.0)
            </Badge>
            <Badge variant="outline" className="px-3 py-1 text-sm">
              <Scale className="h-3.5 w-3.5 mr-1.5" />
              NIS2 &bull; DORA &bull; BSI
            </Badge>
          </div>

          {/* Headline */}
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
            ISMS-Anforderungen in{" "}
            <span className="text-primary">überprüfbare Nachweise</span>
          </h1>

          {/* Subheadline */}
          <p className="text-xl text-muted-foreground mb-4 max-w-2xl mx-auto">
            ISORA verbindet operative Sicherheitsaktivitäten automatisch mit Compliance-Kontrollen.
            Für regulierte Unternehmen im DACH-Raum.
          </p>

          {/* Key differentiator */}
          <p className="text-lg text-primary font-medium mb-8">
            ISMS ↔ SOC Bridge: Incident → A.5.24 → Nachweis dokumentiert
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Button size="lg" asChild className="text-lg px-8">
              <Link href="/register">
                Kostenlos starten
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild className="text-lg px-8">
              <Link href="https://github.com/fbarquez/cyberops-companion" target="_blank">
                <Github className="mr-2 h-5 w-5" />
                GitHub
              </Link>
            </Button>
          </div>

          {/* Trust indicators */}
          <div className="flex flex-wrap justify-center gap-6 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              <span>Community Edition kostenlos</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              <span>Self-Hosted / DSGVO-konform</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              <span>Multi-Tenancy für Berater</span>
            </div>
          </div>
        </div>

        {/* Dashboard Preview */}
        <div className="mt-16 relative">
          <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent z-10 pointer-events-none" />
          <div className="bg-card border rounded-xl shadow-2xl overflow-hidden mx-auto max-w-5xl">
            <div className="bg-muted/50 px-4 py-3 border-b flex items-center gap-2">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <div className="w-3 h-3 rounded-full bg-green-500" />
              </div>
              <div className="flex-1 text-center text-sm text-muted-foreground">
                ISORA — Compliance Hub
              </div>
            </div>
            <div className="p-6 bg-gradient-to-br from-muted/30 to-muted/10">
              {/* Mock dashboard content */}
              <div className="grid grid-cols-4 gap-4 mb-6">
                {[
                  { label: "Kontrollwirksamkeit", value: "87%", color: "text-green-500" },
                  { label: "Verknüpfte Nachweise", value: "234", color: "text-blue-500" },
                  { label: "NIS2-Abdeckung", value: "72%", color: "text-orange-500" },
                  { label: "Offene Gaps", value: "12", color: "text-red-500" },
                ].map((stat, i) => (
                  <div key={i} className="bg-card rounded-lg p-4 border">
                    <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
                    <div className="text-sm text-muted-foreground">{stat.label}</div>
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="col-span-2 bg-card rounded-lg p-4 border h-32" />
                <div className="bg-card rounded-lg p-4 border h-32" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
