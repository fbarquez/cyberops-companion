import {
  LandingNavbar,
  HeroSection,
  FeaturesSection,
  ModulesSection,
  CTASection,
  Footer
} from "@/components/landing";

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <LandingNavbar />
      <main>
        <HeroSection />
        <FeaturesSection />
        <ModulesSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}
