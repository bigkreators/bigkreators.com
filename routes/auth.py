# File: routes/auth.py (Complete file with proper router setup)
"""
Authentication-related routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Form, Query
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from bson import ObjectId
import logging

# Import models explicitly without using relative imports
from models.user import UserCreate, User, Token, TokenData, UserUpdate
from dependencies.database import get_db
from dependencies.auth import get_current_user
from utils.security import hash_password, verify_password, create_access_token
import config

# Create the router instance
router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/register", response_model=Dict[str, Any])
async def register_user(user: UserCreate = Body(...), db=Depends(get_db)):
    """
    Register a new user.
    """
    try:
        # Check if username already exists
        existing_user = await db["users"].find_one({"username": user.username})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        existing_email = await db["users"].find_one({"email": user.email})
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = hash_password(user.password)
        
        # Create user document
        new_user = {
            "username": user.username,
            "email": user.email,
            "passwordHash": hashed_password,
            "role": "user",
            "joinDate": datetime.now(),
            "lastLogin": None,
            "reputation": 0,
            "contributions": {
                "articlesCreated": 0,
                "editsPerformed": 0,
                "rewardsReceived": 0
            },
            # Add default profile fields
            "displayName": None,
            "bio": None, 
            "location": None,
            "website": None,
            "emailPreferences": {
                "articleUpdates": True,
                "proposalUpdates": True,
                "rewards": True,
                "newsletter": False
            },
            "badges": []
        }
        
        # Insert into database
        result = await db["users"].insert_one(new_user)
        
        return {"message": "User registered successfully", "userId": str(result.inserted_id)}
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    remember_me: Optional[str] = Form(None),  # Add remember_me parameter
    db=Depends(get_db)
):
    """
    Enhanced login endpoint with Remember Me functionality.
    
    OAuth2PasswordRequestForm expects:
    - username: string (can be email)
    - password: string
    
    Additional parameters:
    - remember_me: optional string ("true" for extended session)
    """
    try:
        # Log received data for debugging (exclude password)
        logger.debug(f"Login attempt for username: {form_data.username}")
        logger.debug(f"Remember me option: {remember_me}")
        
        # Find user by username
        user = await db["users"].find_one({"username": form_data.username})
        
        # If user not found, try email
        if not user:
            user = await db["users"].find_one({"email": form_data.username})
        
        # Verify user exists and password is correct
        if not user or not verify_password(form_data.password, user["passwordHash"]):
            logger.warning(f"Failed login attempt for: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Determine session duration based on remember_me option
        if remember_me and remember_me.lower() == "true":
            # Extended session (30 days)
            access_token_expires = timedelta(hours=config.JWT_EXPIRATION_HOURS)  # 720 hours = 30 days
            session_type = "extended"
            logger.info(f"Creating extended session for user: {user['username']}")
        else:
            # Standard secure session (24 hours) 
            access_token_expires = timedelta(hours=config.JWT_SHORT_EXPIRATION_HOURS)  # 24 hours
            session_type = "standard"
            logger.info(f"Creating standard session for user: {user['username']}")
        
        # Create access token with appropriate expiration
        access_token, expires_at = create_access_token(
            data={
                "sub": str(user["_id"]),
                "session_type": session_type,
                "remember_me": remember_me == "true" if remember_me else False
            },
            expires_delta=access_token_expires
        )
        
        # Update last login with session info
        await db["users"].update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "lastLogin": datetime.now(),
                    "lastSessionType": session_type,
                    "lastRememberMe": remember_me == "true" if remember_me else False
                }
            }
        )
        
        logger.info(f"Successful {session_type} login for user: {user['username']}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_at": expires_at,
            "session_type": session_type,
            "remember_me": remember_me == "true" if remember_me else False
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get information about the currently authenticated user.
    """
    try:
        # Make a copy of the user data to avoid modifying the original
        user_info = dict(current_user)
        
        # Remove sensitive data
        if "passwordHash" in user_info:
            del user_info["passwordHash"]
        
        # Convert ObjectId to string for JSON serialization
        user_info["_id"] = str(user_info["_id"])
        
        return user_info
    except Exception as e:
        logger.error(f"Error retrieving user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user information: {str(e)}"
        )

