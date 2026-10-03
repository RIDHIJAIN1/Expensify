import http from 'k6/http';
import { check } from 'k6';
import { Trend, Counter } from 'k6/metrics';
import { BASE, JSON_HEADERS, cookieValue, buildCsv } from './lib.js';

const uploadDuration = new Trend('upload_duration', true);
const importedRows = new Counter('imported_rows');
const ROWS_PER_UPLOAD = 1000;

export const options = {
  scenarios: {
    uploads: {
      executor: 'shared-iterations',
      vus: 4,
      iterations: 12,
      maxDuration: '300s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    checks: ['rate>0.98'],
    upload_duration: ['p(95)<20000'],
  },
};

export function setup() {
  const email = `k6_upload_${Date.now()}@example.com`;
  const signup = http.post(
    `${BASE}/api/auth/signup`,
    JSON.stringify({ email, password: 'K6UploadPass!', name: 'k6 uploads' }),
    { headers: JSON_HEADERS }
  );
  if (signup.status !== 201) throw new Error(`signup failed: ${signup.status}`);
  return { access: cookieValue(signup, 'access_token') };
}

export default function (data) {
  const auth = {
    headers: { Cookie: `access_token=${data.access}` },
    timeout: '120s',
    tags: { kind: 'upload' },
  };
  const prefix = `U${__VU}I${__ITER}`;
  const csv = buildCsv(prefix, ROWS_PER_UPLOAD, 100000 + __VU * 10000 + __ITER * 1000);

  const res = http.post(
    `${BASE}/api/uploads`,
    { file: http.file(csv, `stress_${prefix}.csv`, 'text/csv') },
    auth
  );
  uploadDuration.add(res.timings.duration);
  if (res.status === 201) {
    const imported = res.json('imported_count') || 0;
    importedRows.add(imported);
    check(res, {
      'upload completed': (r) => r.json('status') === 'COMPLETED',
      'all rows imported': () => imported === ROWS_PER_UPLOAD,
    });
  }
  check(res, { 'upload status 201': (r) => r.status === 201 });
}
