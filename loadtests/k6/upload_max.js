import http from 'k6/http';
import { check } from 'k6';
import { Trend } from 'k6/metrics';
import { BASE, JSON_HEADERS, cookieValue } from './lib.js';

const MAX_CSV = open('/scripts/fixtures/max_upload.csv');
const MAX_ROWS = MAX_CSV.split('\n').filter((line) => line.trim().length > 0).length - 1;

const maxUploadDuration = new Trend('max_upload_duration', true);
const maxUploadImported = new Trend('max_upload_imported');

export const options = {
  scenarios: {
    max_concurrent: {
      executor: 'shared-iterations',
      exec: 'uploadMax',
      vus: 3,
      iterations: 3,
      maxDuration: '900s',
    },
  },
  thresholds: {
    'http_req_duration{kind:max}': ['p(95)<600000'],
    http_req_failed: ['rate<0.01'],
  },
};

export function setup() {
  const email = `k6_maxupload_${Date.now()}@example.com`;
  const signup = http.post(
    `${BASE}/api/auth/signup`,
    JSON.stringify({ email, password: 'K6MaxPass!', name: 'k6 max upload' }),
    { headers: JSON_HEADERS }
  );
  if (signup.status !== 201) throw new Error(`signup failed: ${signup.status}`);
  return { access: cookieValue(signup, 'access_token'), rows: MAX_ROWS };
}

export function uploadMax(data) {
  const res = http.post(
    `${BASE}/api/uploads`,
    { file: http.file(MAX_CSV, `max_${__VU}_${__ITER}.csv`, 'text/csv') },
    {
      headers: { Cookie: `access_token=${data.access}` },
      timeout: '900s',
      tags: { kind: 'max' },
    }
  );
  maxUploadDuration.add(res.timings.duration);
  check(res, { 'max upload accepted': (r) => r.status === 201 });
  if (res.status === 201) {
    const imported = res.json('imported_count');
    const duplicates = res.json('duplicate_count');
    maxUploadImported.add(imported);
    check(res, {
      'max upload fully accounted': () => imported + duplicates === data.rows,
    });
  }
}
