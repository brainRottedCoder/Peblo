from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Artwork, Episode, Show
from app.reference import SECTIONS
from app.schemas import ValidationIssue, ValidationReport


def build_validation_report(db: Session) -> ValidationReport:
    shows = db.scalars(select(Show).options(selectinload(Show.artwork), selectinload(Show.seasons))).all()
    episodes = db.scalars(
        select(Episode).options(selectinload(Episode.artwork), selectinload(Episode.show))
    ).all()

    blocking: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    # --- published show without a section ---
    for show in shows:
        if show.status == "published" and not show.section:
            blocking.append(
                ValidationIssue(
                    severity="error",
                    code="show_published_no_section",
                    message=f"“{show.title}” is published but has no section.",
                    how_to_fix="Open the show and pick Featured, Series, Minisodes, or Songs, then save.",
                    show_id=show.id,
                    show_title=show.title,
                )
            )
        elif show.status == "published" and show.section not in SECTIONS:
            blocking.append(
                ValidationIssue(
                    severity="error",
                    code="show_unknown_section",
                    message=f"“{show.title}” uses section “{show.section}”, which isn’t one of the allowed homes.",
                    how_to_fix="Change the section to Featured, Series, Minisodes, or Songs.",
                    show_id=show.id,
                    show_title=show.title,
                )
            )

        show_kinds = {a.kind for a in show.artwork}
        if show.status == "published":
            for kind in ("poster", "banner"):
                if kind not in show_kinds:
                    warnings.append(
                        ValidationIssue(
                            severity="warning",
                            code=f"show_missing_{kind}",
                            message=f"“{show.title}” is missing a {kind}. The browse page will look incomplete.",
                            how_to_fix=f"Upload a {kind} on the show page.",
                            show_id=show.id,
                            show_title=show.title,
                        )
                    )

    # --- published episode rules ---
    for ep in episodes:
        if ep.status != "published":
            continue
        if ep.duration_seconds is None or ep.duration_seconds <= 0:
            blocking.append(
                ValidationIssue(
                    severity="error",
                    code="episode_published_no_duration",
                    message=f"“{ep.title}” is published but has no duration.",
                    how_to_fix="Add the running time in seconds (or minutes converted to seconds) and save.",
                    show_id=ep.show_id,
                    show_title=ep.show.title if ep.show else None,
                    episode_id=ep.id,
                    episode_title=ep.title,
                )
            )
        if not ep.artwork:
            blocking.append(
                ValidationIssue(
                    severity="error",
                    code="episode_published_no_artwork",
                    message=f"“{ep.title}” is published but has no pictures.",
                    how_to_fix="Upload at least a thumbnail (640×360). A poster and banner are even better.",
                    show_id=ep.show_id,
                    show_title=ep.show.title if ep.show else None,
                    episode_id=ep.id,
                    episode_title=ep.title,
                )
            )
        elif {a.kind for a in ep.artwork} < {"poster", "banner", "thumbnail"}:
            missing = {"poster", "banner", "thumbnail"} - {a.kind for a in ep.artwork}
            warnings.append(
                ValidationIssue(
                    severity="warning",
                    code="episode_incomplete_artwork",
                    message=f"“{ep.title}” is missing {', '.join(sorted(missing))}.",
                    how_to_fix="Upload the missing picture sizes so every screen has the right crop.",
                    show_id=ep.show_id,
                    show_title=ep.show.title if ep.show else None,
                    episode_id=ep.id,
                    episode_title=ep.title,
                )
            )

    # --- duplicate (content_group, language) among published rows ---
    groups: dict[tuple[str, str], list[Episode]] = defaultdict(list)
    for ep in episodes:
        if ep.status == "published":
            groups[(ep.content_group, ep.language)].append(ep)
    for (group, lang), rows in groups.items():
        if len(rows) > 1:
            titles = ", ".join(f"“{r.title}”" for r in rows)
            lang_label = "English" if lang == "en" else "Hindi" if lang == "hi" else lang
            blocking.append(
                ValidationIssue(
                    severity="error",
                    code="duplicate_content_group_language",
                    message=(
                        f"{titles} are both published as the {lang_label} version of the same episode "
                        f"(content group “{group}”)."
                    ),
                    how_to_fix=(
                        "Keep one and unpublish or retitle the other. "
                        "Language versions of one episode should share a content group — "
                        "but each language only once."
                    ),
                    show_id=rows[0].show_id,
                    show_title=rows[0].show.title if rows[0].show else None,
                    episode_id=rows[0].id,
                    episode_title=rows[0].title,
                )
            )

    # Quality nits (never block)
    for ep in episodes:
        if ep.title and ep.title != ep.title.strip():
            warnings.append(
                ValidationIssue(
                    severity="warning",
                    code="title_whitespace",
                    message=f"“{ep.title}” has extra spaces in the title.",
                    how_to_fix="Trim the title so it displays cleanly.",
                    show_id=ep.show_id,
                    episode_id=ep.id,
                    episode_title=ep.title,
                )
            )
        if ep.title and ep.title[:1].islower():
            warnings.append(
                ValidationIssue(
                    severity="warning",
                    code="title_lowercase",
                    message=f"“{ep.title}” starts with a lowercase letter.",
                    how_to_fix="Capitalise the title the way it should appear on the TV.",
                    show_id=ep.show_id,
                    show_title=ep.show.title if ep.show else None,
                    episode_id=ep.id,
                    episode_title=ep.title,
                )
            )

    grouped: dict[str, list[ValidationIssue]] = defaultdict(list)
    for issue in blocking + warnings:
        grouped[issue.code].append(issue)

    return ValidationReport(
        can_publish=len(blocking) == 0,
        blocking=blocking,
        warnings=warnings,
        groups=dict(grouped),
    )


def artwork_map(items: list[Artwork], storage_url) -> dict[str, str]:
    return {a.kind: storage_url(a.storage_key) for a in items}
