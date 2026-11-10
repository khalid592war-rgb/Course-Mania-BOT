"""Money policy: Decimal only, 2 places. Owner share rounds HALF_UP;
reseller share = price - owner share, so the two always sum exactly."""
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def q(x: Decimal) -> Decimal:
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def split_sale(price: Decimal) -> tuple[Decimal, Decimal]:
    owner = q(price * Decimal("0.50"))
    return owner, q(price) - owner


def available_credit(limit: Decimal, outstanding: Decimal) -> Decimal:
    return max(Decimal("0"), limit - outstanding)
