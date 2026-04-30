import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

export const handlers = [
  http.post('/api/query', () =>
    HttpResponse.json({
      answer: 'Test answer from the brain.',
      sources: ['test_doc', 'another_doc'],
    }),
  ),

  http.get('/api/graph/data', () =>
    HttpResponse.json({
      nodes: [{ data: { id: 'doc_1', label: 'Doc One' } }],
      edges: [],
    }),
  ),

  http.get('/api/doc/:slug', ({ params }) =>
    HttpResponse.json({
      slug: params.slug,
      title: String(params.slug).replace(/_/g, ' '),
      tags: ['test', 'brain'],
      content_html: '<h1>Test Document</h1><p>Hello world.</p>',
    }),
  ),

  http.get('/api/settings', () =>
    HttpResponse.json({
      localai_base_url: 'http://localai:8080',
      tagger: {
        backend: 'anthropic',
        anthropic_model: 'claude-haiku-4-5',
        local_model: 'mistral-7b-instruct',
        temperature: 0.2,
      },
      linker: {
        backend: 'anthropic',
        anthropic_model: 'claude-sonnet-4-6',
        local_model: 'mistral-7b-instruct',
        temperature: 0.3,
      },
    }),
  ),

  http.post('/api/settings', () => HttpResponse.json({ status: 'saved' })),

  http.get('/api/ingest/log', () =>
    HttpResponse.json([
      { ts: '2026-04-30T10:00:00', slug: 'test_doc', warnings: [] },
    ]),
  ),

  http.post('/api/upload', () =>
    HttpResponse.json({
      filename: 'test.pdf',
      status: 'Ingestion started in background',
    }),
  ),

  http.post('/api/settings/test-localai', () =>
    HttpResponse.json({ ok: true, models: ['mistral-7b-instruct'] }),
  ),
]

export const server = setupServer(...handlers)
