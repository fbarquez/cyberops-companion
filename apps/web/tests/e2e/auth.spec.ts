import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test.describe('Login Page', () => {
    test('should display login form', async ({ page }) => {
      await page.goto('/login')

      await expect(page.getByRole('heading', { name: /login|sign in/i })).toBeVisible()
      await expect(page.getByLabel(/email/i)).toBeVisible()
      await expect(page.getByLabel(/password/i)).toBeVisible()
      await expect(page.getByRole('button', { name: /login|sign in/i })).toBeVisible()
    })

    test('should show validation errors for empty form', async ({ page }) => {
      await page.goto('/login')

      await page.getByRole('button', { name: /login|sign in/i }).click()

      // Should show validation error
      await expect(page.getByText(/required|email|password/i)).toBeVisible()
    })

    test('should show error for invalid credentials', async ({ page }) => {
      await page.goto('/login')

      await page.getByLabel(/email/i).fill('invalid@example.com')
      await page.getByLabel(/password/i).fill('wrongpassword')
      await page.getByRole('button', { name: /login|sign in/i }).click()

      // Should show error message
      await expect(page.getByText(/invalid|incorrect|failed/i)).toBeVisible({ timeout: 10000 })
    })

    test('should navigate to register page', async ({ page }) => {
      await page.goto('/login')

      await page.getByRole('link', { name: /register|sign up|create account/i }).click()

      await expect(page).toHaveURL(/register/)
    })
  })

  test.describe('Registration', () => {
    test('should display registration form', async ({ page }) => {
      await page.goto('/register')

      await expect(page.getByRole('heading', { name: /register|sign up|create/i })).toBeVisible()
      await expect(page.getByLabel(/email/i)).toBeVisible()
      await expect(page.getByLabel(/password/i).first()).toBeVisible()
      await expect(page.getByLabel(/name/i)).toBeVisible()
    })
  })

  test.describe('Protected Routes', () => {
    test('should redirect to login when not authenticated', async ({ page }) => {
      await page.goto('/incidents')

      // Should redirect to login
      await expect(page).toHaveURL(/login/)
    })
  })
})