@router.put("/me", response_model=Dict[str, Any])
async def update_current_user(
    user_update: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Update information for the currently authenticated user.
    """
    try:
        # Verify password if provided
        if user_update.current_password:
            if not verify_password(user_update.current_password, current_user["passwordHash"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
        else:
            # Password required for any update
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is required to update account information"
            )
        
        # Prepare update data
        update_data = {}
        
        # Basic fields
        if user_update.email and user_update.email != current_user["email"]:
            # Check if email is already in use
            existing_user = await db["users"].find_one({"email": user_update.email})
            if existing_user and str(existing_user["_id"]) != str(current_user["_id"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is already in use"
                )
            update_data["email"] = user_update.email
        
        # Extended profile fields
        if user_update.display_name is not None:
            update_data["displayName"] = user_update.display_name
            
        if user_update.bio is not None:
            update_data["bio"] = user_update.bio
            
        if user_update.location is not None:
            update_data["location"] = user_update.location
            
        if user_update.website is not None:
            update_data["website"] = user_update.website
        
        # Password update
        if user_update.password:
            update_data["passwordHash"] = hash_password(user_update.password)
        
        # Email preferences
        if user_update.email_preferences:
            update_data["emailPreferences"] = user_update.email_preferences.dict(by_alias=True)
        
        # Only proceed if there are updates
        if not update_data:
            return {"message": "No changes made"}
        
        # Update in database
        result = await db["users"].update_one(
            {"_id": current_user["_id"]},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return {"message": "No changes were applied"}
        
        # Get updated user data
        updated_user = await db["users"].find_one({"_id": current_user["_id"]})
        
        # Remove sensitive data
        if "passwordHash" in updated_user:
            del updated_user["passwordHash"]
        
        # Convert ObjectId to string
        updated_user["_id"] = str(updated_user["_id"])
        
        return {
            "message": "User information updated successfully",
            "user": updated_user
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user information: {str(e)}"
        )

@router.post("/logout")
async def logout():
    """
    Logout endpoint.
    
    Note: Since we're using JWT tokens stored in localStorage,
    actual logout happens on the client side by removing the token.
    This endpoint is mainly for logging purposes.
    """
    return {"message": "Successfully logged out"}

@router.put("/profile", response_model=Dict[str, Any])
async def update_profile(
    user_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Update the current user's profile information.
    """
    try:
        # Verify current password
        if not user_data.get("currentPassword"):
            raise HTTPException(status_code=400, detail="Current password is required")
        
        if not verify_password(user_data["currentPassword"], current_user["passwordHash"]):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Prepare update data
        update_data = {}
        
        # Basic profile fields
        if "displayName" in user_data:
            update_data["displayName"] = user_data["displayName"]
        
        if "bio" in user_data:
            update_data["bio"] = user_data["bio"]
        
        if "location" in user_data:
            update_data["location"] = user_data["location"]
        
        if "website" in user_data:
            update_data["website"] = user_data["website"]
        
        # Email field
        if "email" in user_data and user_data["email"] != current_user["email"]:
            # Check if email is already in use
            existing_user = await db["users"].find_one({"email": user_data["email"]})
            if existing_user and str(existing_user["_id"]) != str(current_user["_id"]):
                raise HTTPException(status_code=400, detail="Email is already in use")
            
            update_data["email"] = user_data["email"]
        
        # Email preferences
        if "emailPreferences" in user_data:
            update_data["emailPreferences"] = user_data["emailPreferences"]
        
        # Password update
        if user_data.get("password"):
            update_data["passwordHash"] = hash_password(user_data["password"])
        
        # Only update if there are changes
        if not update_data:
            return {"message": "No changes to save"}
        
        # Update user in database
        result = await db["users"].update_one(
            {"_id": current_user["_id"]},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return {"message": "No changes made"}
        
        return {"message": "Profile updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

@router.delete("/me")
async def delete_account(
    current_user: Dict[str, Any] = Depends(get_current_user),
    delete_media: bool = Query(False, description="Whether to delete uploaded media files (default: preserve with anonymous attribution)"),
    db=Depends(get_db)
):
    """
    Delete the current user's account with user choice for media handling.
    
    Parameters:
    - delete_media: bool (default False)
      - False: Preserve media with anonymous attribution (recommended)
      - True: Completely delete all uploaded media files
    """
    try:
        user_id = current_user["_id"]
        username = current_user["username"]
        
        # Log the deletion attempt with user's media choice
        logger.warning(f"Account deletion requested: {username} (ID: {user_id})")
        logger.info(f"User chose delete_media={delete_media}")
        
        # Prevent admins from deleting their account if they're the last admin
        if current_user.get("role") == "admin":
            admin_count = await db["users"].count_documents({"role": "admin", "isActive": True})
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete the last admin account"
                )
        
        # === ANONYMIZE CONTRIBUTIONS (PRESERVE CONTENT) ===
        
        # 1. Anonymize created articles
        article_result = await db["articles"].update_many(
            {"createdBy": user_id},
            {
                "$set": {
                    "createdBy": "deleted_user",
                    "createdByUsername": "Deleted User",
                    "authorId": "deleted_user",
                    "authorName": "Deleted User"
                }
            }
        )
        logger.info(f"Anonymized {article_result.modified_count} articles")
        
        # 2. Anonymize article edits/revisions
        revisions_result = await db["revisions"].update_many(
            {"createdBy": user_id},
            {
                "$set": {
                    "createdBy": "deleted_user",
                    "creatorUsername": "Deleted User"
                }
            }
        )
        logger.info(f"Anonymized {revisions_result.modified_count} revisions/edits")
        
        # 3. Anonymize edit proposals
        proposals_result = await db["proposals"].update_many(
            {"proposedBy": user_id},
            {
                "$set": {
                    "proposedBy": "deleted_user",
                    "proposedByUsername": "Deleted User"
                }
            }
        )
        logger.info(f"Anonymized {proposals_result.modified_count} edit proposals")
        
        # 4. Anonymize comments/discussions
        comments_result = await db["comments"].update_many(
            {"authorId": user_id},
            {
                "$set": {
                    "authorId": "deleted_user",
                    "authorName": "Deleted User",
                    "authorUsername": "Deleted User"
                }
            }
        )
        logger.info(f"Anonymized {comments_result.modified_count} comments")
        
        # 5. Handle rewards
        rewards_received_result = await db["rewards"].update_many(
            {"rewardedUser": user_id},
            {
                "$set": {
                    "rewardedUser": "deleted_user",
                    "rewardedUsername": "Deleted User"
                }
            }
        )
        
        rewards_given_result = await db["rewards"].update_many(
            {"rewardedBy": user_id},
            {
                "$set": {
                    "rewardedBy": "deleted_user",
                    "rewardedByUsername": "Deleted User"
                }
            }
        )
        logger.info(f"Anonymized {rewards_received_result.modified_count + rewards_given_result.modified_count} rewards")
        
        # === HANDLE MEDIA BASED ON USER CHOICE ===
        
        media_files = await db["media"].find({"uploadedBy": user_id}).to_list(length=None)
        media_count = len(media_files)
        
        if delete_media:
            # User chose to delete all their media files
            
            # First, get list of files to delete from storage
            files_to_delete = []
            for media in media_files:
                if media.get("filePath"):
                    files_to_delete.append(media["filePath"])
                elif media.get("s3Key"):
                    files_to_delete.append(media["s3Key"])
            
            # Delete from database
            media_result = await db["media"].delete_many({"uploadedBy": user_id})
            
            # Delete actual files from storage
            deleted_files_count = 0
            for file_path in files_to_delete:
                try:
                    # Handle local storage
                    if not file_path.startswith('http'):
                        import os
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            deleted_files_count += 1
                    # Handle S3 storage (if you're using it)
                    else:
                        # Implement S3 deletion here
                        # s3_client.delete_object(Bucket=bucket, Key=s3_key)
                        pass
                except Exception as e:
                    logger.error(f"Failed to delete file {file_path}: {e}")
            
            media_action = f"Deleted {media_result.deleted_count} media files ({deleted_files_count} files removed from storage)"
            media_stats = {
                "action": "deleted",
                "database_records": media_result.deleted_count,
                "storage_files": deleted_files_count,
                "total_files": media_count
            }
            
        else:
            # Default: Preserve media with anonymous attribution
            media_result = await db["media"].update_many(
                {"uploadedBy": user_id},
                {
                    "$set": {
                        "uploadedBy": "deleted_user",
                        "uploaderName": "Deleted User",
                        "uploaderUsername": "Deleted User",
                        "originallyAnonymized": True,
                        "anonymizedAt": datetime.now(),
                        "anonymizationReason": "User account deletion"
                    }
                }
            )
            
            media_action = f"Anonymized {media_result.modified_count} media files (preserved with anonymous attribution)"
            media_stats = {
                "action": "anonymized", 
                "files_anonymized": media_result.modified_count,
                "total_files": media_count
            }
        
        logger.info(media_action)
        
        # === DELETE USER-SPECIFIC PRIVATE DATA ===
        
        # Delete user preferences/settings
        prefs_result = await db["user_preferences"].delete_many({"userId": user_id})
        
        # Delete user's private data (bookmarks, favorites, etc.)
        bookmarks_result = await db["bookmarks"].delete_many({"userId": user_id})
        favorites_result = await db["favorites"].delete_many({"userId": user_id})
        
        # === FINALLY DELETE THE USER ACCOUNT ===
        
        user_delete_result = await db["users"].delete_one({"_id": user_id})
        
        if user_delete_result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user account"
            )
        
        # === AUDIT LOG ===
        
        audit_entry = {
            "action": "user_account_deleted",
            "deletedUsername": username,
            "deletedUserId": str(user_id),
            "deletedAt": datetime.now(),
            "userChoice": {
                "deleteMedia": delete_media
            },
            "itemsAnonymized": {
                "articles": article_result.modified_count,
                "revisions": revisions_result.modified_count,
                "proposals": proposals_result.modified_count,
                "comments": comments_result.modified_count,
                "rewards": rewards_received_result.modified_count + rewards_given_result.modified_count
            },
            "mediaHandling": media_stats,
            "privateDataDeleted": {
                "preferences": prefs_result.deleted_count,
                "bookmarks": bookmarks_result.deleted_count,
                "favorites": favorites_result.deleted_count
            }
        }
        
        await db["audit_log"].insert_one(audit_entry)
        
        logger.info(f"User account deleted successfully: {username}")
        logger.info(f"Content preservation: {article_result.modified_count} articles, "
                   f"{revisions_result.modified_count} edits, {proposals_result.modified_count} proposals anonymized")
        
        return {
            "message": "Account deleted successfully",
            "deleted_user": username,
            "user_choices": {
                "delete_media": delete_media
            },
            "contributions_anonymized": {
                "articles": article_result.modified_count,
                "revisions": revisions_result.modified_count,
                "proposals": proposals_result.modified_count,
                "comments": comments_result.modified_count,
                "rewards": rewards_received_result.modified_count + rewards_given_result.modified_count
            },
            "media_handling": media_stats,
            "private_data_deleted": {
                "preferences": prefs_result.deleted_count,
                "bookmarks": bookmarks_result.deleted_count,
                "favorites": favorites_result.deleted_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting account for {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )
