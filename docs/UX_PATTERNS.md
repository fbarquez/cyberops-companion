# UX Patterns Guide

This document defines the standard UX patterns used throughout CyberOps Companion. Follow these patterns to maintain consistency across all modules.

---

## Table of Contents

1. [Buttons](#buttons)
2. [Forms](#forms)
3. [Dialogs](#dialogs)
4. [Tables](#tables)
5. [Loading States](#loading-states)
6. [Empty States](#empty-states)
7. [Error Handling](#error-handling)
8. [Page Layouts](#page-layouts)
9. [Icons](#icons)

---

## Buttons

### Button Variants

| Variant | Usage | Example |
|---------|-------|---------|
| `default` | Primary actions | Create, Save, Submit |
| `destructive` | Dangerous actions | Delete, Remove |
| `outline` | Secondary actions | Cancel, Import, Export |
| `secondary` | Tertiary actions | Less important actions |
| `ghost` | Minimal actions | Icon buttons, table actions |
| `link` | Navigation | Links within text |

### Button Sizes

| Size | Usage |
|------|-------|
| `default` | Standard buttons |
| `sm` | Table actions, compact areas |
| `lg` | Hero CTAs, important actions |
| `icon` | Icon-only buttons |

### Loading States

Always use `LoadingButton` for form submissions:

```tsx
import { LoadingButton } from "@/components/shared";

<LoadingButton
  isLoading={isPending}
  loadingText="Creating..."
  icon={<Plus className="h-4 w-4" />}
>
  Create Item
</LoadingButton>
```

### Button Patterns

```tsx
// Primary action with icon
<Button>
  <Plus className="h-4 w-4 mr-2" />
  Add Item
</Button>

// Secondary action
<Button variant="outline">
  <Download className="h-4 w-4 mr-2" />
  Export
</Button>

// Destructive action (in dropdowns)
<DropdownMenuItem className="text-destructive">
  <Trash className="h-4 w-4 mr-2" />
  Delete
</DropdownMenuItem>

// Icon-only button
<Button variant="ghost" size="icon">
  <MoreHorizontal className="h-4 w-4" />
</Button>
```

---

## Forms

### Form Field Component

Use `FormField` for consistent form fields:

```tsx
import { FormField } from "@/components/shared";

// Input field
<FormField
  label="Email"
  type="input"
  placeholder="user@example.com"
  error={errors.email?.message}
  required
  {...register("email")}
/>

// Textarea field
<FormField
  type="textarea"
  label="Description"
  rows={4}
  error={errors.description?.message}
  {...register("description")}
/>

// Select field
<FormField
  type="select"
  label="Status"
  value={status}
  onValueChange={setStatus}
  options={[
    { value: "active", label: "Active" },
    { value: "inactive", label: "Inactive" },
  ]}
/>
```

### Form Layout

```tsx
// Standard form structure
<form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
  {/* Single column fields */}
  <FormField label="Name" {...register("name")} />

  {/* Two column layout */}
  <div className="grid grid-cols-2 gap-4">
    <FormField label="First Name" {...register("firstName")} />
    <FormField label="Last Name" {...register("lastName")} />
  </div>

  {/* Full width textarea */}
  <FormField type="textarea" label="Description" {...register("description")} />

  {/* Form actions */}
  <div className="flex justify-end gap-2">
    <Button type="button" variant="outline" onClick={onCancel}>
      Cancel
    </Button>
    <LoadingButton type="submit" isLoading={isPending}>
      Save
    </LoadingButton>
  </div>
</form>
```

### Validation

- Show errors below fields in red (`text-destructive`)
- Mark required fields with red asterisk
- Validate on blur for immediate feedback
- Disable submit button only when form is invalid

---

## Dialogs

### Dialog Sizes

| Size | Max Width | Use Case |
|------|-----------|----------|
| `sm` | 384px | Simple confirmations, single input |
| `md` | 448px | Standard forms (3-5 fields) |
| `lg` | 512px | Medium forms (5-8 fields) |
| `xl` | 672px | Large forms, scrollable content |
| `full` | 896px | Complex forms, data tables |

### Form Dialog

Use `FormDialog` for consistent dialog forms:

```tsx
import { FormDialog } from "@/components/shared";

<FormDialog
  open={isOpen}
  onOpenChange={setIsOpen}
  title="Add New Item"
  description="Fill in the details to create a new item."
  size="lg"
  isLoading={isPending}
  submitLabel="Create"
  submitLoadingLabel="Creating..."
  onSubmit={handleSubmit}
>
  <FormField label="Name" {...register("name")} />
  <FormField label="Description" type="textarea" {...register("description")} />
</FormDialog>
```

### Confirm Dialog

Use `ConfirmDialog` for dangerous actions:

```tsx
import { ConfirmDialog } from "@/components/shared";

<ConfirmDialog
  open={isDeleteOpen}
  onOpenChange={setIsDeleteOpen}
  title="Delete Item"
  description="Are you sure you want to delete this item? This action cannot be undone."
  confirmLabel="Delete"
  confirmLoadingLabel="Deleting..."
  destructive
  isLoading={isDeleting}
  onConfirm={handleDelete}
/>
```

### Dialog Structure Rules

1. Always include `DialogTitle` (accessibility requirement)
2. Always include `DialogDescription` for context
3. Place actions in `DialogFooter`
4. Cancel button on left, primary action on right
5. Show loading spinner in submit button, not overlay

---

## Tables

### Table Structure

```tsx
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { TableSkeleton, TableEmptyState } from "@/components/shared";

<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Name</TableHead>
      <TableHead>Status</TableHead>
      <TableHead className="w-[50px]"></TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {isLoading ? (
      <TableSkeleton columns={3} rows={5} />
    ) : items.length === 0 ? (
      <TableEmptyState
        colSpan={3}
        title="No items yet"
        description="Create your first item to get started."
        action={{ label: "Add Item", onClick: handleAdd }}
      />
    ) : (
      items.map((item) => (
        <TableRow key={item.id}>
          <TableCell>{item.name}</TableCell>
          <TableCell><Badge>{item.status}</Badge></TableCell>
          <TableCell>
            <DropdownMenu>...</DropdownMenu>
          </TableCell>
        </TableRow>
      ))
    )}
  </TableBody>
</Table>
```

### Table Action Column

Always place actions in the last column:

```tsx
<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant="ghost" size="icon">
      <MoreHorizontal className="h-4 w-4" />
    </Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent align="end">
    <DropdownMenuItem onClick={() => handleView(item)}>
      <Eye className="h-4 w-4 mr-2" />
      View
    </DropdownMenuItem>
    <DropdownMenuItem onClick={() => handleEdit(item)}>
      <Pencil className="h-4 w-4 mr-2" />
      Edit
    </DropdownMenuItem>
    <DropdownMenuSeparator />
    <DropdownMenuItem
      className="text-destructive"
      onClick={() => handleDelete(item)}
    >
      <Trash className="h-4 w-4 mr-2" />
      Delete
    </DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

---

## Loading States

### Component Reference

| Component | Use Case |
|-----------|----------|
| `PageLoading` | Full page loading |
| `CardLoading` | Card content loading |
| `TableLoading` | Simple table loading (spinner) |
| `TableSkeleton` | Table loading with placeholders |
| `CardSkeleton` | Card loading with placeholders |
| `StatCardSkeleton` | Dashboard stat card loading |
| `Skeleton` | Custom skeleton elements |

### Usage

```tsx
import { PageLoading, TableSkeleton, Skeleton } from "@/components/shared";

// Page loading
if (isLoading) return <PageLoading />;

// Table skeleton
<TableBody>
  {isLoading ? (
    <TableSkeleton columns={5} rows={10} />
  ) : (
    data.map(item => ...)
  )}
</TableBody>

// Custom skeleton
<div className="space-y-2">
  <Skeleton className="h-4 w-[200px]" />
  <Skeleton className="h-4 w-[150px]" />
</div>
```

---

## Empty States

### Component Reference

| Component | Use Case |
|-----------|----------|
| `EmptyState` | Page/section with no content |
| `TableEmptyState` | Table with no rows |
| `NoItemsEmptyState` | No items created yet |
| `NoResultsEmptyState` | Search/filter returned nothing |
| `ErrorEmptyState` | Error occurred |

### Message Guidelines

| Scenario | Title Format | Example |
|----------|--------------|---------|
| No items | "No {items} yet" | "No incidents yet" |
| No results | "No results found" | "No results found" |
| Error | "Error" | "Error" |

### Usage

```tsx
import { TableEmptyState, NoItemsEmptyState, NoResultsEmptyState } from "@/components/shared";

// Table empty state
<TableEmptyState
  colSpan={5}
  title="No incidents yet"
  description="Create your first incident to start tracking security events."
  action={{ label: "Add Incident", onClick: handleAdd }}
/>

// Page empty state (no items)
<NoItemsEmptyState
  itemName="Incident"
  onAdd={handleAdd}
/>

// Search returned nothing
<NoResultsEmptyState onClear={handleClearFilters} />
```

---

## Error Handling

### Error Display Hierarchy

1. **Toast notifications** - For transient errors (API failures, mutations)
2. **Inline errors** - For form validation
3. **Error states** - For page-level failures

### Toast Usage

```tsx
import { toast } from "sonner";

// Success
toast.success("Item created successfully");

// Error
toast.error("Failed to create item");

// With description
toast.error("Failed to create item", {
  description: "Please check your input and try again.",
});
```

### Error State

```tsx
import { ErrorState, ErrorEmptyState } from "@/components/shared";

// Page-level error
if (error) {
  return (
    <ErrorState
      title="Failed to load data"
      message={error.message}
      onRetry={refetch}
    />
  );
}
```

---

## Page Layouts

### Standard Page Structure

```tsx
export default function ModulePage() {
  return (
    <div className="flex flex-col h-full">
      <Header
        title={t("module.title")}
        actions={
          <Button onClick={handleAdd}>
            <Plus className="h-4 w-4 mr-2" />
            Add Item
          </Button>
        }
      />

      <div className="p-6 space-y-6 overflow-y-auto">
        {/* Filters */}
        <div className="flex gap-4">
          <Input placeholder="Search..." />
          <Select>...</Select>
        </div>

        {/* Stats cards (optional) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>...</Card>
        </div>

        {/* Main content */}
        <Card>
          <Table>...</Table>
        </Card>
      </div>
    </div>
  );
}
```

### Page with Tabs

```tsx
<Tabs defaultValue="overview">
  <TabsList>
    <TabsTrigger value="overview">Overview</TabsTrigger>
    <TabsTrigger value="details">Details</TabsTrigger>
  </TabsList>

  <TabsContent value="overview">...</TabsContent>
  <TabsContent value="details">...</TabsContent>
</Tabs>
```

---

## Icons

### Standard Sizes

| Context | Size | Class |
|---------|------|-------|
| Button icons | 16px | `h-4 w-4` |
| Table cell icons | 16px | `h-4 w-4` |
| Card header icons | 20px | `h-5 w-5` |
| Empty state icons | 24-32px | `h-6 w-6` to `h-8 w-8` |
| Page header icons | 32-48px | `h-8 w-8` to `h-12 w-12` |

### Icon Spacing

```tsx
// Icon before text
<Plus className="h-4 w-4 mr-2" />

// Icon after text
<span className="ml-2"><ChevronRight className="h-4 w-4" /></span>

// Icon only (no margin)
<MoreHorizontal className="h-4 w-4" />
```

### Common Icons by Action

| Action | Icon |
|--------|------|
| Add/Create | `Plus` |
| Edit | `Pencil` |
| Delete | `Trash` |
| View | `Eye` |
| Search | `Search` |
| Filter | `Filter` |
| Refresh | `RefreshCw` |
| Settings | `Settings` |
| More actions | `MoreHorizontal` |
| Close | `X` |
| Back | `ArrowLeft` |
| Download | `Download` |
| Upload | `Upload` |

---

## Component Import Cheatsheet

```tsx
// From shared components
import {
  // Loading
  PageLoading,
  TableSkeleton,
  Skeleton,

  // Empty states
  TableEmptyState,
  NoItemsEmptyState,
  NoResultsEmptyState,

  // Forms
  FormField,
  LoadingButton,

  // Dialogs
  FormDialog,
  ConfirmDialog,

  // Layout
  Header,
} from "@/components/shared";

// From UI components
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
```

---

## Migration Guide

When updating existing pages to follow these patterns:

1. **Replace text loading with TableSkeleton**
   ```tsx
   // Before
   {isLoading && <tr><td colSpan={5}>Loading...</td></tr>}

   // After
   {isLoading && <TableSkeleton columns={5} rows={5} />}
   ```

2. **Replace simple empty with TableEmptyState**
   ```tsx
   // Before
   {items.length === 0 && <tr><td colSpan={5}>No items</td></tr>}

   // After
   {items.length === 0 && (
     <TableEmptyState
       colSpan={5}
       title="No items yet"
       action={{ label: "Add Item", onClick: handleAdd }}
     />
   )}
   ```

3. **Replace dialog forms with FormDialog**
   ```tsx
   // Before
   <Dialog><DialogContent>...</DialogContent></Dialog>

   // After
   <FormDialog title="..." onSubmit={...}>...</FormDialog>
   ```

4. **Add loading spinners to buttons**
   ```tsx
   // Before
   <Button disabled={isPending}>{isPending ? "Saving..." : "Save"}</Button>

   // After
   <LoadingButton isLoading={isPending} loadingText="Saving...">Save</LoadingButton>
   ```
