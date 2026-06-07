"""RSU planning defaults shared across workflow nodes."""

DEFAULT_RSU_GROWTH_RATE = 0.10


def get_rsu_growth_rate(investment_details: dict) -> float:
    """Annual share-price growth for RSU vesting projections (decimal, e.g. 0.10)."""
    return float(
        investment_details.get("rsu_growth_rate", DEFAULT_RSU_GROWTH_RATE)
    )
