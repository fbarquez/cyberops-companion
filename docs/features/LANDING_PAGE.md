# Landing Page

The landing page is the public-facing entry point for unauthenticated users visiting CyberOps Companion.

## Overview

The landing page provides:
- Professional introduction to the platform
- Feature highlights and module showcase
- Clear call-to-action for registration/login
- Responsive design for all devices

## Components

### Location
```
apps/web/
├── app/page.tsx                    # Landing page route
└── components/landing/
    ├── index.ts                    # Barrel export
    ├── navbar.tsx                  # Navigation bar
    ├── hero.tsx                    # Hero section
    ├── features.tsx                # Features grid
    ├── modules.tsx                 # Modules showcase
    ├── cta.tsx                     # Call-to-action
    └── footer.tsx                  # Footer
```

### Component Details

#### LandingNavbar
Responsive navigation with:
- Logo and brand name
- Navigation links (Features, Modules, Pricing)
- Auth buttons (Login, Get Started)
- Mobile hamburger menu

#### HeroSection
Main hero area with:
- Headline and value proposition
- Primary and secondary CTAs
- Dashboard preview image placeholder
- Gradient background effects

#### FeaturesSection
6-card grid showcasing key capabilities:
1. **Incident Response** - NIST-aligned incident lifecycle
2. **SOC Operations** - Alert triage and case management
3. **Vulnerability Management** - CVE tracking and scanning
4. **Risk Management** - Risk register and assessments
5. **Compliance** - Multi-framework support
6. **Threat Intelligence** - IOC management and MITRE ATT&CK

#### ModulesSection
10 security modules displayed in a grid:
- Incident Management
- SOC Module
- Vulnerabilities
- Risk Management
- TPRM
- Compliance
- CMDB
- Threat Intelligence
- Integrations
- Reporting

#### CTASection
Final call-to-action with:
- Compelling headline
- Feature highlights (Free trial, No credit card, etc.)
- Registration button

#### Footer
Standard footer with:
- Logo and tagline
- Navigation links by category (Product, Company, Resources, Legal)
- Social media links
- Copyright notice

## Styling

### Theme Support
- Full dark mode support
- Uses Tailwind CSS and Shadcn/ui components
- Consistent with dashboard theme

### Responsive Breakpoints
```
Mobile:  < 640px  (sm)
Tablet:  640-1024px (md)
Desktop: > 1024px (lg)
```

### Key CSS Classes
```css
/* Hero gradient background */
bg-gradient-to-br from-background via-background to-primary/5

/* Card hover effects */
hover:shadow-lg transition-all duration-300

/* Responsive grid */
grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8
```

## Routing

### Unauthenticated Users
- Visit `/` → See landing page
- Click "Get Started" → Go to `/register`
- Click "Login" → Go to `/login`

### Authenticated Users
- Can still visit landing page
- Shows "Dashboard" button instead of "Get Started"

## Customization

### Adding New Features
Edit `components/landing/features.tsx`:
```tsx
const features = [
  {
    icon: Shield,
    title: "Feature Name",
    description: "Feature description...",
  },
  // Add more features...
];
```

### Adding New Modules
Edit `components/landing/modules.tsx`:
```tsx
const modules = [
  {
    icon: AlertTriangle,
    name: "Module Name",
    description: "Module description...",
    href: "/module-path",
  },
  // Add more modules...
];
```

### Changing Hero Content
Edit `components/landing/hero.tsx` to modify:
- Headlines and subheadlines
- CTA button text and links
- Dashboard preview image

## Performance

### Optimizations
- Components use `"use client"` only where needed
- Icons loaded from lucide-react (tree-shakeable)
- No external API calls on landing page
- Images use Next.js Image component (when added)

### Lighthouse Targets
- Performance: 90+
- Accessibility: 100
- Best Practices: 100
- SEO: 100

## Future Enhancements

- [ ] Add actual dashboard screenshot
- [ ] Testimonials section
- [ ] Pricing comparison table
- [ ] Video demo embed
- [ ] Blog/resources section
- [ ] Trust badges (certifications, compliance)
- [ ] Live demo button
