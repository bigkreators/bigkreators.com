# File: models/bot_task.py
class BotTaskRun(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    bot_id: PyObjectId
    task_type: str
    parameters: Dict[str, Any] = {}
    status: str = "pending"  # pending, running, completed, failed, cancelled
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    items_processed: int = 0
    items_successful: int = 0
    items_failed: int = 0
    error_log: List[str] = []
    
    # Approval workflow
    requires_approval: bool = False
    approved_by: Optional[PyObjectId] = None
    approved_at: Optional[datetime] = None

# Bot task queue
@router.post("/api/bots/{bot_id}/tasks/{task_type}/queue")
async def queue_bot_task(
    bot_id: str,
    task_type: str,
    parameters: Dict = {},
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Queue a task for a bot to execute."""
    
    # Verify bot exists and is approved
    bot = await db["bots"].find_one({
        "_id": ObjectId(bot_id),
        "status": "approved"
    })
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found or not approved")
    
    # Check if user can operate this bot
    if str(bot["operatorUserId"]) != str(current_user["_id"]) and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized to operate this bot")
    
    # Check if bot is approved for this task
    if task_type not in bot["approved_tasks"]:
        raise HTTPException(status_code=403, detail=f"Bot not approved for task: {task_type}")
    
    # Create task run
    task_config = BOT_TASKS.get(task_type)
    task_run = BotTaskRun(
        bot_id=ObjectId(bot_id),
        task_type=task_type,
        parameters=parameters,
        requires_approval=task_config.requires_approval if task_config else True
    )
    
    result = await db["bot_task_runs"].insert_one(task_run.model_dump(by_alias=True))
    
    return {"task_id": task_run.task_id, "status": "queued"}
