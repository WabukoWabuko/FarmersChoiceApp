# Autonomous Farm Intelligence: Source Matrix

This matrix is the initial Kenya-first source contract. Provider access, licensing, and quotas must be confirmed before production rollout; the application must expose source status and abstain when a source is unavailable or stale.

| Intelligence | Automatic source | Update frequency | Resolution | Cost | Confidence |
| --- | --- | --- | --- | --- | --- |
| Weather observations and forecast | Kenya Meteorological Department where access is contracted; ICPAC climate services; NASA POWER or Open-Meteo as a documented fallback | 15 minutes to daily, provider-dependent | Station or 1-11 km grid | Contract or free tier; verify limits | High for contracted station data; medium for fallback grids |
| Rainfall history and anomaly | CHIRPS via ClimateSERV or public cloud distribution | Daily | About 5 km grid | Free for research and many commercial uses; verify license | High for regional anomaly; lower for a single field |
| Satellite vegetation and crop stress | Copernicus Sentinel-2 via Copernicus Data Space or STAC-compatible cloud catalog; Landsat Collection 2 fallback | 3-5 days to weekly, cloud-dependent | 10 m Sentinel-2; 30 m Landsat | Public access subject to service terms and quotas | High for clear-sky indices; low when cloud-obscured |
| Soil texture and baseline properties | ISRIC SoilGrids; Kenya soil maps where licensed; farmer or laboratory samples for calibration | Static map revisions plus sample events | 250 m SoilGrids; field sample point | SoilGrids is open; laboratory and licensed maps incur cost | Medium for baseline maps; high for verified samples |
| Terrain, elevation, and slope | Copernicus DEM or NASA SRTM | Static | 30 m to 90 m | Public/open access subject to terms | High for terrain-derived risk |
| Market prices and availability | Kenya Agricultural Market Information System (KAMIS) or Agriculture and Food Authority feeds where available; WFP or FAOSTAT for regional fallback | Daily to weekly | Market and commodity level | Public/contract-dependent | Medium until market and commodity coverage is verified |
| Crop calendars and agronomy | KALRO guidance, Kenya county extension material, FAO crop knowledge, and versioned agronomist rules | Seasonal and revision-based | Crop, county, and agroecological zone | Public or partner/licensed | Medium until locally reviewed; high only for approved rules |
| Drought and food-security risk | ICPAC drought products; FEWS NET and FAO datasets | Weekly to monthly | County or regional grid | Public/partner terms | Medium to high for regional risk, not field diagnosis |
| Farm boundary and field identity | Farmer-captured polygon or GPS survey, with consent and accuracy metadata | On change | Field polygon | Device and survey cost | High when GPS accuracy and consent are recorded |

## Pipeline Contract

Every provider adapter must emit a normalized observation envelope:

```text
source, provider_version, observed_at, fetched_at, geometry,
variable, value, unit, resolution, quality_flags, confidence,
license, raw_payload_reference
```

The automated pipeline is organized into these stages:

1. **Schedule**: enqueue provider jobs by cadence, field geography, and tenant consent.
2. **Fetch**: apply timeouts, retries with backoff, rate-limit handling, and circuit breaking.
3. **Archive**: retain the raw response and request metadata in object storage or a local raw-data volume.
4. **Normalize**: convert units, timestamps, coordinate reference systems, and provider schemas.
5. **Validate**: reject impossible values, detect duplicates, mark gaps, and attach quality flags.
6. **Aggregate**: intersect grids with field polygons and calculate field-level summaries with uncertainty.
7. **Persist**: write normalized observations, provenance, freshness, and model inputs to PostgreSQL/PostGIS in production; SQLite remains the local prototype backend.
8. **Score**: run versioned recommendation, health, risk, and operations models only on observations passing freshness and quality thresholds.
9. **Explain**: retain the exact observations, source versions, assumptions, and confidence components used for each decision.
10. **Deliver**: update the dashboard and send only actionable alerts; route low-confidence or high-impact decisions to agronomist review.

## Rollout Gates

- Pilot one or two Kenyan counties and a small crop set before claiming national or pan-African coverage.
- Do not label demo or fallback data as current field observations.
- Do not issue an autonomous action when required observations are stale, missing, cloud-obscured, or below the configured confidence threshold.
- Record source licensing, farmer consent, data retention, and deletion behavior for every tenant.
- Promote a provider to production only after fixture tests, outage tests, quota tests, and an agronomist review of representative fields.