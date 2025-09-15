# File: models/bot.py
class BotUser(BaseModel):
    user_id: PyObjectId = Field(..., alias="userId")
    bot_name: str
    operator_user_id: PyObjectId = Field(..., alias="operatorUserId") 
    description: str
    bot_type: str  # "cleanup", "maintenance", "content", "analysis"
    approved_tasks: List[str] = []  # What the bot is allowed to do
    rate_limit: int = Field(default=60, description="Actions per hour")
    status: str = Field(default="pending")  # pending, approved, suspended, blocked
    approval_date: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    edit_count: int = 0
    
    # Bot-specific flags
    requires_approval: bool = True  # Some bots need pre-approval for edits
    can_auto_edit: bool = False     # Can make edits without review
    max_edits_per_run: int = 50
    
class BotTask(BaseModel):
    task_name: str
    description: str
    risk_level: str  # "low", "medium", "high"
    requires_approval: bool
    
# Predefined bot tasks
BOT_TASKS = {
    "fix_double_redirects": BotTask(
        task_name="fix_double_redirects",
        description="Fix double redirects (A→B→C becomes A→C)",
        risk_level="low",
        requires_approval=False
    ),
    "cleanup_main_to_user_redirects": BotTask(
        task_name="cleanup_main_to_user_redirects", 
        description="Convert problematic Main→User redirects to disambiguation pages",
        risk_level="medium",
        requires_approval=True
    ),
    "create_disambiguation_pages": BotTask(
        task_name="create_disambiguation_pages",
        description="Create disambiguation pages for ambiguous titles",
        risk_level="medium", 
        requires_approval=True
    )
}
