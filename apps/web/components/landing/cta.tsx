import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

export function CTASection() {
  return (
    <section className="py-20 md:py-32 bg-primary text-primary-foreground">
      <div className="container mx-auto px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Ready to transform your security operations?
          </h2>
          <p className="text-xl opacity-90 mb-8">
            Join security teams who trust ISORA to protect their organizations.
            Start your free trial today.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              size="lg"
              variant="secondary"
              asChild
              className="text-lg px-8"
            >
              <Link href="/register">
                Start Free Trial
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
            <Button
              size="lg"
              variant="outline"
              asChild
              className="text-lg px-8 bg-transparent border-primary-foreground/30 hover:bg-primary-foreground/10"
            >
              <Link href="/login">
                Sign In
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
