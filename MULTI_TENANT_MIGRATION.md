# Multi-Tenant User Isolation Migration Guide

## Overview

This document describes the multi-tenant isolation implementation for the FastAPI + MongoDB backend. Every resource is now scoped to the authenticated user via their JWT token.

## What Changed

### 1. Authentication Requirement
All endpoints now require JWT Bearer authentication. The `user_id` is extracted from the JWT `sub` field and used to filter all database operations.

### 2. Isolated Resources
The following collections are now scoped by `user_id`:
- `groups` — Facebook groups
- `topics` — Content topics
- `user_contents` — User-generated content
- `post_schedules` — Post schedules
- `repost_schedules` — Repost schedules
- `interact_schedules` — Interaction schedules
- `fanpage_schedules` — Fanpage schedules (legacy)
- `fanpage_schedules_v2` — Fanpage schedules v2
- `fb_accounts` — Facebook account credentials
- `activity_logs` — Activity logs
- `app_settings` — Application settings (per-user)

### 3. Architecture Changes

#### New Files
- `app/dependencies.py` — Shared dependency `get_user_id()` that extracts user ID from JWT

#### Modified Routers
All routers now inject `user_id: str = Depends(get_user_id)`:
- `app/routers/groups.py`
- `app/routers/topics.py`
- `app/routers/schedules.py` (all 3 schedule types)
- `app/routers/logs.py`
- `app/routers/setting.py`
- `app/routers/fb_accounts.py`
- `app/routers/fanpage_schedules.py`
- `app/routers/user_contents.py`

#### Modified Backend
- `app/mongo_crud_adapter.py` — All methods now accept optional `user_id` parameter
  - When `user_id` is provided (router context): queries are filtered by `{"user_id": user_id}`
  - When `user_id` is `None` (scheduler context): no user filter (safe because scheduler uses specific IDs)
  
- `app/crud.py` — All MongoDB functions now thread `user_id` parameter

- `app/scheduler.py` — Background jobs retrieve `user_id` from schedule documents for logging:
  ```python
  user_id = doc.get("user_id")
  crud.create_log(db, "fanpage_v2", schedule_id, user_id=user_id)
  ```

## Database Schema Changes

### All Collections Get `user_id` Field

Every document now includes:
```javascript
{
  "id": 123,
  "user_id": "uuid-string",  // NEW: UUID from JWT sub field
  // ... other fields
}
```

### App Settings — Per-User
Previously `app_settings` had a single document `{"id": 1}` shared by all users.

Now each user gets their own settings document keyed by `user_id`:
```javascript
// Old (single shared document)
{ "id": 1, "headless_mode": false, "thu_muc_anh": "C:/..." }

// New (per-user documents)
{ "user_id": "uuid-1", "headless_mode": false, "thu_muc_anh": "C:/..." }
{ "user_id": "uuid-2", "headless_mode": true, "thu_muc_anh": "D:/..." }
```

## Migration Steps

### 1. Create Indexes
Run the index creation script to add indexes on `user_id` for query performance:

```bash
python -m app.create_indexes
```

This creates non-unique indexes on `user_id` for all collections and a unique sparse index on `app_settings.user_id`.

### 2. Assign Existing Data to Users

**Option A: Assign to a specific user (recommended for production)**

```javascript
// MongoDB shell — assign all existing data to the first admin user
const adminUser = db.users.findOne({role: "admin"});
const userId = adminUser.id;

db.groups.updateMany({user_id: {$exists: false}}, {$set: {user_id: userId}});
db.topics.updateMany({user_id: {$exists: false}}, {$set: {user_id: userId}});
db.user_contents.updateMany({user_id: {$exists: false}}, {$set: {user_id: userId}});
db.post_schedules.updateMany({user_id: {$exists: false}}, {$set: {user_id: userId}});
db.repost_schedules.updateMany({user_id: {$exists: false}}, {$set: {user_id: userId}});
db.interact_schedules.updateMany({user_id: {$exists: false}}, {$set: {user_id: userId}});
db.fanpage_schedules.updateMany({user_id: {$exists: false}}, {$set: {user_id: userId}});
db.fanpage_schedules_v2.updateMany({user_id: {$exists: false}}, {$set: {user_id: userId}});
db.fb_accounts.updateMany({user_id: {$exists: false}}, {$set: {user_id: userId}});
db.activity_logs.updateMany({user_id: {$exists: false}}, {$set: {user_id: userId}});

// Migrate legacy app_settings
db.app_settings.updateOne({id: 1}, {$set: {user_id: userId}});
```

**Option B: Delete test data (if not in production)**

```javascript
// MongoDB shell — remove all data without user_id
db.groups.deleteMany({user_id: {$exists: false}});
db.topics.deleteMany({user_id: {$exists: false}});
// ... repeat for all collections
```

**Option C: Leave as-is (only works for scheduler)**

Documents without `user_id` will be inaccessible via API endpoints (filtered out by user_id check), but scheduler jobs can still access them since they use specific `schedule_id` values.

### 3. Restart the Application

```bash
# The app will now enforce user isolation on all endpoints
python -m uvicorn app.main:app --reload
```

