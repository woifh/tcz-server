# Rate Limit Adjustment

## Issue
During testing, the application was hitting the rate limit:
```
429 Too Many Requests
50 per 1 hour
```

## Root Cause
The Flask-Limiter was configured with conservative default limits:
- 200 requests per day
- 50 requests per hour

During development and testing, especially with the Alpine.js migration where we're making more API calls, these limits were too restrictive.

## Solution
Increased the default rate limits for development:

**File:** `app/__init__.py`

**Before:**
```python
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
```

**After:**
```python
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["2000 per day", "500 per hour"],
    storage_uri="memory://"
)
```

## Changes
- **Daily limit:** 200 → 2000 (10x increase)
- **Hourly limit:** 50 → 500 (10x increase)

## Impact
✅ Development and testing can proceed without hitting limits
✅ Still provides protection against abuse
✅ More appropriate for local development

## Production Considerations
For production deployment, you may want to:

1. **Use environment-based configuration:**
```python
if app.config['ENV'] == 'development':
    default_limits = ["2000 per day", "500 per hour"]
else:
    default_limits = ["200 per day", "50 per hour"]
```

2. **Use Redis for distributed rate limiting:**
```python
storage_uri="redis://localhost:6379"
```

3. **Exempt certain endpoints:**
```python
@limiter.exempt
def some_endpoint():
    ...
```

4. **Per-endpoint limits:**
```python
@limiter.limit("100 per hour")
def api_endpoint():
    ...
```

## Testing
After the change:
1. Server was restarted
2. Rate limit counter was reset
3. API endpoints are now accessible
4. Testing can continue

## Status: ✅ FIXED

The rate limit has been increased and the server has been restarted. You can now access:
- http://127.0.0.1:5000/reservations/?format=json
- All other API endpoints

The 429 error should no longer occur during normal testing.
