import http from 'k6/http';
import { check } from 'k6';

export const BASE = __ENV.BASE_URL || 'http://host.docker.internal:8000';
export const JSON_HEADERS = { 'Content-Type': 'application/json' };

export function cookieValue(res, name) {
  const list = res.cookies[name];
  return list && list.length ? list[0].value : '';
}

export function signup(email, password, name) {
  return http.post(
    `${BASE}/api/auth/signup`,
    JSON.stringify({ email, password, name }),
    { headers: JSON_HEADERS }
  );
}

export function ok(res, label, expected) {
  const want = expected === undefined ? 200 : expected;
  return check(res, { [`${label} [${want}]`]: (r) => r.status === want });
}

export function buildCsv(prefix, rows, amountBase) {
  const lines = ['Date,Description,Amount,Type,Reference'];
  for (let i = 0; i < rows; i++) {
    const day = (i % 28) + 1;
    const cents = amountBase + i;
    lines.push(
      `2026-09-${day < 10 ? '0' : ''}${day},` +
        `${prefix}Merchant${i % 40},` +
        `${Math.floor(cents / 100)}.${String(cents % 100).padStart(2, '0')},` +
        `${i % 5 === 0 ? 'CREDIT' : 'DEBIT'},` +
        `${prefix}-${i}-${Math.random().toString(36).slice(2, 8)}`
    );
  }
  return lines.join('\n');
}