## Testing Multi-Tenant Isolation

### 1. Create Two Test Users

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user1",
    "password": "Password123",
    "confirm_password": "Password123"
  }'

curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user2",
    "password": "Password123",
    "confirm_password": "Password123"
  }'
```

### 2. Login and Get Tokens

```bash
# User 1
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "Password123"}'
# Save token1

# User 2
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user2", "password": "Password123"}'
# Save token2
```

### 3. Create Resources as Each User

```bash
# User 1 creates a group
curl -X POST http://localhost:8000/groups \
  -H "Authorization: Bearer $TOKEN1" \
  -H "Content-Type: application/json" \
  -d '{
    "ten": "User1 Group",
    "url": "https://facebook.com/groups/user1group"
  }'

# User 2 creates a group
curl -X POST http://localhost:8000/groups \
  -H "Authorization: Bearer $TOKEN2" \
  -H "Content-Type: application/json" \
  -d '{
    "ten": "User2 Group",
    "url": "https://facebook.com/groups/user2group"
  }'
```

### 4. Verify Isolation

```bash
# User 1 lists groups — should only see User1 Group
curl -X GET http://localhost:8000/groups \
  -H "Authorization: Bearer $TOKEN1"

# User 2 lists groups — should only see User2 Group
curl -X GET http://localhost:8000/groups \
  -H "Authorization: Bearer $TOKEN2"
```

Expected: Each user only sees their own groups. Cross-tenant access is prevented.

## Scheduler Background Jobs

### How User Isolation Works in Background Jobs

The scheduler jobs (posting, reposting, interaction) run without a user session. They retrieve `user_id` from the schedule document itself:

```python
def job_fanpage_v2(schedule_id: int):
    doc = col.find_one({"id": schedule_id})
    user_id = doc.get("user_id")  # Retrieved from document
    
    # Use user_id for logging and settings lookup
    cfg = _lay_cau_hinh_hien_tai(db, user_id=user_id)
    log = crud.create_log(db, "fanpage_v2", schedule_id, user_id=user_id)
```

### Why This is Safe

1. **Schedule ID is unique** — Each schedule has a globally unique ID
2. **user_id is stored at creation** — When a user creates a schedule via API, their `user_id` is stored in the document
3. **Scheduler doesn't need filtering** — The scheduler fetches schedules by exact `id`, not by user_id query
4. **Logs are properly scoped** — Activity logs inherit `user_id` from the schedule document

## Backward Compatibility

### SQLAlchemy Path (USE_MONGODB=False)

The SQLAlchemy code path keeps working without user isolation (for backward compatibility). The routers now require JWT auth regardless, but the SQL queries don't filter by user_id:

```python
if settings.USE_MONGODB:
    # MongoDB: user isolation applied
    def list_groups(db, user_id=None):
        return store.list_groups(user_id=user_id)
else:
    # SQLAlchemy: no user isolation (legacy behavior)
    def list_groups(db, user_id=None):
        return db.query(models.Group).order_by(models.Group.id).all()
```

This is intentional — the task scope focused on MongoDB isolation since `USE_MONGODB=True` is the active deployment path.

## Security Considerations

### 1. JWT Token Security
- Tokens contain `user_id` in the `sub` claim
- Token validation happens in `get_current_user()` dependency
- Expired or invalid tokens are rejected with 401 Unauthorized

### 2. Query Injection Prevention
- MongoDB queries use parameterized filters: `{"user_id": user_id}`
- `user_id` is a validated UUID string from JWT (not user input)
- No raw query string concatenation

### 3. Horizontal Privilege Escalation Prevention
- Users cannot access resources by guessing IDs
- All queries include `{"user_id": user_id}` filter
- Even if a user knows another user's `group_id`, the query will return 404

### 4. Scheduler Safety
- Scheduler uses specific `schedule_id` (not user queries)
- `user_id` is retrieved from the schedule document (not passed in)
- Cannot be exploited to access other users' data

## Performance Considerations

### Indexes
The `create_indexes.py` script creates indexes on `user_id` for all collections. This ensures query performance scales well with multiple users.

### Query Patterns
All queries follow this pattern:
```javascript
// Fast: uses index on user_id
db.groups.find({"user_id": "uuid-string"}).sort("id", 1)

// Fast: uses both id (unique) and user_id (indexed)
db.groups.findOne({"id": 123, "user_id": "uuid-string"})
```

### Collection Size
With multi-tenancy, collections grow with the number of users × resources per user. The indexes keep queries fast even with thousands of users.

## Rollback Plan

If issues arise after deployment, you can temporarily disable user isolation by modifying the routers to pass `user_id=None`:

```python
# Temporary rollback — DO NOT use in production long-term
def danh_sach_nhom(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return crud.list_groups(db, user_id=None)  # Disables isolation
```

Then plan a proper fix and redeploy with isolation enabled.

## Support

For issues or questions about multi-tenant isolation:
1. Check MongoDB logs for query errors
2. Verify JWT tokens contain valid `user_id` in sub claim
3. Ensure indexes are created (`python -m app.create_indexes`)
4. Verify existing data has `user_id` field populated
