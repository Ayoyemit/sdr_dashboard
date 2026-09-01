import { defineRailway, github, preserve, project, service } from "railway/iac";

/**
 * Ayoyemi2 — keep in sync with Railway dashboard.
 * web = API (Dockerfile at repo root), sdr_dashboard = Next.js (root sdr-web).
 */
export default defineRailway(() => {
  const web = service("web", {
    source: github("Ayoyemit/sdr_dashboard", {
      branch: "feature/new-ui",
      checkSuites: false,
    }),
    build: {
      builder: "DOCKERFILE",
      dockerfilePath: "sdr-api/Dockerfile",
    },
    deploy: {
      healthcheckPath: "/health",
      healthcheckTimeout: 300,
      restartPolicyType: "ON_FAILURE",
    },
    replicas: { "europe-west4-drams3a": 1 },
    env: {
      ALLOWED_ORIGINS: preserve(),
      DISABLE_PREWARM: preserve(),
    },
  });

  const sdr_dashboard = service("sdr_dashboard", {
    source: github("Ayoyemit/sdr_dashboard", {
      branch: "feature/new-ui",
      checkSuites: false,
      rootDirectory: "sdr-web",
    }),
    deploy: {
      healthcheckPath: "/",
      restartPolicyType: "ON_FAILURE",
    },
    replicas: { "europe-west4-drams3a": 1 },
    networking: { privateNetworkEndpoint: "sdrdashboard" },
    env: {
      NEXT_PUBLIC_API_BASE: preserve(),
    },
  });

  return project("Ayoyemi2", {
    resources: [web, sdr_dashboard],
  });
});
