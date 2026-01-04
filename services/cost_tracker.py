"""
API Cost Tracking and Optimization
Monitors spending across AI providers and optimizes usage
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
from pathlib import Path

from core.config import settings
from core.logger import app_logger, audit_logger


@dataclass
class APICall:
    """Record of a single API call"""

    timestamp: datetime
    provider: str  # openai, gemini, anthropic
    model: str
    tokens_input: int
    tokens_output: int
    cost_usd: float
    response_time_ms: float
    user_id: str


class CostTracker:
    """Tracks and optimizes API costs"""

    def __init__(self):
        self.calls: List[APICall] = []
        self.cost_file = Path("./logs/api_costs.json")
        self.cost_file.parent.mkdir(exist_ok=True)

        # Load historical costs
        self._load_costs()

    def _load_costs(self):
        """Load historical cost data"""
        if self.cost_file.exists():
            try:
                with open(self.cost_file, "r") as f:
                    data = json.load(f)
                    self.calls = [
                        APICall(
                            **{
                                **call,
                                "timestamp": datetime.fromisoformat(call["timestamp"]),
                            }
                        )
                        for call in data
                    ]
                app_logger.info("cost_history_loaded", records=len(self.calls))
            except Exception as e:
                app_logger.error("cost_history_load_failed", error=str(e))

    def _save_costs(self):
        """Save cost data to file"""
        try:
            data = [
                {**asdict(call), "timestamp": call.timestamp.isoformat()}
                for call in self.calls
            ]
            with open(self.cost_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            app_logger.error("cost_history_save_failed", error=str(e))

    def calculate_cost(
        self, provider: str, model: str, tokens_input: int, tokens_output: int
    ) -> float:
        """Calculate cost for an API call"""
        total_tokens = tokens_input + tokens_output

        if provider == "openai":
            cost_per_1k = settings.cost_tracking.openai_cost_per_1k_tokens
        elif provider == "anthropic":
            cost_per_1k = settings.cost_tracking.anthropic_cost_per_1k_tokens
        elif provider == "gemini":
            cost_per_1k = settings.cost_tracking.gemini_cost_per_1k_tokens
        else:
            cost_per_1k = 0.001  # default

        return (total_tokens / 1000) * cost_per_1k

    def record_call(
        self,
        provider: str,
        model: str,
        tokens_input: int,
        tokens_output: int,
        response_time_ms: float,
        user_id: str = "default",
    ):
        """Record an API call"""
        cost = self.calculate_cost(provider, model, tokens_input, tokens_output)

        call = APICall(
            timestamp=datetime.now(),
            provider=provider,
            model=model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_usd=cost,
            response_time_ms=response_time_ms,
            user_id=user_id,
        )

        self.calls.append(call)
        self._save_costs()

        # Audit log
        audit_logger.log_api_call(
            provider=provider,
            model=model,
            tokens_used=tokens_input + tokens_output,
            cost_usd=cost,
            response_time_ms=response_time_ms,
        )

        # Check if approaching budget limit
        daily_cost = self.get_daily_cost()
        budget = settings.cost_tracking.daily_budget_usd
        threshold = budget * (settings.cost_tracking.alert_threshold_percent / 100)

        if daily_cost >= threshold:
            app_logger.warning(
                "daily_budget_threshold_reached",
                daily_cost=daily_cost,
                budget=budget,
                percent=int((daily_cost / budget) * 100),
            )

    def get_daily_cost(self, date: Optional[datetime] = None) -> float:
        """Get total cost for a specific day"""
        if date is None:
            date = datetime.now()

        start_of_day = datetime(date.year, date.month, date.day)
        end_of_day = start_of_day + timedelta(days=1)

        return sum(
            call.cost_usd
            for call in self.calls
            if start_of_day <= call.timestamp < end_of_day
        )

    def get_monthly_cost(self, year: int, month: int) -> float:
        """Get total cost for a specific month"""
        return sum(
            call.cost_usd
            for call in self.calls
            if call.timestamp.year == year and call.timestamp.month == month
        )

    def get_cost_by_provider(self, days: int = 30) -> Dict[str, float]:
        """Get cost breakdown by provider"""
        cutoff = datetime.now() - timedelta(days=days)

        costs = {}
        for call in self.calls:
            if call.timestamp >= cutoff:
                costs[call.provider] = costs.get(call.provider, 0) + call.cost_usd

        return costs

    def get_cost_by_user(self, days: int = 30) -> Dict[str, float]:
        """Get cost breakdown by user"""
        cutoff = datetime.now() - timedelta(days=days)

        costs = {}
        for call in self.calls:
            if call.timestamp >= cutoff:
                costs[call.user_id] = costs.get(call.user_id, 0) + call.cost_usd

        return costs

    def should_downgrade_model(self, user_id: str) -> bool:
        """Determine if model should be downgraded to save costs"""
        if not settings.cost_tracking.enable_auto_downgrade:
            return False

        daily_cost = self.get_daily_cost()
        budget = settings.cost_tracking.daily_budget_usd

        # Downgrade if 90% of budget used
        return daily_cost >= (budget * 0.9)

    def get_statistics(self, days: int = 7) -> Dict:
        """Get comprehensive cost statistics"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_calls = [call for call in self.calls if call.timestamp >= cutoff]

        if not recent_calls:
            return {
                "total_calls": 0,
                "total_cost": 0,
                "avg_cost_per_call": 0,
                "total_tokens": 0,
                "avg_response_time_ms": 0,
            }

        total_cost = sum(call.cost_usd for call in recent_calls)
        total_tokens = sum(
            call.tokens_input + call.tokens_output for call in recent_calls
        )
        avg_response_time = sum(call.response_time_ms for call in recent_calls) / len(
            recent_calls
        )

        return {
            "total_calls": len(recent_calls),
            "total_cost": round(total_cost, 4),
            "avg_cost_per_call": round(total_cost / len(recent_calls), 4),
            "total_tokens": total_tokens,
            "avg_response_time_ms": round(avg_response_time, 2),
            "cost_by_provider": self.get_cost_by_provider(days),
            "daily_budget": settings.cost_tracking.daily_budget_usd,
            "budget_used_percent": round(
                (self.get_daily_cost() / settings.cost_tracking.daily_budget_usd) * 100,
                1,
            ),
        }


# Global cost tracker instance
cost_tracker = CostTracker()
