"""
Analytics Routes
Handles historical analysis, anomaly detection, and reporting
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta
import os

from api.v1.routes.auth import get_current_active_user, User
from core.logger import app_logger

# Import analytics logic
try:
    from services.analytics import AnalyticsEngine

    analytics_engine = AnalyticsEngine()
except ImportError:
    analytics_engine = None
    app_logger.warning("analytics_module_not_available")

router = APIRouter()


# Models
class DashboardStats(BaseModel):
    total_incidents: int
    active_alerts: int
    resolved_incidents: int
    average_response_time_minutes: float
    threat_level: str
    daily_incidents: List[dict]
    incidents_by_type: dict


class AnomalyDetection(BaseModel):
    timestamp: datetime
    metric: str
    value: float
    anomaly_score: float
    is_anomaly: bool


class AnomalyResponse(BaseModel):
    detected: int
    anomalies: List[AnomalyDetection]
    model: str
    contamination: float


class TrendData(BaseModel):
    date: str
    value: float
    moving_average: Optional[float] = None


class TrendResponse(BaseModel):
    metric: str
    period: str
    data: List[TrendData]
    trend: str  # increasing, decreasing, stable


class ExportRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metrics: List[str] = ["threats", "incidents", "alerts"]
    format: str = "excel"  # excel, csv


# Routes
@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(current_user: User = Depends(get_current_active_user)):
    """
    Get dashboard statistics overview

    Returns key metrics for the main dashboard
    """
    try:
        # TODO: Get real data from database
        stats = {
            "total_incidents": 1247,
            "active_alerts": 3,
            "resolved_incidents": 1198,
            "average_response_time_minutes": 4.2,
            "threat_level": "low",
            "daily_incidents": [
                {"date": "01/01/2026", "count": 12},
                {"date": "02/01/2026", "count": 8},
                {"date": "03/01/2026", "count": 15},
                {"date": "04/01/2026", "count": 7},
            ],
            "incidents_by_type": {
                "weapon": 45,
                "suspicious_package": 23,
                "unauthorized_access": 18,
                "crowd_density": 10,
            },
        }

        app_logger.info("dashboard_stats_retrieved", user=current_user.username)

        return DashboardStats(**stats)

    except Exception as e:
        app_logger.error("dashboard_stats_error", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get dashboard stats: {str(e)}"
        )


@router.get("/anomalies", response_model=AnomalyResponse)
async def detect_anomalies(
    metric: str = "threat_count",
    days: int = 30,
    current_user: User = Depends(get_current_active_user),
):
    """
    Detect anomalies in historical data using Isolation Forest

    Query Parameters:
    - metric: Metric to analyze (threat_count, response_time, crowd_density)
    - days: Number of days to analyze (default: 30)
    """
    if not analytics_engine:
        # Return mock anomaly data
        return AnomalyResponse(
            detected=2,
            anomalies=[
                AnomalyDetection(
                    timestamp=datetime.now() - timedelta(days=5),
                    metric=metric,
                    value=85.0,
                    anomaly_score=0.92,
                    is_anomaly=True,
                ),
                AnomalyDetection(
                    timestamp=datetime.now() - timedelta(days=12),
                    metric=metric,
                    value=72.0,
                    anomaly_score=0.78,
                    is_anomaly=True,
                ),
            ],
            model="IsolationForest",
            contamination=0.1,
        )

    try:
        app_logger.info(
            "anomaly_detection_started",
            user=current_user.username,
            metric=metric,
            days=days,
        )

        # Load historical data
        analytics_engine.load_historical_data()

        # Detect anomalies
        anomalies_df = analytics_engine.detect_anomalies(
            metric=metric, contamination=0.1
        )

        # Format response
        anomalies = []
        if anomalies_df is not None and not anomalies_df.empty:
            for _, row in anomalies_df.iterrows():
                anomalies.append(
                    AnomalyDetection(
                        timestamp=row.get("timestamp", datetime.now()),
                        metric=metric,
                        value=row.get("value", 0.0),
                        anomaly_score=row.get("anomaly_score", 0.0),
                        is_anomaly=row.get("is_anomaly", False),
                    )
                )

        app_logger.info(
            "anomaly_detection_complete",
            anomalies_found=len([a for a in anomalies if a.is_anomaly]),
        )

        return AnomalyResponse(
            detected=len([a for a in anomalies if a.is_anomaly]),
            anomalies=anomalies,
            model="IsolationForest",
            contamination=0.1,
        )

    except Exception as e:
        app_logger.error("anomaly_detection_error", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Anomaly detection failed: {str(e)}"
        )


@router.get("/trends", response_model=TrendResponse)
async def get_trends(
    metric: str = "threat_count",
    period: str = "7d",
    current_user: User = Depends(get_current_active_user),
):
    """
    Get trend analysis with moving averages

    Query Parameters:
    - metric: Metric to analyze (threat_count, response_time, crowd_density)
    - period: Time period (7d, 30d, 90d)
    """
    if not analytics_engine:
        # Return mock trend data
        days_map = {"7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(period, 7)

        data = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
            value = 10 + i * 0.5 + (i % 3) * 2
            moving_avg = 10 + i * 0.4
            data.append(TrendData(date=date, value=value, moving_average=moving_avg))

        return TrendResponse(metric=metric, period=period, data=data, trend="stable")

    try:
        # Parse period
        days_map = {"7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(period, 7)

        app_logger.info(
            "trend_analysis_started",
            user=current_user.username,
            metric=metric,
            period=period,
        )

        # Generate trend analysis
        trend_plot = analytics_engine.generate_trend_analysis(metric=metric, days=days)

        # TODO: Extract data from plot and format response
        # For now, return dummy data
        data = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=days - i)).strftime("%Y-%m-%d")
            data.append(TrendData(date=date, value=10 + i * 0.5, moving_average=10.0))

        return TrendResponse(metric=metric, period=period, data=data, trend="stable")

    except Exception as e:
        app_logger.error("trend_analysis_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


@router.get("/heatmap")
async def get_heatmap(
    metric: str = "threat_density",
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate heatmap visualization data

    Query Parameters:
    - metric: Metric to visualize (threat_density, crowd_density, response_time)
    """
    if not analytics_engine:
        # Return mock heatmap data
        import json

        mock_heatmap = {
            "data": [
                {
                    "type": "heatmap",
                    "z": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
                    "x": ["Zone A", "Zone B", "Zone C"],
                    "y": ["Morning", "Afternoon", "Evening"],
                }
            ],
            "layout": {"title": f"{metric} Heatmap"},
        }
        return {"plot_json": json.dumps(mock_heatmap)}

    try:
        app_logger.info(
            "heatmap_generation_started", user=current_user.username, metric=metric
        )

        # Generate heatmap
        heatmap_plot = analytics_engine.generate_heatmap(metric=metric)

        # Return plot as JSON (Plotly format)
        if heatmap_plot:
            return {"plot_json": heatmap_plot.to_json()}
        else:
            return {"message": "No data available for heatmap"}

    except Exception as e:
        app_logger.error("heatmap_generation_error", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Heatmap generation failed: {str(e)}"
        )


