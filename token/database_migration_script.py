#!/usr/bin/env python3
"""
MongoDB Database Migration Script for WCT Token Integration
This script adds token-related fields and collections to your existing BigKreators database
"""

import asyncio
import os
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, TEXT
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Colors for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def print_section(title):
    print(f"\n{YELLOW}{'='*50}{NC}")
    print(f"{YELLOW}{title}{NC}")
    print(f"{YELLOW}{'='*50}{NC}")

def print_success(message):
    print(f"{GREEN}✅ {message}{NC}")

def print_error(message):
    print(f"{RED}❌ {message}{NC}")

def print_info(message):
    print(f"{BLUE}ℹ️  {message}{NC}")

class TokenDatabaseMigration:
    def __init__(self, mongo_uri: str, db_name: str):
        self.client = AsyncIOMotorClient(mongo_uri)
        self.db = self.client[db_name]
        
    async def run_migration(self):
        """Run the complete database migration"""
        print_section("BigKreators Token Database Migration")
        print_info("This will add token functionality to your existing MongoDB database")
        
        try:
            # Test connection
            await self.test_connection()
            
            # Run migrations in order
            await self.migrate_users_collection()
            await self.create_contributions_collection()
            await self.create_token_rewards_collection()
            await self.create_weekly_distributions_collection()
            await self.create_staking_records_collection()
            await self.create_governance_proposals_collection()
            await self.update_articles_collection()
            await self.create_indices()
            await self.seed_initial_data()
            
            print_section("Migration Complete!")
            print_success("Database successfully migrated for token integration")
            
        except Exception as e:
            print_error(f"Migration failed: {e}")
            raise
        finally:
            await self.close()
    
    async def test_connection(self):
        """Test database connection"""
        try:
            await self.client.admin.command('ping')
            print_success("Connected to MongoDB successfully")
            
            # Check existing collections
            collections = await self.db.list_collection_names()
            print_info(f"Found {len(collections)} existing collections: {', '.join(collections)}")
            
        except Exception as e:
            print_error(f"Database connection failed: {e}")
            raise
    
    async def migrate_users_collection(self):
        """Add token-related fields to existing users"""
        print_section("Migrating Users Collection")
        
        # Add token fields to existing users
        update_result = await self.db.users.update_many(
            {},  # Update all users
            {
                "$set": {
                    "wallet_address": None,
                    "reputation_score": 1.0,
                    "total_contributions": 0,
                    "total_points": 0,
                    "total_tokens_earned": 0.0,
                    "staked_tokens": 0.0,
                    "governance_power": 0.0,
                    "last_reward_claim": None,
                    "token_updated_at": datetime.utcnow()
                }
            }
        )
        
        print_success(f"Updated {update_result.modified_count} existing users with token fields")
        
        # Show user count
        user_count = await self.db.users.count_documents({})
        print_info(f"Total users in database: {user_count}")
    
    async def create_contributions_collection(self):
        """Create contributions tracking collection"""
        print_section("Creating Contributions Collection")
        
        # Create collection with schema validation
        contributions_schema = {
            "bsonType": "object",
            "required": ["user_id", "article_id", "type", "base_points", "total_points", "created_at"],
            "properties": {
                "user_id": {"bsonType": "string"},
                "article_id": {"bsonType": "string"},
                "type": {
                    "bsonType": "string",
                    "enum": ["creation", "major_edit", "minor_edit", "review", "translation"]
                },
                "base_points": {"bsonType": "int"},
                "quality_multiplier": {"bsonType": "double", "minimum": 0.5, "maximum": 3.0},
                "reputation_multiplier": {"bsonType": "double", "minimum": 0.8, "maximum": 1.5},
                "demand_multiplier": {"bsonType": "double", "minimum": 1.0, "maximum": 2.5},
                "total_points": {"bsonType": "int"},
                "description": {"bsonType": "string"},
                "metadata": {"bsonType": "object"},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"}
            }
        }
        
        try:
            await self.db.create_collection(
                "contributions",
                validator={"$jsonSchema": contributions_schema}
            )
            print_success("Created contributions collection with validation")
        except Exception as e:
            if "already exists" in str(e):
                print_info("Contributions collection already exists")
            else:
                raise
    
    async def create_token_rewards_collection(self):
        """Create individual token rewards collection"""
        print_section("Creating Token Rewards Collection")
        
        rewards_schema = {
            "bsonType": "object",
            "required": ["user_id", "week_start", "week_end", "total_points", "token_amount", "status"],
            "properties": {
                "user_id": {"bsonType": "string"},
                "weekly_distribution_id": {"bsonType": "string"},
                "week_start": {"bsonType": "date"},
                "week_end": {"bsonType": "date"},
                "total_points": {"bsonType": "int"},
                "token_amount": {"bsonType": "double"},
                "staking_multiplier": {"bsonType": "double", "minimum": 1.0, "maximum": 2.0},
                "transaction_signature": {"bsonType": "string"},
                "status": {
                    "bsonType": "string",
                    "enum": ["pending", "processing", "completed", "failed"]
                },
                "claimed_at": {"bsonType": "date"},
                "created_at": {"bsonType": "date"}
            }
        }
        
        try:
            await self.db.create_collection(
                "token_rewards",
                validator={"$jsonSchema": rewards_schema}
            )
            print_success("Created token_rewards collection")
        except Exception as e:
            if "already exists" in str(e):
                print_info("Token rewards collection already exists")
            else:
                raise
    
    async def create_weekly_distributions_collection(self):
        """Create weekly distribution tracking collection"""
        print_section("Creating Weekly Distributions Collection")
        
        distributions_schema = {
            "bsonType": "object",
            "required": ["week_start", "week_end", "total_points", "total_tokens", "status"],
            "properties": {
                "week_start": {"bsonType": "date"},
                "week_end": {"bsonType": "date"},
                "total_points": {"bsonType": "int"},
                "total_tokens": {"bsonType": "double"},
                "point_to_token_ratio": {"bsonType": "double"},
                "user_count": {"bsonType": "int"},
                "distribution_tx_hash": {"bsonType": "string"},
                "status": {
                    "bsonType": "string",
                    "enum": ["pending", "processing", "completed", "failed"]
                },
                "started_at": {"bsonType": "date"},
                "completed_at": {"bsonType": "date"},
                "created_at": {"bsonType": "date"}
            }
        }
        
        try:
            await self.db.create_collection(
                "weekly_distributions",
                validator={"$jsonSchema": distributions_schema}
            )
            print_success("Created weekly_distributions collection")
        except Exception as e:
            if "already exists" in str(e):
                print_info("Weekly distributions collection already exists")
            else:
                raise
    
    async def create_staking_records_collection(self):
        """Create staking records collection"""
        print_section("Creating Staking Records Collection")
        
        staking_schema = {
            "bsonType": "object",
            "required": ["user_id", "amount", "duration_days", "start_date", "end_date", "status"],
            "properties": {
                "user_id": {"bsonType": "string"},
                "amount": {"bsonType": "double"},
                "duration_days": {"bsonType": "int", "enum": [30, 90, 180, 365]},
                "apy_rate": {"bsonType": "double"},
                "multiplier": {"bsonType": "double"},
                "start_date": {"bsonType": "date"},
                "end_date": {"bsonType": "date"},
                "status": {
                    "bsonType": "string",
                    "enum": ["active", "completed", "unstaked_early"]
                },
                "stake_tx_hash": {"bsonType": "string"},
                "unstake_tx_hash": {"bsonType": "string"},
                "rewards_earned": {"bsonType": "double"},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"}
            }
        }
        
        try:
            await self.db.create_collection(
                "staking_records",
                validator={"$jsonSchema": staking_schema}
            )
            print_success("Created staking_records collection")
        except Exception as e:
            if "already exists" in str(e):
                print_info("Staking records collection already exists")
            else:
                raise
    
    async def create_governance_proposals_collection(self):
        """Create governance proposals collection"""
        print_section("Creating Governance Proposals Collection")
        
        proposals_schema = {
            "bsonType": "object",
            "required": ["title", "description", "proposer_id", "proposal_type", "status"],
            "properties": {
                "title": {"bsonType": "string"},
                "description": {"bsonType": "string"},
                "proposer_id": {"bsonType": "string"},
                "proposal_type": {
                    "bsonType": "string",
                    "enum": ["parameter_change", "feature_request", "treasury_allocation", "governance_change"]
                },
                "parameters": {"bsonType": "object"},
                "voting_start": {"bsonType": "date"},
                "voting_end": {"bsonType": "date"},
                "votes_for": {"bsonType": "double"},
                "votes_against": {"bsonType": "double"},
                "votes_abstain": {"bsonType": "double"},
                "total_voting_power": {"bsonType": "double"},
                "quorum_required": {"bsonType": "double"},
                "status": {
                    "bsonType": "string",
                    "enum": ["draft", "active", "passed", "rejected", "executed", "cancelled"]
                },
                "execution_tx_hash": {"bsonType": "string"},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"}
            }
        }
        
        try:
            await self.db.create_collection(
                "governance_proposals",
                validator={"$jsonSchema": proposals_schema}
            )
            print_success("Created governance_proposals collection")
        except Exception as e:
            if "already exists" in str(e):
                print_info("Governance proposals collection already exists")
            else:
                raise
    
    async def update_articles_collection(self):
        """Add token-related fields to articles collection"""
        print_section("Updating Articles Collection")
        
        # Add token-related fields to existing articles
        update_result = await self.db.articles.update_many(
            {},
            {
                "$set": {
                    "demand_score": 1.0,
                    "quality_score": 1.0,
                    "total_tokens_earned": 0.0,
                    "contribution_count": 0,
                    "last_contribution_date": None,
                    "token_metadata": {
                        "featured": False,
                        "high_demand": False,
                        "expert_reviewed": False
                    }
                }
            }
        )
        
        print_success(f"Updated {update_result.modified_count} articles with token fields")
        
        article_count = await self.db.articles.count_documents({})
        print_info(f"Total articles in database: {article_count}")
    
    async def create_indices(self):
        """Create database indices for token collections"""
        print_section("Creating Database Indices")
        
        indices_created = 0
        
        # Users collection indices
        try:
            await self.db.users.create_index([("wallet_address", ASCENDING)], unique=True, sparse=True)
            indices_created += 1
        except Exception:
            pass  # Index might already exist
        
        # Contributions collection indices
        indices = [
            ([("user_id", ASCENDING), ("created_at", -1)], {}),
            ([("article_id", ASCENDING), ("created_at", -1)], {}),
            ([("type", ASCENDING)], {}),
            ([("created_at", -1)], {}),
            ([("total_points", -1)], {})
        ]
        
        for index_spec, options in indices:
            try:
                await self.db.contributions.create_index(index_spec, **options)
                indices_created += 1
            except Exception:
                pass
        
        # Token rewards collection indices
        rewards_indices = [
            ([("user_id", ASCENDING), ("week_start", -1)], {}),
            ([("weekly_distribution_id", ASCENDING)], {}),
            ([("status", ASCENDING)], {}),
            ([("created_at", -1)], {})
        ]
        
        for index_spec, options in rewards_indices:
            try:
                await self.db.token_rewards.create_index(index_spec, **options)
                indices_created += 1
            except Exception:
                pass
        
        # Weekly distributions indices
        dist_indices = [
            ([("week_start", ASCENDING)], {"unique": True}),
            ([("status", ASCENDING)], {}),
            ([("created_at", -1)], {})
        ]
        
        for index_spec, options in dist_indices:
            try:
                await self.db.weekly_distributions.create_index(index_spec, **options)
                indices_created += 1
            except Exception:
                pass
        
        # Staking records indices
        staking_indices = [
            ([("user_id", ASCENDING), ("status", ASCENDING)], {}),
            ([("end_date", ASCENDING)], {}),
            ([("created_at", -1)], {})
        ]
        
        for index_spec, options in staking_indices:
            try:
                await self.db.staking_records.create_index(index_spec, **options)
                indices_created += 1
            except Exception:
                pass
        
        # Governance proposals indices
        gov_indices = [
            ([("proposer_id", ASCENDING)], {}),
            ([("status", ASCENDING)], {}),
            ([("voting_end", ASCENDING)], {}),
            ([("created_at", -1)], {})
        ]
        
        for index_spec, options in gov_indices:
            try:
                await self.db.governance_proposals.create_index(index_spec, **options)
                indices_created += 1
            except Exception:
                pass
        
        print_success(f"Created {indices_created} database indices")
    
    async def seed_initial_data(self):
        """Seed initial data for token system"""
        print_section("Seeding Initial Data")
        
        # Create initial weekly distribution record
        current_week_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        # Get Monday of current week
        days_since_monday = current_week_start.weekday()
        week_start = current_week_start - timedelta(days=days_since_monday)
        week_end = week_start + timedelta(days=7)
        
        initial_distribution = {
            "week_start": week_start,
            "week_end": week_end,
            "total_points": 0,
            "total_tokens": 10000.0,  # Weekly pool
            "point_to_token_ratio": 0.0,
            "user_count": 0,
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        try:
            await self.db.weekly_distributions.insert_one(initial_distribution)
            print_success("Created initial weekly distribution record")
        except Exception as e:
            print_info("Initial distribution record already exists or failed to create")
        
        # Create sample contribution types reference
        contribution_types = {
            "contribution_types": {
                "creation": {"base_points": 100, "description": "Creating new wiki articles"},
                "major_edit": {"base_points": 50, "description": "Substantial content improvements"},
                "minor_edit": {"base_points": 20, "description": "Small fixes and formatting"},
                "review": {"base_points": 10, "description": "Reviewing edit proposals"},
                "translation": {"base_points": 75, "description": "Translating articles"}
            },
            "multipliers": {
                "quality": {"min": 0.5, "max": 3.0, "default": 1.0},
                "reputation": {"min": 0.8, "max": 1.5, "default": 1.0},
                "demand": {"min": 1.0, "max": 2.5, "default": 1.0}
            },
            "staking_tiers": {
                "30_days": {"apy": 0.05, "multiplier": 1.1},
                "90_days": {"apy": 0.12, "multiplier": 1.3},
                "180_days": {"apy": 0.25, "multiplier": 1.6},
                "365_days": {"apy": 0.50, "multiplier": 2.0}
            },
            "updated_at": datetime.utcnow()
        }
        
        try:
            await self.db.system_config.replace_one(
                {"_id": "token_system"},
                {"_id": "token_system", **contribution_types},
                upsert=True
            )
            print_success("Created token system configuration")
        except Exception as e:
            print_info("Token system config already exists or failed to create")
        
        print_success("Initial data seeded successfully")
    
    async def close(self):
        """Close database connection"""
        self.client.close()

async def main():
    """Main migration function"""
    
    # Get database configuration
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("DB_NAME", "bigkreators")
    
    if not mongo_uri:
        print_error("MONGO_URI environment variable not set")
        print_info("Add MONGO_URI to your .env file")
        return False
    
    print_info(f"Connecting to database: {db_name}")
    print_info(f"MongoDB URI: {mongo_uri[:20]}...")
    
    try:
        # Run migration
        migration = TokenDatabaseMigration(mongo_uri, db_name)
        await migration.run_migration()
        
        print_section("Migration Summary")
        print_success("✅ Users collection: Added token fields")
        print_success("✅ Contributions collection: Created with validation")
        print_success("✅ Token rewards collection: Created")
        print_success("✅ Weekly distributions collection: Created")
        print_success("✅ Staking records collection: Created")
        print_success("✅ Governance proposals collection: Created")
        print_success("✅ Articles collection: Added token fields")
        print_success("✅ Database indices: Created for performance")
        print_success("✅ Initial data: Seeded system configuration")
        
        print_section("Next Steps")
        print_info("1. Test the token API endpoints")
        print_info("2. Create your first contribution")
        print_info("3. Run weekly reward distribution")
        print_info("4. Set up staking functionality")
        
        return True
        
    except Exception as e:
        print_error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
