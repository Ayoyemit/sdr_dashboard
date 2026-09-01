import { defineRailway, github, preserve, project, service } from "railway/iac";

/**
 * Railway project: Ayoyemi2
 *
 * Service naming in Railway (do not swap):
 *   - web           → FastAPI (repo root, sdr-api/Dockerfile)
 *   - sdr_dashboard → Next.js frontend (root directory: sdr-web)
 */
export default defineRailway(() => {
  const web = service("web", {
    source: github("Ayoyemit/sdr_dashboard", {
      branch: "feature/new-ui",
      checkSuites: false,
    }),
    healthcheck: { path: "/health", timeout: 300 },
    replicas: { "europe-west4-drams3a": 1 },
    env: {
      ALLOWED_ORIGINS: preserve(),
    },
  });

  const sdr_dashboard = service("sdr_dashboard", {
    source: github("Ayoyemit/sdr_dashboard", {
      branch: "feature/new-ui",
      checkSuites: false,
      rootDirectory: "sdr-web",
    }),
    healthcheck: { path: "/" },
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
