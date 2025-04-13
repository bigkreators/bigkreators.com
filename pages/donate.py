"""
Donation-related routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
import logging

from dependencies import get_db, get_current_user, get_cache

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/donate", response_class=HTMLResponse)
async def donate_page(
    request: Request,
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Render the donation page.
    """
    templates = request.app.state.templates
    
    try:
        # Get donation stats from cache or compute them
        cache_key = "donation_stats"
        donation_stats = await cache.get(cache_key)
        
        if not donation_stats:
            # In a real implementation, this would fetch actual stats from a database
            # For now, using placeholder data
            donation_stats = {
                "total_donations": 5280,
                "total_amount": 92450,
                "monthly_supporters": 325,
                "recent_donors": [
                    {"name": "Anonymous", "amount": 50, "message": "Keep up the great work!"},
                    {"name": "John D.", "amount": 25, "message": "Happy to support this project"},
                    {"name": "Sarah M.", "amount": 100, "message": "Great resource, thank you"},
                    {"name": "Anonymous", "amount": 10, "message": None},
                    {"name": "Michael T.", "amount": 35, "message": "Invaluable information source"}
                ],
                "top_sponsors": [
                    {"name": "Example Corp", "level": "Gold"},
                    {"name": "Sample Industries", "level": "Silver"},
                    {"name": "Demo Technologies", "level": "Bronze"}
                ]
            }
            
            # Cache for 1 hour
            await cache.set(cache_key, donation_stats, 3600)
        
        # Render the template
        return templates.TemplateResponse(
            "donate.html",
            {
                "request": request,
                "stats": donation_stats
            }
        )
    except Exception as e:
        logger.error(f"Error rendering donation page: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error loading donation page: {str(e)}"},
            status_code=500
        )

@router.get("/donate/sponsors", response_class=HTMLResponse)
async def sponsors_page(
    request: Request,
    db=Depends(get_db)
):
    """
    Render the sponsors recognition page.
    """
    templates = request.app.state.templates
    
    # This would normally fetch actual sponsors from a database
    # Using placeholder data for now
    sponsors = {
        "gold": [
            {"name": "Example Corp", "website": "https://example.com", "description": "Leading provider of example services"},
            {"name": "ABC Enterprises", "website": "https://abc.example", "description": "Global leader in alphabetical solutions"}
        ],
        "silver": [
            {"name": "Sample Industries", "website": "https://sample.example", "description": "Creating innovative samples since 2015"},
            {"name": "XYZ Corporation", "website": "https://xyz.example", "description": "Pioneers in dimensional technologies"},
            {"name": "Tech Solutions", "website": "https://tech.example", "description": "Making technology accessible"}
        ],
        "bronze": [
            {"name": "Demo Technologies", "website": "https://demo.example", "description": "Bringing demonstrations to life"},
            {"name": "New Horizons", "website": "https://newhorizons.example", "description": "Exploring new frontiers"},
            {"name": "Digital Dynamics", "website": "https://digital.example", "description": "Dynamic digital solutions"},
            {"name": "Future Systems", "website": "https://future.example", "description": "Building the systems of tomorrow"}
        ]
    }
    
    return templates.TemplateResponse(
        "sponsors.html",
        {
            "request": request,
            "sponsors": sponsors
        }
    )

@router.get("/donate/transparency", response_class=HTMLResponse)
async def transparency_page(
    request: Request,
    db=Depends(get_db)
):
    """
    Render the financial transparency page.
    """
    templates = request.app.state.templates
    
    # This would normally fetch actual financial data from a database
    # Using placeholder data for now
    financial_data = {
        "current_quarter": {
            "period": "Q1 2025",
            "income": {
                "donations": 24530,
                "monthly_supporters": 9750,
                "corporate_sponsorships": 7500
            },
            "expenses": {
                "server_costs": 8200,
                "development": 15000,
                "content_management": 7500,
                "administrative": 3500
            }
        },
        "previous_quarters": [
            {
                "period": "Q4 2024",
                "total_income": 38500,
                "total_expenses": 32000,
                "report_url": "#q4-2024-report"
            },
            {
                "period": "Q3 2024",
                "total_income": 35200,
                "total_expenses": 31500,
                "report_url": "#q3-2024-report"
            },
            {
                "period": "Q2 2024",
                "total_income": 31800,
                "total_expenses": 29700,
                "report_url": "#q2-2024-report"
            }
        ],
        "annual_reports": [
            {"year": 2024, "url": "#2024-annual-report"},
            {"year": 2023, "url": "#2023-annual-report"}
        ]
    }
    
    return templates.TemplateResponse(
        "financial_transparency.html",
        {
            "request": request,
            "financial_data": financial_data
        }
    )
