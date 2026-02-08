import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, Github } from "lucide-react";

export function CTASection() {
  return (
    <section className="py-20 md:py-32 bg-primary text-primary-foreground">
      <div className="container mx-auto px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Bereit für nachvollziehbare Compliance?
          </h2>
          <p className="text-xl opacity-90 mb-8">
            Community Edition kostenlos. Self-Hosted. DSGVO-konform.
            Multi-Tenancy für Berater und MSSPs inklusive.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              size="lg"
              variant="secondary"
              asChild
              className="text-lg px-8"
            >
              <Link href="/register">
                Kostenlos starten
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
            <Button
              size="lg"
              variant="outline"
              asChild
              className="text-lg px-8 bg-transparent border-primary-foreground/30 hover:bg-primary-foreground/10"
            >
              <Link href="https://github.com/fbarquez/cyberops-companion" target="_blank">
                <Github className="mr-2 h-5 w-5" />
                GitHub
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
