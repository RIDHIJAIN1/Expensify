import http from 'k6/http';
import { check } from 'k6';
import { BASE, JSON_HEADERS, cookieValue } from './lib.js';

const OVER_CSV = open('/scripts/fixtures/over_limit.csv');

export const options = {
  scenarios: {
    over_limit: {
      executor: 'shared-iterations',
      vus: 1,
      iterations: 1,
      maxDuration: '60s',
    },
  },
  thresholds: {
    checks: ['rate==1'],
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<5000'],
  },
};

export function setup() {
  const email = `k6_overlimit_${Date.now()}@example.com`;
  const signup = http.post(
    `${BASE}/api/auth/signup`,
    JSON.stringify({ email, password: 'K6OverPass!', name: 'k6 over limit' }),
    { headers: JSON_HEADERS }
  );
  if (signup.status !== 201) throw new Error(`signup failed: ${signup.status}`);
  return { access: cookieValue(signup, 'access_token') };
}

export default function (data) {
  const res = http.post(
    `${BASE}/api/uploads`,
    { file: http.file(OVER_CSV, 'over_limit.csv', 'text/csv') },
    {
      headers: { Cookie: `access_token=${data.access}` },
      timeout: '60s',
      responseCallback: http.expectedStatuses(400),
    }
  );
  check(res, {
    'over-limit rejected 400': (r) => r.status === 400,
    'over-limit explains size': (r) => r.body.includes('too large'),
  });
}
