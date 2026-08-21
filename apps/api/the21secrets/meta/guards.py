"""Version-independent guard against Meta API restrictions that no
operational mode or approval can override — these aren't safety-ceiling
choices, they're Meta rejecting the call outright. Confirmed in
docs/research/repository-audit.md: Advantage+ Shopping and Advantage+ App
campaigns can't be created or updated via the Marketing API at all, in force
since 2026-05-19 across every API version. There's no partial support to
special-case, so this rejects unconditionally rather than trying to guess
which fields would trigger Meta's own block."""

_BLOCKED_SMART_PROMOTION_TYPES = {"AUTOMATED_SHOPPING_ADS", "SMART_APP_PROMOTION"}


class AdvantagePlusNotSupported(ValueError):
    pass


def check_not_advantage_plus(smart_promotion_type: str | None) -> None:
    if smart_promotion_type and smart_promotion_type.upper() in _BLOCKED_SMART_PROMOTION_TYPES:
        raise AdvantagePlusNotSupported(
            f"'{smart_promotion_type}' campaigns (Advantage+ Shopping/App) can't be created or "
            "updated via the Marketing API — Meta blocked this entirely as of 2026-05-19. "
            "Use Ads Manager directly for this campaign type."
        )
