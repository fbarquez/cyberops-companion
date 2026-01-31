# Mobile Responsive Design

Complete mobile-first responsive implementation for CyberOps Companion.

---

## Overview

The platform is fully responsive, adapting to mobile, tablet, and desktop screen sizes with:
- Mobile drawer sidebar (replaces fixed sidebar on small screens)
- Responsive tables with column hiding
- Adaptive forms with single/multi-column layouts
- Touch-friendly dialogs and controls

---

## Breakpoints

| Breakpoint | Pixels | Usage |
|------------|--------|-------|
| Default | < 768px | Mobile (drawer sidebar, stacked layouts, single column) |
| `md:` | >= 768px | Tablet/Desktop (fixed sidebar, two-column forms, tables) |
| `lg:` | >= 1024px | Large desktop (more table columns, wider layouts) |

---

## Components

### Mobile Sidebar

**File:** `components/shared/mobile-sidebar.tsx`

The mobile sidebar uses a Sheet (drawer) component that slides in from the left:

```tsx
import { MobileSidebar } from "@/components/shared/mobile-sidebar";

// In layout
<MobileSidebar open={sidebarOpen} onOpenChange={setSidebarOpen} />
```

**Features:**
- Same navigation items as desktop sidebar
- User info section
- Logout button
- Closes on navigation

### Desktop Sidebar

**File:** `components/shared/sidebar.tsx`

Hidden on mobile, visible on tablet and up:

```tsx
<aside className="hidden md:flex flex-col h-screen w-64 ...">
```

### Header

**File:** `components/shared/header.tsx`

Responsive header with hamburger menu:

```tsx
<header className="h-14 md:h-16 px-4 md:px-6 ...">
  {/* Hamburger - mobile only */}
  <Button className="md:hidden" onClick={toggleMobileSidebar}>
    <Menu className="h-5 w-5" />
  </Button>

  {/* Title - truncates on mobile */}
  <h1 className="text-lg md:text-xl font-semibold truncate">
    {title}
  </h1>

  {/* Language switcher - icon only on mobile */}
  <span className="hidden md:inline">{language}</span>
</header>
```

### Responsive Table

**File:** `components/shared/responsive-table.tsx`

Adaptive table that hides columns on smaller screens:

```tsx
import { ResponsiveTable, ScrollableTable } from "@/components/shared/responsive-table";

// Option 1: Use ResponsiveTable with breakpoint props
<ResponsiveTable
  headers={[
    { key: "name", label: "Name" },
    { key: "email", label: "Email", hideOnMobile: true },
    { key: "role", label: "Role", hideOnTablet: true },
    { key: "actions", label: "" },
  ]}
  data={users}
  renderRow={(user) => (
    <TableRow>
      <TableCell>{user.name}</TableCell>
      <TableCell className="hidden md:table-cell">{user.email}</TableCell>
      <TableCell className="hidden lg:table-cell">{user.role}</TableCell>
      <TableCell>...</TableCell>
    </TableRow>
  )}
/>

// Option 2: Manual column hiding
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Name</TableHead>
      <TableHead className="hidden md:table-cell">Email</TableHead>
      <TableHead className="hidden lg:table-cell">Created</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow>
      <TableCell>John Doe</TableCell>
      <TableCell className="hidden md:table-cell">john@example.com</TableCell>
      <TableCell className="hidden lg:table-cell">2026-01-31</TableCell>
    </TableRow>
  </TableBody>
</Table>
```

### Scrollable Table Wrapper

For tables with many columns, wrap with horizontal scroll:

```tsx
<ScrollableTable>
  <Table>...</Table>
</ScrollableTable>

// Or manually
<div className="overflow-x-auto -mx-4 md:mx-0">
  <div className="inline-block min-w-full align-middle">
    <Table>...</Table>
  </div>
</div>
```

### Mobile Card Row

Helper for displaying data as cards on mobile:

```tsx
import { MobileCardRow, MobileCardHeader } from "@/components/shared/responsive-table";

// On mobile, show as card instead of table row
<div className="md:hidden">
  <MobileCardHeader>
    <Badge>{status}</Badge>
    <span>{date}</span>
  </MobileCardHeader>
  <MobileCardRow label="Name" value={name} />
  <MobileCardRow label="Email" value={email} />
  <MobileCardRow label="Role" value={role} />
</div>
```

