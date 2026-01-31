import {
  Zap,
  Shield,
  BarChart3,
  Users,
  Lock,
  Globe
} from "lucide-react";

const features = [
  {
    icon: Zap,
    title: "Real-time Response",
    description: "Respond to security incidents in real-time with automated workflows and intelligent alerting."
  },
  {
    icon: Shield,
    title: "Unified Platform",
    description: "Consolidate your security operations into a single platform for better visibility and control."
  },
  {
    icon: BarChart3,
    title: "Advanced Analytics",
    description: "Gain insights from your security data with comprehensive reporting and trend analysis."
  },
  {
    icon: Users,
    title: "Team Collaboration",
    description: "Enable seamless collaboration between security teams with built-in communication tools."
  },
  {
    icon: Lock,
    title: "Compliance Ready",
    description: "Meet regulatory requirements with pre-built frameworks for NIST, ISO 27001, SOC 2, and more."
  },
  {
    icon: Globe,
    title: "Third-Party Risk",
    description: "Manage vendor risks effectively with automated assessments and continuous monitoring."
  }
];

export function FeaturesSection() {
  return (
    <section id="features" className="py-20 md:py-32 bg-muted/30">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Everything you need for security operations
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            A comprehensive suite of tools designed to help security teams work smarter, not harder.
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
      </div>
    </section>
  );
}