@router.post("/export")
async def export_report(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
):
    """
    Export analytics report to Excel or CSV

    Request Body:
    - start_date: Start date for report (optional)
    - end_date: End date for report (optional)
    - metrics: List of metrics to include
    - format: Export format (excel, csv)
    """
    if not analytics_engine:
        # Return mock file when analytics engine is unavailable
        import csv
        from io import StringIO

        app_logger.info(
            "report_export_mock",
            user=current_user.username,
            format=request.format,
            metrics=request.metrics,
        )

        # Generate mock CSV data
        output = StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow(
            [
                "Date",
                "Threats Detected",
                "Alerts Sent",
                "Response Time (s)",
                "Crowd Density",
            ]
        )

        # Write sample data
        for i in range(30):
            date = (datetime.now() - timedelta(days=29 - i)).strftime("%Y-%m-%d")
            writer.writerow([date, 10 + i, 5 + i // 2, 2.5, 75 + i])

        # Create file
        filename = f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = f"/tmp/{filename}"

        with open(filepath, "w") as f:
            f.write(output.getvalue())

        # Schedule cleanup
        def cleanup_file():
            try:
                os.remove(filepath)
            except Exception:
                pass

        background_tasks.add_task(cleanup_file)

        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="text/csv",
        )

    try:
        app_logger.info(
            "report_export_started",
            user=current_user.username,
            format=request.format,
            metrics=request.metrics,
        )

        # Set default dates
        start_date = request.start_date or (datetime.now() - timedelta(days=30))
        end_date = request.end_date or datetime.now()

        # Generate filename
        filename = f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = f"/tmp/{filename}"

        # Export to Excel
        analytics_engine.export_to_excel(
            filename=filepath, start_date=start_date, end_date=end_date
        )

        # Schedule file cleanup after sending
        def cleanup_file():
            try:
                os.remove(filepath)
            except Exception as e:
                app_logger.error("file_cleanup_error", file=filepath, error=str(e))

        background_tasks.add_task(cleanup_file)

        app_logger.info("report_export_complete", filename=filename)

        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except Exception as e:
        app_logger.error("report_export_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Report export failed: {str(e)}")


@router.get("/comparative")
async def comparative_analysis(
    metric: str = "threat_count",
    days1: int = 7,
    days2: int = 30,
    current_user: User = Depends(get_current_active_user),
):
    """
    Compare metrics across different time periods

    Query Parameters:
    - metric: Metric to compare
    - days1: First period duration (days)
    - days2: Second period duration (days)
    """
    if not analytics_engine:
        # Return mock comparative data
        return {
            "metric": metric,
            "period1": {
                "days": days1,
                "average": 42.5,
                "max": 75.0,
                "min": 15.0,
                "total_incidents": 18,
            },
            "period2": {
                "days": days2,
                "average": 38.2,
                "max": 68.0,
                "min": 12.0,
                "total_incidents": 45,
            },
            "change_percentage": 11.3,
            "trend": "increasing",
            "recommendation": "Threat levels have increased by 11.3% compared to the previous period. Consider increasing surveillance.",
        }

    try:
        app_logger.info(
            "comparative_analysis_started", user=current_user.username, metric=metric
        )

        comparison = analytics_engine.comparative_analysis(
            metric=metric, days1=days1, days2=days2
        )

        return comparison

    except Exception as e:
        app_logger.error("comparative_analysis_error", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Comparative analysis failed: {str(e)}"
        )


@router.get("/predictions")
async def get_predictions(
    metric: str = "threat_count",
    hours_ahead: int = 24,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get predictive insights for future trends

    Query Parameters:
    - metric: Metric to predict
    - hours_ahead: Prediction horizon (hours)
    """
    if not analytics_engine:
        # Return mock prediction data
        predictions = []
        for i in range(hours_ahead):
            predictions.append(
                {
                    "timestamp": (datetime.now() + timedelta(hours=i + 1)).isoformat(),
                    "predicted_value": 25.0 + i * 1.5 + (i % 4) * 2,
                    "confidence_lower": 20.0 + i * 1.2,
                    "confidence_upper": 30.0 + i * 1.8,
                }
            )

        return {
            "metric": metric,
            "predictions": predictions,
            "model_confidence": 0.85,
            "recommendation": "Based on historical patterns, expect moderate activity levels in the next 24 hours.",
        }

    try:
        app_logger.info(
            "predictions_started",
            user=current_user.username,
            metric=metric,
            hours_ahead=hours_ahead,
        )

        insights = analytics_engine.get_predictive_insights(
            metric=metric, hours_ahead=hours_ahead
        )

        return insights

    except Exception as e:
        app_logger.error("predictions_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Predictions failed: {str(e)}")
