# -*- coding: utf-8 -*-
"""
Script to create MongoDB indexes for user_id field on all collections.
Run this once after deploying the multi-tenant isolation update.

Usage: python -m app.create_indexes
"""
from app.mongo_db import get_collection


def create_user_id_indexes():
    """Create indexes on user_id field for all multi-tenant collections."""
    collections = [
        "groups",
        "topics",
        "user_contents",
        "post_schedules",
        "repost_schedules",
        "interact_schedules",
        "fanpage_schedules",
        "fanpage_schedules_v2",
        "fb_accounts",
        "activity_logs",
    ]
    
    for col_name in collections:
        col = get_collection(col_name)
        try:
            result = col.create_index("user_id")
            print(f"✓ Created index on {col_name}.user_id: {result}")
        except Exception as e:
            print(f"✗ Error creating index on {col_name}: {e}")
    
    # Create composite index for app_settings (user_id is the primary key)
    try:
        settings_col = get_collection("app_settings")
        result = settings_col.create_index("user_id", unique=True, sparse=True)
        print(f"✓ Created unique index on app_settings.user_id: {result}")
    except Exception as e:
        print(f"✗ Error creating index on app_settings: {e}")
    
    print("\n✓ Index creation complete!")
    print("\nNote: Existing data without user_id field will need to be either:")
    print("  1. Assigned to a specific user (recommended for production)")
    print("  2. Deleted (if test data)")
    print("  3. Left as-is (will only be accessible via scheduler background jobs)")


if __name__ == "__main__":
    create_user_id_indexes()
