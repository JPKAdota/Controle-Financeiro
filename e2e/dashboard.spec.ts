import { test, expect } from '@playwright/test';

test('App deve carregar e mostrar a interface do Controle Financeiro', async ({ page }) => {
    await page.goto('/');

    await expect(page).toHaveTitle(/Controle Financeiro/i);
    await expect(page.getByRole('heading', { name: 'Relatório Financeiro' })).toBeVisible();
});
