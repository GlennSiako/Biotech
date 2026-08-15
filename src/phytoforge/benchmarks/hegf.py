"""Curated design library for the first hEGF benchmark."""

from __future__ import annotations

from phytoforge.domain import Design


BENCHMARK_ID = "hegf-nb-transient-v0"
CALIBRATION_TIER = "S0"


def design_library() -> tuple[Design, ...]:
    """Return the bounded, versioned hEGF design library.

    The categories reconstruct study-level comparisons without encoding or
    generating nucleotide sequences.
    """

    return (
        _design("tw-apoplast-base", "thomas_2014_like", "apoplast", harvest=13),
        _design("tw-er-base", "thomas_2014_like", "er", harvest=13),
        _design("tw-vacuole-base", "thomas_2014_like", "vacuole", harvest=13),
        _design(
            "tw-vacuole-coding",
            "thomas_2014_like",
            "vacuole",
            coding=True,
            harvest=13,
        ),
        _design(
            "tw-vacuole-suppressed",
            "thomas_2014_like",
            "vacuole",
            suppressor=True,
            harvest=13,
        ),
        _design(
            "tw-vacuole-optimized",
            "thomas_2014_like",
            "vacuole",
            coding=True,
            suppressor=True,
            intensity="high",
            harvest=13,
        ),
        _design(
            "tw-vacuole-age4",
            "thomas_2014_like",
            "vacuole",
            coding=True,
            suppressor=True,
            age=4,
            harvest=13,
        ),
        _design(
            "tw-vacuole-age6",
            "thomas_2014_like",
            "vacuole",
            coding=True,
            suppressor=True,
            age=6,
            harvest=13,
        ),
        _design(
            "h20-apoplast-c-tag",
            "hanittinan_2020_like",
            "apoplast",
            coding=True,
            tag="c_terminal",
            harvest=4,
        ),
        _design(
            "h20-er-c-tag",
            "hanittinan_2020_like",
            "er",
            coding=True,
            tag="c_terminal",
            harvest=4,
        ),
        _design(
            "h20-apoplast-n-tag",
            "hanittinan_2020_like",
            "apoplast",
            coding=True,
            tag="n_terminal",
            harvest=4,
        ),
        _design(
            "h20-er-n-tag",
            "hanittinan_2020_like",
            "er",
            coding=True,
            tag="n_terminal",
            harvest=4,
        ),
        _design(
            "h20-cytosol-c-tag",
            "hanittinan_2020_like",
            "cytosol",
            coding=True,
            tag="c_terminal",
            harvest=4,
        ),
        _design(
            "h20-cytosol-n-tag",
            "hanittinan_2020_like",
            "cytosol",
            coding=True,
            tag="n_terminal",
            harvest=4,
        ),
        _design(
            "h20-er-c-tag-day2",
            "hanittinan_2020_like",
            "er",
            coding=True,
            tag="c_terminal",
            harvest=2,
        ),
        _design(
            "h20-er-c-tag-day6",
            "hanittinan_2020_like",
            "er",
            coding=True,
            tag="c_terminal",
            harvest=6,
        ),
    )


def evidence_for(design: Design) -> tuple[str, ...]:
    """Return evidence claims relevant to a design's study context."""

    if design.study_context == "thomas_2014_like":
        claims = [
            "tw2014_localization_vacuole",
            "tw2014_plant_age_five_week",
        ]
        if design.coding_adapted:
            claims.append("tw2014_codon_vacuole_34pct")
        if design.silencing_suppression:
            claims.append("tw2014_p19_over_threefold")
        return tuple(claims)

    claims = [
        "h2020_er_c_terminal_best",
        "h2020_harvest_observation_window",
    ]
    if design.tag_position != "none":
        claims.append("h2020_affinity_capture")
    return tuple(claims)


def _design(
    design_id: str,
    context: str,
    localization: str,
    *,
    coding: bool = False,
    suppressor: bool = False,
    tag: str = "none",
    intensity: str = "medium",
    age: int = 5,
    harvest: int,
) -> Design:
    return Design(
        design_id=design_id,
        study_context=context,
        localization=localization,
        coding_adapted=coding,
        silencing_suppression=suppressor,
        tag_position=tag,
        expression_intensity=intensity,
        plant_age_weeks=age,
        harvest_day=harvest,
    )
