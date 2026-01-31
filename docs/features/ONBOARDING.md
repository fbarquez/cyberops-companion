# Onboarding Flow

The onboarding flow guides new users through initial setup after registration, ensuring they configure their workspace and understand the platform.

## Overview

A 5-step wizard that collects:
1. Welcome introduction
2. Organization profile
3. Module selection
4. Feature tour
5. Completion with quick actions

## Architecture

### Files Structure
```
apps/web/
├── app/onboarding/page.tsx              # Main onboarding page
├── stores/onboarding-store.ts           # Zustand state management
└── components/onboarding/
    ├── index.ts                         # Barrel export
    ├── welcome-step.tsx                 # Step 1: Welcome
    ├── organization-step.tsx            # Step 2: Organization
    ├── modules-step.tsx                 # Step 3: Modules
    ├── tour-step.tsx                    # Step 4: Tour
    └── complete-step.tsx                # Step 5: Complete
```

### State Management

Uses Zustand with persist middleware for state persistence:

```typescript
interface OnboardingData {
  organizationName: string;
  organizationSize: string;
  industry: string;
  jobTitle: string;
  selectedModules: string[];
  completedAt: string | null;
}

interface OnboardingStore {
  currentStep: number;
  isComplete: boolean;
  data: OnboardingData;

  // Actions
  nextStep: () => void;
  prevStep: () => void;
  setData: (data: Partial<OnboardingData>) => void;
  completeOnboarding: () => void;
  resetOnboarding: () => void;
}
```

### Persistence

State is persisted to `localStorage` under key `cyberops-onboarding`:
- Users can close browser and resume later
- Data survives page refreshes
- Only cleared on explicit reset or completion

## Steps Detail

### Step 1: Welcome

**Component:** `WelcomeStep`

Content:
- Welcome message with user's name (if available)
- Overview of what onboarding covers
- 4 steps preview with icons
- Single "Get Started" button

### Step 2: Organization Profile

**Component:** `OrganizationStep`

Fields collected:
| Field | Type | Options/Validation |
|-------|------|-------------------|
| Organization Name | Input | Required, min 2 chars |
| Organization Size | Select | 1-10, 11-50, 51-200, 201-1000, 1000+ |
| Industry | Select | Financial, Healthcare, Technology, Government, Retail, Manufacturing, Other |
| Job Title | Input | Optional |

### Step 3: Module Selection

**Component:** `ModulesStep`

Available modules:
1. Incident Management (recommended)
2. SOC Module (recommended)
3. Vulnerability Management (recommended)
4. Risk Management
5. TPRM
6. Compliance
7. CMDB
8. Threat Intelligence
9. Integrations
10. Reporting

Features:
- Multi-select with checkboxes
- "Recommended" badges on key modules
- Module descriptions
- At least 1 module required

### Step 4: Feature Tour

**Component:** `TourStep`

Carousel-style tour showing:
1. Dashboard overview
2. Incident management workflow
3. Real-time alerts
4. Reporting capabilities

Features:
- Auto-advance option (disabled by default)
- Manual navigation (prev/next)
- Progress dots
- Skip button

### Step 5: Complete

**Component:** `CompleteStep`

Content:
- Success message with checkmark
- Summary of configuration
- Quick start actions:
  - Create first incident
  - Import vulnerabilities
  - Set up integrations
  - Invite team members
- "Go to Dashboard" button

## User Flow

### Registration Flow
```
Register → Onboarding → Dashboard
         ↓
    (if incomplete)
         ↓
    Resume from last step
```

### Dashboard Protection
```
Dashboard Access
      ↓
   Authenticated?
      ↓ No
   → Login
      ↓ Yes
   Onboarding complete?
      ↓ No
   → Onboarding
      ↓ Yes
   → Dashboard
```

## Integration Points

### Auth Store Integration

The onboarding checks authentication status:
```typescript
const { isAuthenticated, isLoading } = useAuthStore();

useEffect(() => {
  if (!isLoading && !isAuthenticated) {
    router.push("/login");
  }
}, [isAuthenticated, isLoading, router]);
```

### Dashboard Layout Integration

Dashboard layout checks onboarding completion:
```typescript
const { isComplete: isOnboardingComplete } = useOnboardingStore();

useEffect(() => {
  if (!isLoading && isAuthenticated && !isOnboardingComplete) {
    router.push("/onboarding");
  }
}, [isAuthenticated, isLoading, isOnboardingComplete, router]);
```

## Customization

### Adding a New Step

1. Create component in `components/onboarding/`:
```tsx
export function NewStep({ onNext, onBack }: StepProps) {
  return (
    <div>
      {/* Step content */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>Back</Button>
        <Button onClick={onNext}>Continue</Button>
      </div>
    </div>
  );
}
```

2. Export from `index.ts`:
```typescript
export { NewStep } from "./new-step";
```

3. Update `app/onboarding/page.tsx`:
```typescript
const TOTAL_STEPS = 6; // Increment

// Add step rendering
{currentStep === 5 && <NewStep onNext={nextStep} onBack={prevStep} />}
```

### Modifying Organization Options

Edit `organization-step.tsx`:
```typescript
const industries = [
  { value: "financial", label: "Financial Services" },
  { value: "healthcare", label: "Healthcare" },
  // Add more...
];

const sizes = [
  { value: "1-10", label: "1-10 employees" },
  // Add more...
];
```

### Changing Module Recommendations

Edit `modules-step.tsx`:
```typescript
const modules = [
  {
    id: "incidents",
    name: "Incident Management",
    recommended: true,  // Toggle this
    // ...
  },
];
```

## API Integration (Future)

Currently, onboarding data is stored client-side only. Future enhancement:

```typescript
// POST /api/v1/users/onboarding
{
  organization: {
    name: string;
    size: string;
    industry: string;
  },
  preferences: {
    modules: string[];
  }
}
```

## Accessibility

- All form fields have proper labels
- Keyboard navigation supported
- Focus management between steps
- Screen reader announcements for step changes
- Color contrast meets WCAG 2.1 AA

## Testing Checklist

- [ ] Complete flow end-to-end
- [ ] Refresh mid-flow (should resume)
- [ ] Close browser, reopen (should resume)
- [ ] Skip optional fields
- [ ] Select no modules (should show error)
- [ ] Complete and verify dashboard access
- [ ] Reset and verify flow restarts