---

## Responsive Patterns

### Forms

Single column on mobile, two columns on tablet+:

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
  <FormField label="Name" ... />
  <FormField label="Email" ... />
  <FormField label="Phone" ... />
  <FormField label="Role" ... />
</div>

// Full width fields
<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
  <div className="md:col-span-2">
    <FormField label="Description" ... />
  </div>
</div>
```

### Dialogs

Responsive width and scrolling:

```tsx
<DialogContent className="w-[95vw] max-w-lg max-h-[90vh] overflow-y-auto">
  ...
</DialogContent>

// Size presets (from FormDialog)
// sm: max-w-sm
// md: max-w-md (default)
// lg: max-w-lg
// xl: max-w-xl
// full: max-w-4xl
```

### Filter Bars

Stack on mobile, inline on desktop:

```tsx
<div className="flex flex-col md:flex-row gap-4">
  <Input placeholder="Search..." className="w-full md:w-64" />
  <Select>...</Select>
  <Select>...</Select>
  <Button>Filter</Button>
</div>
```

### Stats Cards

Responsive grid:

```tsx
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
  <StatCard title="Total" value={100} />
  <StatCard title="Active" value={80} />
  <StatCard title="Pending" value={15} />
  <StatCard title="Closed" value={5} />
</div>
```

### Tabs

Scrollable on mobile:

```tsx
<Tabs>
  <TabsList className="w-full overflow-x-auto flex-nowrap">
    <TabsTrigger value="tab1" className="flex-shrink-0">Tab 1</TabsTrigger>
    <TabsTrigger value="tab2" className="flex-shrink-0">Tab 2</TabsTrigger>
    <TabsTrigger value="tab3" className="flex-shrink-0">Tab 3</TabsTrigger>
  </TabsList>
</Tabs>
```

### Buttons

Icon-only on mobile, with text on desktop:

```tsx
<Button>
  <Plus className="h-4 w-4" />
  <span className="hidden md:inline ml-2">Add Item</span>
</Button>

// Or use sr-only for accessibility
<Button>
  <Plus className="h-4 w-4" />
  <span className="sr-only md:not-sr-only md:ml-2">Add Item</span>
</Button>
```

---

## Page-Specific Implementations

### Dashboard Layout

```tsx
// app/(dashboard)/layout.tsx
<div className="flex h-screen">
  {/* Desktop sidebar - hidden on mobile */}
  <Sidebar />

  {/* Mobile sidebar drawer */}
  <MobileSidebar open={mobileOpen} onOpenChange={setMobileOpen} />

  <div className="flex-1 flex flex-col">
    <Header onMenuClick={() => setMobileOpen(true)} />
    <main className="flex-1 overflow-auto p-4 md:p-6">
      {children}
    </main>
  </div>
</div>
```

### Incidents Page

```tsx
// Responsive filters
<div className="flex flex-col md:flex-row gap-4 mb-6">
  <Input placeholder="Search..." className="w-full md:w-64" />
  <Select>...</Select>
</div>

// Table with hidden columns
<TableHead className="hidden md:table-cell">Assignee</TableHead>
<TableHead className="hidden lg:table-cell">Created</TableHead>
```

### SOC Page

```tsx
// Tabs scroll horizontally on mobile
<TabsList className="overflow-x-auto">
  <TabsTrigger>Dashboard</TabsTrigger>
  <TabsTrigger>Alerts</TabsTrigger>
  <TabsTrigger>Cases</TabsTrigger>
  <TabsTrigger>Playbooks</TabsTrigger>
</TabsList>

// Stats grid adapts
<div className="grid grid-cols-2 md:grid-cols-4 gap-4">
  ...
</div>
```

### Risks Page

```tsx
// Form uses responsive grid
<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
  <FormField label="Title" />
  <FormField label="Category" />
  <FormField label="Likelihood" />
  <FormField label="Impact" />
  <div className="md:col-span-2">
    <FormField label="Description" />
  </div>
</div>
```

---

## Chart Responsiveness

### ChartCard

```tsx
// components/dashboard/widgets/ChartCard.tsx
<div className={cn(
  "h-48 md:h-64 lg:h-72",  // Responsive height
  className
)}>
  {children}
