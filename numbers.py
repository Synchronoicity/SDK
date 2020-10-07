from decimal import Decimal

default_precision = 6


def round_decimal(decimalObj: Decimal, num_of_places: int = 6) -> Decimal:
    return decimalObj.quantize(Decimal(10) ** -num_of_places).normalize()


def chunks(l, n):
    """Yield n number of sequential chunks from l."""
    d, r = divmod(len(l), n)
    for i in range(n):
        si = (d+1)*(i if i < r else r) + d*(0 if i < r else i - r)
        yield l[si:si+(d+1 if i < r else d)]