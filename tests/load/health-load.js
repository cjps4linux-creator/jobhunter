import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  scenarios: [
    {
      name: "baseline",
      executor: "constant-vus",
      vus: 5,
      duration: "30s",
    },
  ],
};

const BASE_URL = __ENV.BASE_URL || "http://127.0.0.1:8000";

export default function () {
  const res = http.get(`${BASE_URL}/health`);
  check(res, {
    "status is 200": (r) => r.status === 200,
    "latency < 250ms": (r) => r.timings.duration < 250,
  });
  sleep(0.2);
}

export function handleSummary(data) {
  return {
    "artifacts/b5/k6-summary.json": JSON.stringify(data, null, 2),
    stdout: JSON.stringify(data, null, 2),
  };
}
