import http from 'k6/http';
import { check, fail } from 'k6';
import { BASE, JSON_HEADERS, cookieValue, ok } from './lib.js';

export const options = {
  vus: 1,
  iterations: 1,
  thresholds: {
    http_req_failed: ['rate==0'],
    checks: ['rate==1'],
  },
};

export default function () {
  const stamp = Date.now();
  const email = `k6_smoke_${stamp}@example.com`;
  const password = 'K6SmokePass!';

  ok(http.get(`${BASE}/api/health`), 'health');

  const signup = http.post(
    `${BASE}/api/auth/signup`,
    JSON.stringify({ email, password, name: 'k6 smoke' }),
    { headers: JSON_HEADERS }
  );
  ok(signup, 'auth.signup', 201);
  const access = cookieValue(signup, 'access_token');
  const refresh = cookieValue(signup, 'refresh_token');
  if (!access || !refresh) fail('signup did not set auth cookies');

  const auth = { headers: { Cookie: `access_token=${access}` } };
  const authJson = { headers: { Cookie: `access_token=${access}`, 'Content-Type': 'application/json' } };

  ok(http.get(`${BASE}/api/auth/me`, auth), 'auth.me');
  ok(http.post(`${BASE}/api/auth/refresh`, null, { headers: { Cookie: `refresh_token=${refresh}` } }), 'auth.refresh');

  const csv =
    'Date,Description,Amount,Type,Reference\n' +
    `2026-09-01,Smoke Swiggy,428.50,DEBIT,SMOKE-${stamp}-1\n` +
    `2026-09-02,Smoke Amazon,999.00,DEBIT,SMOKE-${stamp}-2\n` +
    `2026-09-03,Smoke Salary,75000.00,CREDIT,SMOKE-${stamp}-3\n`;

  const upload = http.post(
    `${BASE}/api/uploads`,
    { file: http.file(csv, 'smoke.csv', 'text/csv') },
    auth
  );
  ok(upload, 'uploads.create', 201);
  check(upload, { 'upload imported 3': (r) => r.json('imported_count') === 3 });

  const reupload = http.post(
    `${BASE}/api/uploads`,
    { file: http.file(csv, 'smoke.csv', 'text/csv') },
    auth
  );
  ok(reupload, 'uploads.create dup', 201);
  check(reupload, { 'reupload deduped 3': (r) => r.json('duplicate_count') === 3 });

  ok(http.get(`${BASE}/api/uploads`, auth), 'uploads.list');
  ok(http.get(`${BASE}/api/uploads/${upload.json('id')}`, auth), 'uploads.get');

  const txs = http.get(`${BASE}/api/transactions?limit=5`, auth);
  ok(txs, 'transactions.list');
  check(txs, { 'transactions total 3': (r) => r.json('total') === 3 });
  const txId = txs.json('items.0.id');
  ok(http.get(`${BASE}/api/transactions/${txId}`, auth), 'transactions.get');

  const cats = http.get(`${BASE}/api/categories`, auth);
  ok(cats, 'categories.list');
  const foodId = cats.json().find((c) => c.name === 'Food').id;

  const cat = http.post(
    `${BASE}/api/categories`,
    JSON.stringify({ name: 'K6 Cat', keywords: ['k6merchant'], color: '#112233' }),
    authJson
  );
  ok(cat, 'categories.create', 201);
  const catId = cat.json('id');
  ok(http.patch(`${BASE}/api/categories/${catId}`, JSON.stringify({ name: 'K6 Cat 2' }), authJson), 'categories.update');
  ok(http.delete(`${BASE}/api/categories/${catId}`, null, auth), 'categories.delete');

  ok(http.patch(`${BASE}/api/transactions/${txId}`, JSON.stringify({ category_id: foodId }), authJson), 'transactions.patch');

  ok(http.get(`${BASE}/api/summary`, auth), 'summary');
  ok(http.get(`${BASE}/api/insights?date_from=2026-01-01&date_to=2026-12-31`, auth), 'insights');

  ok(http.put(`${BASE}/api/budgets/${foodId}`, JSON.stringify({ amount: '1000.00' }), authJson), 'budgets.put');
  ok(http.get(`${BASE}/api/budgets`, auth), 'budgets.list');
  ok(http.delete(`${BASE}/api/budgets/${foodId}`, null, auth), 'budgets.delete');

  const csvExport = http.get(`${BASE}/api/export/csv`, auth);
  ok(csvExport, 'export.csv');
  check(csvExport, { 'export csv header': (r) => r.body.startsWith('Date,Description,Amount,Type,Reference,Category') });

  const pdfExport = http.get(`${BASE}/api/export/pdf`, auth, { tags: { kind: 'pdf' } });
  ok(pdfExport, 'export.pdf');
  check(pdfExport, { 'export pdf magic': (r) => r.body.slice(0, 5) === '%PDF-' });

  ok(http.post(`${BASE}/api/auth/logout`, null, auth), 'auth.logout');
  ok(http.get(`${BASE}/api/auth/me`), 'auth.me anon after logout', 401);
}
