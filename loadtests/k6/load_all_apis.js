import http from 'k6/http';
import { check } from 'k6';
import { BASE, JSON_HEADERS, cookieValue, ok } from './lib.js';

export const options = {
  scenarios: {
    all_apis: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '15s', target: 10 },
        { duration: '30s', target: 20 },
        { duration: '20s', target: 20 },
        { duration: '10s', target: 0 },
      ],
      gracefulRampDown: '5s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<1500', 'p(99)<4000'],
    checks: ['rate>0.99'],
  },
};

export function setup() {
  const email = `k6_load_${Date.now()}@example.com`;
  const password = 'K6LoadPass!';
  const signup = http.post(
    `${BASE}/api/auth/signup`,
    JSON.stringify({ email, password, name: 'k6 load' }),
    { headers: JSON_HEADERS }
  );
  if (signup.status !== 201) throw new Error(`signup failed: ${signup.status} ${signup.body}`);
  const access = cookieValue(signup, 'access_token');
  const refresh = cookieValue(signup, 'refresh_token');
  const auth = { headers: { Cookie: `access_token=${access}` } };

  const lines = ['Date,Description,Amount,Type,Reference'];
  for (let i = 0; i < 300; i++) {
    const day = (i % 28) + 1;
    const cents = 5000 + i;
    lines.push(
      `2026-09-${day < 10 ? '0' : ''}${day},SeedMerchant${i % 20},` +
        `${Math.floor(cents / 100)}.${String(cents % 100).padStart(2, '0')},` +
        `${i % 5 === 0 ? 'CREDIT' : 'DEBIT'},SEED-${i}`
    );
  }
  const upload = http.post(
    `${BASE}/api/uploads`,
    { file: http.file(lines.join('\n'), 'seed.csv', 'text/csv') },
    auth
  );
  if (upload.status !== 201) throw new Error(`seed upload failed: ${upload.status} ${upload.body}`);

  const txs = http.get(`${BASE}/api/transactions?limit=20`, auth);
  const cats = http.get(`${BASE}/api/categories`, auth);
  return {
    access,
    refresh,
    txIds: txs.json('items').map((t) => t.id),
    foodId: cats.json().find((c) => c.name === 'Food').id,
    uploadId: upload.json('id'),
  };
}

export default function (data) {
  const auth = { headers: { Cookie: `access_token=${data.access}` } };
  const roll = Math.random() * 100;
  const txId = data.txIds[Math.floor(Math.random() * data.txIds.length)];

  if (roll < 22) {
    const type = Math.random() < 0.5 ? 'DEBIT' : 'CREDIT';
    const offset = Math.floor(Math.random() * 100);
    ok(http.get(`${BASE}/api/transactions?limit=25&type=${type}&offset=${offset}`, auth), 'transactions.list');
  } else if (roll < 36) {
    ok(http.get(`${BASE}/api/summary?date_from=2026-08-01&date_to=2026-10-31`, auth), 'summary');
  } else if (roll < 44) {
    ok(http.get(`${BASE}/api/insights?date_from=2026-08-01&date_to=2026-10-31`, auth), 'insights');
  } else if (roll < 54) {
    ok(http.get(`${BASE}/api/budgets?date_from=2026-08-01&date_to=2026-10-31`, auth), 'budgets.list');
  } else if (roll < 62) {
    ok(http.get(`${BASE}/api/categories`, auth), 'categories.list');
  } else if (roll < 70) {
    ok(http.get(`${BASE}/api/uploads`, auth), 'uploads.list');
  } else if (roll < 78) {
    ok(http.get(`${BASE}/api/transactions/${txId}`, auth), 'transactions.get');
  } else if (roll < 88) {
    const res = http.get(`${BASE}/api/export/csv?date_from=2026-08-01&date_to=2026-10-31`, auth);
    ok(res, 'export.csv');
    check(res, { 'export csv non-trivial': (r) => r.body.length > 100 });
  } else if (roll < 94) {
    ok(http.get(`${BASE}/api/health`), 'health');
  } else {
    ok(http.post(`${BASE}/api/auth/refresh`, null, { headers: { Cookie: `refresh_token=${data.refresh}` } }), 'auth.refresh');
  }
}
