export const CURRENT_DESIGN_VERSION = "v4-practice-net-map";

export const APP_ERAS = [
  {
    id: "first-live-tracker",
    designVersions: ["v0-manual-tracker"],
    title: "First Live Tracker",
    dateLabel: "Jun 27, 2026",
    shortLabel: "First Live",
    summary: "Practice sessions became persistent, trackable records.",
    visibleFeature: "Manual sessions, Quick Log, Target Completion, and public read-only stats.",
    snapshotKind: "first-live",
    primarySha: "d44fa987675a3043cf06d78047d41862a3a7123f",
    codeUrl:
      "https://github.com/sdrawkcaBdeT/chipping/tree/d44fa987675a3043cf06d78047d41862a3a7123f"
  },
  {
    id: "polish-fonts",
    designVersions: ["v1-dashboard-polish"],
    title: "Polish (Fonts!)",
    dateLabel: "Jun 27, 2026",
    shortLabel: "Polish",
    summary: "The dashboard started to feel like a real training product.",
    visibleFeature: "Expressway and DIN typography, stronger hierarchy, and session detail pages.",
    snapshotKind: "polish-fonts",
    primarySha: "097e6eeae7a45bfc4549b5c43b8ca2dadad7e133",
    codeUrl:
      "https://github.com/sdrawkcaBdeT/chipping/tree/097e6eeae7a45bfc4549b5c43b8ca2dadad7e133"
  },
  {
    id: "net-map-analytics",
    designVersions: ["v2-net-map-analytics"],
    shaPrefixes: ["f557984"],
    title: "Net Map Analytics",
    dateLabel: "Jun 27, 2026",
    shortLabel: "Net Map",
    summary: "Target performance moved from a generic grid into the actual net layout.",
    visibleFeature: "Range-aware target map, last-run mode, and spatial practice readouts.",
    snapshotKind: "net-map",
    primarySha: "f557984",
    codeUrl: "https://github.com/sdrawkcaBdeT/chipping/tree/f557984"
  },
  {
    id: "app-era-timeline",
    designVersions: ["v3-app-era-timeline"],
    title: "App Era Timeline",
    dateLabel: "Jun 27, 2026",
    shortLabel: "Era Timeline",
    summary: "Sessions now carry a visible product-history trail.",
    visibleFeature: "Era badges, visual snapshots, session provenance, and code snapshots.",
    snapshotKind: "era-timeline",
    primarySha: null,
    codeUrl: null
  },
  {
    id: "practice-net-map",
    designVersions: [CURRENT_DESIGN_VERSION],
    title: "Practice Net Map",
    dateLabel: "Jun 27, 2026",
    shortLabel: "Practice Map",
    summary: "The physical target map moved into live practice and session review.",
    visibleFeature: "Current target, completed targets, and attempts now render on the real net layout.",
    snapshotKind: "practice-net",
    primarySha: null,
    codeUrl: null
  }
];

export function codeUrlForSha(sha) {
  return sha ? `https://github.com/sdrawkcaBdeT/chipping/tree/${sha}` : null;
}

export function resolveAppEra(source = {}) {
  const designVersion = source.design_version;
  const appGitSha = source.app_git_sha || "";

  const byDesignVersion = APP_ERAS.find((era) =>
    era.designVersions.includes(designVersion)
  );
  if (byDesignVersion) {
    if (
      designVersion === "v1-dashboard-polish" &&
      APP_ERAS.find((era) =>
        era.shaPrefixes?.some((prefix) => appGitSha.startsWith(prefix))
      )
    ) {
      return APP_ERAS.find((era) =>
        era.shaPrefixes?.some((prefix) => appGitSha.startsWith(prefix))
      );
    }
    return byDesignVersion;
  }

  const bySha = APP_ERAS.find((era) =>
    era.shaPrefixes?.some((prefix) => appGitSha.startsWith(prefix))
  );

  return bySha || APP_ERAS[APP_ERAS.length - 1];
}