</div>
```

### Hiding Charts on Mobile

For complex charts that don't work well on mobile:

```tsx
<div className="hidden md:block">
  <RiskHeatMap data={data} />
</div>
<div className="md:hidden">
  <p className="text-muted-foreground text-center py-8">
    View on larger screen for risk matrix
  </p>
</div>
```

---

## Testing Responsive Design

### Browser DevTools

1. Open Chrome/Firefox DevTools (F12)
2. Toggle Device Toolbar (Ctrl+Shift+M)
3. Select device preset or set custom dimensions

### Key Widths to Test

| Width | Device |
|-------|--------|
| 375px | iPhone SE |
| 414px | iPhone 14 |
| 768px | iPad Mini (breakpoint) |
| 1024px | iPad Pro / Small laptop |
| 1440px | Desktop |

### Checklist

- [ ] Sidebar collapses to drawer on mobile
- [ ] Hamburger menu visible and functional
- [ ] Tables scroll horizontally or hide columns
- [ ] Forms stack to single column
- [ ] Dialogs fit within viewport
- [ ] Buttons show icons only on mobile
- [ ] Text doesn't overflow
- [ ] Touch targets are at least 44x44px

---

## Files Modified

| File | Changes |
|------|---------|
| `components/ui/sheet.tsx` | Added Sheet component from shadcn/ui |
| `components/shared/mobile-sidebar.tsx` | New mobile drawer sidebar |
| `components/shared/responsive-table.tsx` | New responsive table helpers |
| `components/shared/sidebar.tsx` | Added `hidden md:flex` |
| `components/shared/header.tsx` | Hamburger menu, responsive sizing |
| `components/ui/dialog.tsx` | Responsive width, overflow |
| `components/dashboard/widgets/ChartCard.tsx` | Responsive heights |
| `app/(dashboard)/layout.tsx` | Integrated mobile sidebar |
| `app/(dashboard)/risks/page.tsx` | Responsive forms |
| `app/(dashboard)/soc/page.tsx` | Responsive tabs, tables |
| `app/(dashboard)/incidents/page.tsx` | Responsive filters, tables |

---

## Tailwind Classes Reference

### Visibility

```css
hidden          /* display: none */
md:block        /* display: block at md+ */
md:hidden       /* display: none at md+ */
md:flex         /* display: flex at md+ */
md:table-cell   /* display: table-cell at md+ */
```

### Grid

```css
grid-cols-1           /* 1 column */
md:grid-cols-2        /* 2 columns at md+ */
lg:grid-cols-4        /* 4 columns at lg+ */
md:col-span-2         /* Span 2 columns at md+ */
```

### Flex

```css
flex-col              /* Column direction */
md:flex-row           /* Row direction at md+ */
flex-wrap             /* Allow wrapping */
flex-shrink-0         /* Don't shrink */
```

### Spacing

```css
p-4 md:p-6            /* Padding 16px, 24px at md+ */
gap-4                 /* Gap 16px */
-mx-4 md:mx-0         /* Negative margin mobile, none at md+ */
```

### Sizing

```css
w-full md:w-64        /* Full width, 256px at md+ */
h-14 md:h-16          /* Height 56px, 64px at md+ */
max-w-lg              /* Max width large */
max-h-[90vh]          /* Max height 90% viewport */
```

### Text

```css
text-sm md:text-base  /* Small text, base at md+ */
truncate              /* Truncate with ellipsis */
whitespace-nowrap     /* No wrapping */
```

### Overflow

```css
overflow-x-auto       /* Horizontal scroll */
overflow-y-auto       /* Vertical scroll */
overflow-hidden       /* Hide overflow */
```

---

## Accessibility Notes

1. **Touch Targets**: Minimum 44x44px for buttons and links
2. **Focus States**: Visible focus rings for keyboard navigation
3. **Screen Readers**: Use `sr-only` for icon-only buttons
4. **Zoom**: Layout works at 200% zoom
5. **Orientation**: Works in portrait and landscape

---

## Best Practices

1. **Mobile-first**: Start with mobile styles, add `md:` for larger screens
2. **Progressive Enhancement**: Core functionality works on all sizes
3. **Test Often**: Check responsive behavior during development
4. **Avoid Fixed Widths**: Use `max-w-*` and percentages
5. **Consider Touch**: Larger tap targets, no hover-only interactions
6. **Performance**: Lazy load heavy components on mobile
