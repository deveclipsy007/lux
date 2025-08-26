import { test, expect } from './fixtures';

// Executes a RAG query via API and validates the response structure

test('executa consulta RAG e valida resposta', async ({ request }) => {
  const response = await request.post('/api/rag', {
    data: { query: 'Olá, tudo bem?' }
  });

  expect(response.ok()).toBeTruthy();
  const json = await response.json();
  expect(json).toHaveProperty('answer');
});
