import { test, expect } from './fixtures';

// Creates a new agent through the UI and verifies it persists in the agent list

const LONG_INSTRUCTIONS = 'Instruções '.repeat(10); // >80 chars

test('criar agente e verificar persistência', async ({ page }) => {
  await page.goto('/');

  await page.fill('#agent_name', 'Agente Teste');
  await page.fill('#instructions', LONG_INSTRUCTIONS);
  await page.selectOption('#specialization', { value: 'Suporte' });

  await page.click('#btn-continue');

  await page.waitForSelector('#btn-materialize-server:not([disabled])');
  await page.click('#btn-materialize-server');

  await page.click('button.tab-button[data-section="page-agents"]');

  const card = page.locator('#agents-grid').locator('text=Agente Teste');
  await expect(card).toBeVisible();
});
