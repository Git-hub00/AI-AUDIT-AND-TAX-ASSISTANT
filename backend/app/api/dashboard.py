from fastapi import APIRouter, Depends
from app.core.security import verify_token
from app.core.database import get_database
from bson import ObjectId
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(
    current_user: dict = Depends(verify_token),
    db = Depends(get_database)
):
    """Get dashboard statistics for user"""
    
    user_id = ObjectId(current_user["user_id"])
    
    # Get document counts
    total_documents = await db.documents.count_documents({"user_id": user_id})
    processed_documents = await db.documents.count_documents({
        "user_id": user_id,
        "status": "done"
    })
    
    # Get transaction counts
    total_transactions = await db.transactions.count_documents({"user_id": user_id})
    
    # Get tax record counts
    total_tax_records = await db.tax_records.count_documents({"user_id": user_id})
    
    # Get anomaly report counts
    total_anomaly_reports = await db.anomaly_reports.count_documents({"user_id": user_id})
    
    # Get recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    recent_documents = await db.documents.count_documents({
        "user_id": user_id,
        "uploaded_at": {"$gte": thirty_days_ago}
    })
    
    recent_tax_records = await db.tax_records.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": thirty_days_ago}
    })
    
    recent_anomaly_reports = await db.anomaly_reports.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": thirty_days_ago}
    })
    
    # Get high-risk transactions count
    high_risk_transactions = await db.transactions.count_documents({
        "user_id": user_id,
        "anomaly_score": {"$gte": 0.7}
    })
    
    # Get total amounts
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": None,
            "total_income": {"$sum": "$total_income"},
            "total_tax": {"$sum": "$predicted_tax"}
        }}
    ]
    
    tax_totals = await db.tax_records.aggregate(pipeline).to_list(1)
    total_income = tax_totals[0]["total_income"] if tax_totals else 0
    total_tax = tax_totals[0]["total_tax"] if tax_totals else 0
    
    # Get flagged amount from anomaly reports
    anomaly_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": None,
            "total_flagged": {"$sum": "$total_flagged_amount"}
        }}
    ]
    
    anomaly_totals = await db.anomaly_reports.aggregate(anomaly_pipeline).to_list(1)
    total_flagged_amount = anomaly_totals[0]["total_flagged"] if anomaly_totals else 0
    
    return {
        "documents": {
            "total": total_documents,
            "processed": processed_documents,
            "recent": recent_documents,
            "processing_rate": round((processed_documents / total_documents * 100) if total_documents > 0 else 0, 1)
        },
        "transactions": {
            "total": total_transactions,
            "high_risk": high_risk_transactions,
            "risk_rate": round((high_risk_transactions / total_transactions * 100) if total_transactions > 0 else 0, 1)
        },
        "tax_records": {
            "total": total_tax_records,
            "recent": recent_tax_records,
            "total_income": round(total_income, 2),
            "total_tax": round(total_tax, 2),
            "effective_rate": round((total_tax / total_income * 100) if total_income > 0 else 0, 2)
        },
        "anomaly_reports": {
            "total": total_anomaly_reports,
            "recent": recent_anomaly_reports,
            "total_flagged_amount": round(total_flagged_amount, 2)
        },
        "activity": {
            "documents_this_month": recent_documents,
            "tax_calculations_this_month": recent_tax_records,
            "anomaly_scans_this_month": recent_anomaly_reports
        }
    }

@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 10,
    current_user: dict = Depends(verify_token),
    db = Depends(get_database)
):
    """Get recent user activity"""
    
    user_id = ObjectId(current_user["user_id"])
    activities = []
    
    # Get recent documents
    recent_docs = await db.documents.find(
        {"user_id": user_id}
    ).sort("uploaded_at", -1).limit(5).to_list(5)
    
    for doc in recent_docs:
        activities.append({
            "type": "document_upload",
            "title": f"Uploaded {doc['filename']}",
            "timestamp": doc["uploaded_at"].isoformat() if isinstance(doc["uploaded_at"], datetime) else doc["uploaded_at"],
            "status": doc["status"],
            "id": str(doc["_id"])
        })
    
    # Get recent tax records
    recent_tax = await db.tax_records.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(3).to_list(3)
    
    for tax in recent_tax:
        activities.append({
            "type": "tax_calculation",
            "title": f"Tax calculated for {tax['fiscal_year']}",
            "timestamp": tax["created_at"].isoformat() if isinstance(tax["created_at"], datetime) else tax["created_at"],
            "amount": tax["predicted_tax"],
            "id": str(tax["_id"])
        })
    
    # Get recent anomaly reports
    recent_anomalies = await db.anomaly_reports.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(3).to_list(3)
    
    for anomaly in recent_anomalies:
        activities.append({
            "type": "anomaly_scan",
            "title": f"Anomaly scan completed",
            "timestamp": anomaly["created_at"].isoformat() if isinstance(anomaly["created_at"], datetime) else anomaly["created_at"],
            "anomalies_found": anomaly["anomalous_transactions"],
            "id": str(anomaly["_id"])
        })
    
    # Sort all activities by timestamp
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {
        "activities": activities[:limit],
        "total": len(activities)
    }

@router.get("/summary")
async def get_dashboard_summary(
    current_user: dict = Depends(verify_token),
    db = Depends(get_database)
):
    """Get dashboard summary for quick overview"""
    
    user_id = ObjectId(current_user["user_id"])
    
    # Get latest tax record
    latest_tax = await db.tax_records.find_one(
        {"user_id": user_id},
        sort=[("created_at", -1)]
    )
    
    # Get latest anomaly report
    latest_anomaly = await db.anomaly_reports.find_one(
        {"user_id": user_id},
        sort=[("created_at", -1)]
    )
    
    # Get document processing status
    pending_docs = await db.documents.count_documents({
        "user_id": user_id,
        "status": {"$in": ["uploaded", "processing"]}
    })
    
    return {
        "latest_tax_calculation": {
            "fiscal_year": latest_tax["fiscal_year"] if latest_tax else None,
            "predicted_tax": latest_tax["predicted_tax"] if latest_tax else 0,
            "calculated_at": latest_tax["created_at"].isoformat() if latest_tax and isinstance(latest_tax["created_at"], datetime) else None
        },
        "latest_anomaly_scan": {
            "anomalies_found": latest_anomaly["anomalous_transactions"] if latest_anomaly else 0,
            "anomaly_rate": latest_anomaly["anomaly_rate"] if latest_anomaly else 0,
            "scanned_at": latest_anomaly["created_at"].isoformat() if latest_anomaly and isinstance(latest_anomaly["created_at"], datetime) else None
        },
        "pending_processing": {
            "documents": pending_docs
        },
        "user_info": {
            "user_id": current_user["user_id"],
            "email": current_user.get("email", "")
        }
    }

@router.post("/create-sample-data")
async def create_sample_data(
    current_user: dict = Depends(verify_token),
    db = Depends(get_database)
):
    """Create sample data for new users"""
    
    try:
        from app.services.user_onboarding import user_onboarding
        await user_onboarding.create_sample_data_for_user(current_user["user_id"])
        
        return {
            "success": True,
            "message": "Sample data created successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create sample data: {str(e)}"
        )