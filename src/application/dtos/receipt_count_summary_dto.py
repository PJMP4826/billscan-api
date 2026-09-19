from dataclasses import dataclass


@dataclass(frozen=True)
class ReceiptCountSummary:
    total: int
    billable: int
    non_billable: int

    def to_dict(self) -> dict[str, str]:
        return {
            "total": str(self.total),
            "facturables": str(self.billable),
            "no_facturables": str(self.non_billable),
        }
