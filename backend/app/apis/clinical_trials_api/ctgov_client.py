"""ClinicalTrials.gov v2 client built to stay independent from existing agents.

Inputs/outputs are intentionally simple dictionaries so this module can be
plugged into the clinical agent later without rewiring business logic.

Key capabilities
- Query v2 /studies with field projection and pagination.
- Normalize studies into a compact shape for downstream analytics/visuals.
- Compute lightweight aggregates (phase/status/sponsor/location counts).

Data contracts
---------------
`search_trials` returns a dict with:
- query: filters that were applied
- total_returned: number of normalized trials in this page/window
- trials: list of normalized trial dicts (see `_normalize_study`)
- aggregates: counters for phase/status/sponsor/location + enrollment summary
- source: metadata about API/timeouts

This module avoids touching existing agent code and can be imported later via:
`from app.apis.clinical_trials_api import ClinicalTrialsGovClient`
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional

import requests

DEFAULT_BASE_URL = "https://clinicaltrials.gov/api/v2"

# Default field projection focused on metadata + design + site footprint
SUMMARY_FIELDS = [
    "protocolSection.identificationModule.nctId",
    "protocolSection.identificationModule.briefTitle",
    "protocolSection.identificationModule.officialTitle",
    "protocolSection.identificationModule.acronym",
    "protocolSection.statusModule.overallStatus",
    "protocolSection.statusModule.startDateStruct",
    "protocolSection.statusModule.primaryCompletionDateStruct",
    "protocolSection.statusModule.completionDateStruct",
    "protocolSection.statusModule.studyFirstPostDateStruct",
    "protocolSection.statusModule.resultsFirstPostDateStruct",
    "protocolSection.statusModule.whyStopped",
    "protocolSection.statusModule.lastUpdatePostDateStruct",
    "protocolSection.designModule.phases",
    "protocolSection.designModule.studyType",
    "protocolSection.designModule.designInfo.allocation",
    "protocolSection.designModule.designInfo.interventionModel",
    "protocolSection.designModule.designInfo.interventionModelDescription",
    "protocolSection.designModule.enrollmentInfo.count",
    "protocolSection.designModule.enrollmentInfo.type",
    "protocolSection.armsInterventionsModule.armGroups",
    "protocolSection.armsInterventionsModule.interventions",
    "protocolSection.contactsLocationsModule.locations",
    "protocolSection.contactsLocationsModule.overallOfficials",
    "protocolSection.sponsorCollaboratorsModule.leadSponsor",
    "protocolSection.sponsorCollaboratorsModule.collaborators",
    "protocolSection.outcomesModule.primaryOutcomes",
    "protocolSection.outcomesModule.secondaryOutcomes",
    "protocolSection.eligibilityModule.eligibilityCriteria",
    "protocolSection.eligibilityModule.sex",
    "protocolSection.eligibilityModule.minimumAge",
    "protocolSection.eligibilityModule.maximumAge",
    "protocolSection.eligibilityModule.healthyVolunteers",
    "derivedSection.conditionsModule.conditions",
    "derivedSection.interventionsModule.interventionsMeshList",
    "hasResults",
]

# Extended fields for results when explicitly requested
RESULT_FIELDS = [
    "resultsSection.participantFlowModule",
    "resultsSection.baselineCharacteristicsModule",
    "resultsSection.outcomeMeasuresModule",
    "resultsSection.adverseEventsModule",
]


class ClinicalTrialsGovClient:
    """Thin wrapper over ClinicalTrials.gov v2 endpoints."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = 20,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    def search_trials(
        self,
        drug_name: Optional[str] = None,
        condition: Optional[str] = None,
        phase: Optional[str] = None,
        status: Optional[str] = None,
        country: Optional[str] = None,
        page_size: int = 200,
        max_records: int = 500,
        include_results: bool = False,
    ) -> Dict[str, Any]:
        """Search for studies and return normalized payload with aggregates."""
        if not drug_name and not condition:
            raise ValueError(
                "At least one of drug_name or condition is required for querying trials"
            )

        term_parts = []
        if drug_name:
            term_parts.append(f'intervention:"{drug_name}"')
        if condition:
            term_parts.append(f'condition:"{condition}"')
        if phase:
            term_parts.append(f'phase:"{phase}"')
        if status:
            term_parts.append(f'status:"{status}"')
        if country:
            term_parts.append(f'country:"{country}"')

        query_term = " AND ".join(term_parts)

        fields = SUMMARY_FIELDS + (RESULT_FIELDS if include_results else [])

        studies = self._request_studies(
            query_term=query_term,
            fields=fields,
            page_size=page_size,
            max_records=max_records,
        )

        normalized = [self._normalize_study(study) for study in studies]
        aggregates = self._summarize_trials(normalized)

        return {
            "query": {
                "drug_name": drug_name,
                "condition": condition,
                "phase": phase,
                "status": status,
                "country": country,
                "page_size": page_size,
                "max_records": max_records,
                "include_results": include_results,
            },
            "total_returned": len(normalized),
            "trials": normalized,
            "aggregates": aggregates,
            "source": {
                "api": "clinicaltrials.gov v2",
                "endpoint": f"{self.base_url}/studies",
                "query_term": query_term,
                "timeout_seconds": self.timeout,
            },
        }

    def fetch_trial(self, nct_id: str, include_results: bool = False) -> Dict[str, Any]:
        """Fetch a single study by NCT ID and normalize it."""
        if not nct_id:
            raise ValueError("nct_id is required")

        url = f"{self.base_url}/studies/{nct_id}"
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        # Single trial endpoint returns the study object directly (not wrapped)
        study = data
        return {
            "trial": self._normalize_study(study),
            "source": {
                "api": "clinicaltrials.gov v2",
                "endpoint": url,
                "timeout_seconds": self.timeout,
            },
        }

    # ---- Internal helpers -------------------------------------------------

    def _request_studies(
        self,
        query_term: str,
        fields: List[str],
        page_size: int,
        max_records: int,
    ) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/studies"
        params = {
            "query.term": query_term,
            "pageSize": page_size,
        }

        # Omit fields parameter: v2 API returns full data structure and
        # field filtering can cause 400 errors. Better to fetch full and
        # normalize selectively than to struggle with field validation.
        # If payload size becomes issue, revisit with actual working fields.

        results: List[Dict[str, Any]] = []
        page_token: Optional[str] = None

        while len(results) < max_records:
            if page_token:
                params["pageToken"] = page_token
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            studies = data.get("studies", [])
            results.extend(studies)
            page_token = data.get("nextPageToken")
            if not page_token or not studies:
                break
        return results[:max_records]

    def _normalize_study(self, study: Dict[str, Any]) -> Dict[str, Any]:
        """Map API study to a compact, analysis-friendly structure."""
        protocol = study.get("protocolSection", {})
        derived = study.get("derivedSection", {})

        ident = protocol.get("identificationModule", {})
        status = protocol.get("statusModule", {})
        design = protocol.get("designModule", {})
        arms = protocol.get("armsInterventionsModule", {})
        outcomes = protocol.get("outcomesModule", {})
        eligibility = protocol.get("eligibilityModule", {})
        contacts = protocol.get("contactsLocationsModule", {})
        sponsors = protocol.get("sponsorCollaboratorsModule", {})

        conditions = (derived.get("conditionsModule") or {}).get("conditions", [])

        normalized = {
            "nct_id": ident.get("nctId"),
            "brief_title": ident.get("briefTitle"),
            "official_title": ident.get("officialTitle"),
            "acronym": ident.get("acronym"),
            "overall_status": status.get("overallStatus"),
            "start_date": self._extract_date(status.get("startDateStruct")),
            "primary_completion_date": self._extract_date(
                status.get("primaryCompletionDateStruct")
            ),
            "completion_date": self._extract_date(status.get("completionDateStruct")),
            "study_first_post_date": self._extract_date(
                status.get("studyFirstPostDateStruct")
            ),
            "results_first_post_date": self._extract_date(
                status.get("resultsFirstPostDateStruct")
            ),
            "last_update_post_date": self._extract_date(
                status.get("lastUpdatePostDateStruct")
            ),
            "why_stopped": status.get("whyStopped"),
            "phase": design.get("phases", []),
            "study_type": design.get("studyType"),
            "design": {
                "allocation": (design.get("designInfo") or {}).get("allocation"),
                "intervention_model": (design.get("designInfo") or {}).get(
                    "interventionModel"
                ),
                "intervention_model_description": (design.get("designInfo") or {}).get(
                    "interventionModelDescription"
                ),
            },
            "enrollment": {
                "count": (design.get("enrollmentInfo") or {}).get("count"),
                "type": (design.get("enrollmentInfo") or {}).get("type"),
            },
            "conditions": conditions,
            "interventions": self._extract_interventions(arms.get("interventions", [])),
            "arms": self._extract_arm_groups(arms.get("armGroups", [])),
            "primary_outcomes": self._extract_outcomes(
                outcomes.get("primaryOutcomes", [])
            ),
            "secondary_outcomes": self._extract_outcomes(
                outcomes.get("secondaryOutcomes", [])
            ),
            "eligibility": {
                "criteria": eligibility.get("eligibilityCriteria"),
                "sex": eligibility.get("sex"),
                "min_age": eligibility.get("minimumAge"),
                "max_age": eligibility.get("maximumAge"),
                "healthy_volunteers": eligibility.get("healthyVolunteers"),
            },
            "sponsors": {
                "lead": sponsors.get("leadSponsor"),
                "collaborators": sponsors.get("collaborators", []),
                "overall_officials": contacts.get("overallOfficials", []),
            },
            "locations": self._extract_locations(contacts.get("locations", [])),
            "has_results": bool(study.get("hasResults")),
        }

        return normalized

    def _extract_outcomes(
        self, outcomes: Iterable[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return [
            {
                "measure": outcome.get("measure"),
                "description": outcome.get("description"),
                "time_frame": outcome.get("timeFrame"),
            }
            for outcome in outcomes or []
        ]

    def _extract_interventions(
        self, interventions: Iterable[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return [
            {
                "name": intervention.get("name"),
                "type": intervention.get("type"),
                "description": intervention.get("description"),
                "arm_labels": intervention.get("armGroupLabels", []),
                "other_names": intervention.get("otherNames", []),
            }
            for intervention in interventions or []
        ]

    def _extract_arm_groups(
        self, arm_groups: Iterable[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return [
            {
                "label": arm.get("label"),
                "type": arm.get("type"),
                "description": arm.get("description"),
                "interventions": arm.get("interventionNames", []),
            }
            for arm in arm_groups or []
        ]

    def _extract_locations(
        self, locations: Iterable[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return [
            {
                "facility": loc.get("facility"),
                "city": loc.get("city"),
                "state": loc.get("state"),
                "country": loc.get("country"),
                "status": loc.get("status"),
                "zip": loc.get("zip"),
                "geo": {
                    "lat": loc.get("geoPoint", {}).get("lat"),
                    "lon": loc.get("geoPoint", {}).get("lon"),
                }
                if loc.get("geoPoint")
                else None,
            }
            for loc in locations or []
        ]

    def _extract_date(self, date_struct: Optional[Dict[str, Any]]) -> Optional[str]:
        if not date_struct:
            return None
        # date_struct may include partial dates; preserve string to avoid losing fidelity
        return date_struct.get("date")

    def _summarize_trials(self, trials: List[Dict[str, Any]]) -> Dict[str, Any]:
        phases = Counter()
        statuses = Counter()
        sponsors = Counter()
        countries = Counter()
        enrollment_counts: List[int] = []

        for trial in trials:
            for phase in trial.get("phase") or []:
                phases[phase] += 1
            status = trial.get("overall_status")
            if status:
                statuses[status] += 1
            lead = (trial.get("sponsors") or {}).get("lead") or {}
            lead_name = lead.get("name") if isinstance(lead, dict) else None
            if lead_name:
                sponsors[lead_name] += 1
            for loc in trial.get("locations") or []:
                if loc.get("country"):
                    countries[loc["country"]] += 1
            enrollment = trial.get("enrollment", {}).get("count")
            if isinstance(enrollment, int):
                enrollment_counts.append(enrollment)

        def _counter_to_list(counter: Counter) -> List[Dict[str, Any]]:
            return [
                {"name": name, "count": count} for name, count in counter.most_common()
            ]

        return {
            "phase_distribution": _counter_to_list(phases),
            "status_distribution": _counter_to_list(statuses),
            "sponsor_counts": _counter_to_list(sponsors),
            "location_counts": _counter_to_list(countries),
            "enrollment": {
                "counted_trials": len(enrollment_counts),
                "total_enrollment": sum(enrollment_counts)
                if enrollment_counts
                else None,
                "median_enrollment": self._median(enrollment_counts)
                if enrollment_counts
                else None,
            },
        }

    def _median(self, values: List[int]) -> Optional[float]:
        if not values:
            return None
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        mid = n // 2
        if n % 2 == 1:
            return float(sorted_vals[mid])
        return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2


__all__ = [
    "ClinicalTrialsGovClient",
    "SUMMARY_FIELDS",
    "RESULT_FIELDS",
    "DEFAULT_BASE_URL",
]
