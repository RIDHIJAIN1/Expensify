import http from 'k6/http';
import { check } from 'k6';
import { BASE, JSON_HEADERS, cookieValue, ok } from './lib.js';

const ROWS = 500;

export const options = {
  scenarios: {
    exports: {
      executor: 'shared-iterations',
      vus: 5,
      iterations: 20,
      maxDuration: '180s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    checks: ['rate>0.98'],
    'http_req_duration{kind:pdf}': ['p(95)<8000'],
    'http_req_duration{kind:csv}': ['p(95)<3000'],
  },
};

export function setup() {
  const email = `k6_export_${Date.now()}@example.com`;
  const password = 'K6ExportPass!';
  const signup = http.post(
    `${BASE}/api/auth/signup`,
    JSON.stringify({ email, password, name: 'k6 export' }),
    { headers: JSON_HEADERS }
  );
  if (signup.status !== 201) throw new Error(`signup failed: ${signup.status}`);
  const access = cookieValue(signup, 'access_token');

  const lines = ['Date,Description,Amount,Type,Reference'];
  for (let i = 0; i < ROWS; i++) {
    const day = (i % 28) + 1;
    const cents = 1000 + i;
    lines.push(
      `2026-09-${day < 10 ? '0' : ''}${day},ExportMerchant${i % 30},` +
        `${Math.floor(cents / 100)}.${String(cents % 100).padStart(2, '0')},` +
        `${i % 4 === 0 ? 'CREDIT' : 'DEBIT'},EXP-${i}`
    );
  }
  const upload = http.post(
    `${BASE}/api/uploads`,
    { file: http.file(lines.join('\n'), 'export_seed.csv', 'text/csv') },
    { headers: { Cookie: `access_token=${access}` } }
  );
  if (upload.status !== 201) throw new Error(`seed upload failed: ${upload.status} ${upload.body}`);
  return { access, rows: upload.json('imported_count') };
}

export default function (data) {
  const auth = { headers: { Cookie: `access_token=${data.access}` } };

  const csv = http.get(`${BASE}/api/export/csv`, {
    ...auth,
    tags: { kind: 'csv' },
  });
  ok(csv, 'export.csv');
  check(csv, {
    'csv exact row count': (r) => r.body.split('\n').length - 2 === data.rows,
    'csv header intact': (r) => r.body.startsWith('Date,Description,Amount,Type,Reference,Category'),
  });

  const filtered = http.get(`${BASE}/api/export/csv?date_from=2026-09-01&date_to=2026-09-10`, {
    ...auth,
    tags: { kind: 'csv' },
  });
  ok(filtered, 'export.csv filtered');
  check(filtered, { 'filtered csv smaller': (r) => r.body.split('\n').length - 2 < data.rows });

  const pdf = http.get(`${BASE}/api/export/pdf`, {
    ...auth,
    tags: { kind: 'pdf' },
    timeout: '60s',
  });
  ok(pdf, 'export.pdf');
  check(pdf, {
    'pdf magic bytes': (r) => r.body.slice(0, 5) === '%PDF-',
    'pdf non-trivial size': (r) => r.body.length > 1500,
    'pdf eof marker': (r) => r.body.includes('%%EOF'),
  });
}
