from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QuotaTracker:
    calls: dict[str, int] = field(default_factory=dict)
    units: dict[str, int] = field(default_factory=dict)

    def track(self, method: str, cost: int) -> None:
        self.calls[method] = self.calls.get(method, 0) + 1
        self.units[method] = self.units.get(method, 0) + cost

    def summary(self) -> dict[str, object]:
        by_method: dict[str, dict[str, int]] = {}
        for method, call_count in self.calls.items():
            by_method[method] = {
                "calls": call_count,
                "units": self.units.get(method, 0),
            }

        return {
            "total_calls": sum(self.calls.values()),
            "estimated_units": sum(self.units.values()),
            "by_method": by_method,
        }
