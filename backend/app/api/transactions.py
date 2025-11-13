from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from app.core.security import verify_token
from app.core.database import get_database
from bson import ObjectId
from datetime import datetime

router = APIRouter()

@router.get("/")
async def get_transactions(
    client_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    merchant: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    sort_by: str = Query("date", regex="^(date|amount|anomaly_score)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: dict = Depends(verify_token),
    db = Depends(get_database)
):
    """Get transactions with filtering, pagination, and sorting"""
    
    # Build query
    query = {"user_id": ObjectId(current_user["user_id"])}
    
    if client_id:
        query["client_id"] = ObjectId(client_id)
    
    if date_from or date_to:
        date_query = {}
        if date_from:
            date_query["$gte"] = datetime.fromisoformat(date_from)
        if date_to:
            date_query["$lte"] = datetime.fromisoformat(date_to)
        query["date"] = date_query
    
    if merchant:
        query["merchant"] = {"$regex": merchant, "$options": "i"}
    
    if category:
        query["category"] = category
    
    if min_amount is not None or max_amount is not None:
        amount_query = {}
        if min_amount is not None:
            amount_query["$gte"] = min_amount
        if max_amount is not None:
            amount_query["$lte"] = max_amount
        query["amount"] = amount_query
    
    # Get total count
    total = await db.transactions.count_documents(query)
    
    # Build sort
    sort_direction = 1 if sort_order == "asc" else -1
    sort_field = sort_by
    
    # Get transactions with pagination
    skip = (page - 1) * limit
    cursor = db.transactions.find(query).skip(skip).limit(limit).sort(sort_field, sort_direction)
    transactions = await cursor.to_list(length=limit)
    
    # Convert ObjectIds to strings
    for txn in transactions:
        txn["_id"] = str(txn["_id"])
        txn["user_id"] = str(txn["user_id"])
        txn["client_id"] = str(txn["client_id"])
        txn["document_id"] = str(txn["document_id"])
        # Convert datetime to ISO string
        if isinstance(txn.get("date"), datetime):
            txn["date"] = txn["date"].isoformat()
        if isinstance(txn.get("created_at"), datetime):
            txn["created_at"] = txn["created_at"].isoformat()
    
    return {
        "transactions": transactions,
        "total": total,
        "page": page,
        "limit": limit,
        "filters": {
            "client_id": client_id,
            "date_from": date_from,
            "date_to": date_to,
            "merchant": merchant,
            "category": category,
            "min_amount": min_amount,
            "max_amount": max_amount
        }
    }

@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: str,
    current_user: dict = Depends(verify_token),
    db = Depends(get_database)
):
    """Get single transaction details"""
    
    transaction = await db.transactions.find_one({
        "_id": ObjectId(transaction_id),
        "user_id": ObjectId(current_user["user_id"])
    })
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Convert ObjectIds to strings
    transaction["_id"] = str(transaction["_id"])
    transaction["user_id"] = str(transaction["user_id"])
    transaction["client_id"] = str(transaction["client_id"])
    transaction["document_id"] = str(transaction["document_id"])
    
    # Convert datetime to ISO string
    if isinstance(transaction.get("date"), datetime):
        transaction["date"] = transaction["date"].isoformat()
    if isinstance(transaction.get("created_at"), datetime):
        transaction["created_at"] = transaction["created_at"].isoformat()
    
    return transaction

@router.patch("/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    update_data: dict,
    current_user: dict = Depends(verify_token),
    db = Depends(get_database)
):
    """Update transaction details (category, description, etc.)"""
    
    # Verify transaction ownership
    transaction = await db.transactions.find_one({
        "_id": ObjectId(transaction_id),
        "user_id": ObjectId(current_user["user_id"])
    })
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Filter allowed update fields
    allowed_fields = {"description", "merchant", "category", "amount", "currency"}
    filtered_update = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    if not filtered_update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    # Update transaction
    await db.transactions.update_one(
        {"_id": ObjectId(transaction_id)},
        {"$set": filtered_update}
    )
    
    return {"updated": True, "fields": list(filtered_update.keys())}

@router.get("/stats/summary")
async def get_transaction_summary(
    client_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user: dict = Depends(verify_token),
    db = Depends(get_database)
):
    """Get transaction summary statistics"""
    
    # Build match query
    match_query = {"user_id": ObjectId(current_user["user_id"])}
    
    if client_id:
        match_query["client_id"] = ObjectId(client_id)
    
    if date_from or date_to:
        date_query = {}
        if date_from:
            date_query["$gte"] = datetime.fromisoformat(date_from)
        if date_to:
            date_query["$lte"] = datetime.fromisoformat(date_to)
        match_query["date"] = date_query
    
    # Aggregation pipeline
    pipeline = [
        {"$match": match_query},
        {
            "$group": {
                "_id": None,
                "total_transactions": {"$sum": 1},
                "total_amount": {"$sum": "$amount"},
                "avg_amount": {"$avg": "$amount"},
                "min_amount": {"$min": "$amount"},
                "max_amount": {"$max": "$amount"},
                "high_anomaly_count": {
                    "$sum": {"$cond": [{"$gte": ["$anomaly_score", 0.7]}, 1, 0]}
                }
            }
        }
    ]
    
    result = await db.transactions.aggregate(pipeline).to_list(length=1)
    
    if not result:
        return {
            "total_transactions": 0,
            "total_amount": 0,
            "avg_amount": 0,
            "min_amount": 0,
            "max_amount": 0,
            "high_anomaly_count": 0
        }
    
    return result[0]