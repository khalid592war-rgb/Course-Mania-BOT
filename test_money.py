from decimal import Decimal
from app.money import split_sale, available_credit


def test_split_200():
    assert split_sale(Decimal("200")) == (Decimal("100.00"), Decimal("100.00"))


def test_split_odd_sums_exactly():
    o, r = split_sale(Decimal("99.99"))
    assert o + r == Decimal("99.99")


def test_available_credit_never_negative():
    assert available_credit(Decimal("1000"), Decimal("1200")) == Decimal("0")
    assert available_credit(Decimal("1000"), Decimal("100")) == Decimal("900")
