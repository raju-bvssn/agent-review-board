<!-- dfa6544a-0759-4e0d-8719-9815019f6aed 80c7658f-a724-4aca-8bee-74bb8e92fb9c -->
# Implement Real Salesforce Agentforce API Integration

## Overview

Replace placeholder responses in `generate_text()` with real Salesforce Agentforce API calls using verified endpoint, payload structure, and error fallback handling.

## Verified API Details

- **Endpoint**: `/execute` (NOT `/actions/execute`)
- **Payload**: `"input": {}` (singular, NOT `"inputs": []`)
- **Response**: `{"output": {"text": "..."}}`
- **Auth**: Session ID preferred, OAuth fallback
- **Errors**: Return as text (don't raise)

## Implementation Steps

### 1. Add System Prompt to UI

**File:** [`app/ui/pages/llm_settings.py`](app/ui/pages/llm_settings.py)

In all three Agentforce auth sections (oauth_password, oauth_jwt, session_id), add after the auth-specific fields:

```python
system_prompt = st.text_area(
    "System Prompt (Optional)",
    placeholder="e.g., You are a professional technical writer...",
    help="Optional instructions for the Agentforce agent"
)
```

Add to each auth's configuration storage:

```python
'system_prompt': system_prompt,
```

### 2. Add Class Attributes

**File:** [`app/llm/agentforce_provider.py`](app/llm/agentforce_provider.py)

After line 30 (after `AUTH_TYPES = [...]`), add:

```python
# Salesforce API version for Agentforce
API_VERSION = "v61.0"
```

### 3. Store System Prompt in Constructor

**File:** [`app/llm/agentforce_provider.py`](app/llm/agentforce_provider.py)

After line 94 (after `self.session_id = kwargs.get('session_id')`), add:

```python
self.system_prompt = kwargs.get('system_prompt') or ""
```

### 4. Implement Real API Call

**File:** [`app/llm/agentforce_provider.py`](app/llm/agentforce_provider.py)

Replace lines 272-311 with:

```python
# Get access token (prefer session_id, fallback to OAuth)
try:
    access_token = self.session_id if self.session_id else self._get_access_token()
except Exception as e:
    return (
        f"[Agentforce Authentication Error]\n"
        f"Failed to get access token: {str(e)}\n"
        f"→ Falling back to placeholder mode."
    )

# Build dynamic endpoint
instance_url = self.instance_url.rstrip("/")
endpoint = f"{instance_url}/services/data/{self.API_VERSION}/agentforce/agents/{self.agent_id}/execute"

# Build request
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

payload = {
    "input": {
        "text": prompt,
        "context": self.system_prompt  # NOTE: Some agents use "instructions" instead of "context"
    }
}
# NOTE: If the agent ignores context, switch the key to: "instructions": self.system_prompt

# Debug logging
print(f"[Agentforce] Calling agent {self.agent_id} at {endpoint}")

# Retry logic
last_exception = None
for attempt in range(self.MAX_RETRIES):
    try:
        response = self.client.post(endpoint, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse standard Salesforce response format
            if "output" in data and "text" in data["output"]:
                result_text = data["output"]["text"]
                print(f"[Agentforce] Received {len(result_text)} chars")
                return result_text
            else:
                return (
                    f"[Agentforce Warning] Unexpected response format:\n"
                    f"{json.dumps(data, indent=2)}"
                )
        
        else:
            error_text = response.text
            last_exception = Exception(f"HTTP {response.status_code}: {error_text}")
            
            # Retry on server errors (500+)
            if response.status_code >= 500:
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_DELAY * (2 ** attempt)
                    print(f"[Agentforce] Server error, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
            
            # Don't retry on client errors (401, 403, 404)
            break
    
    except Exception as e:
        last_exception = e
        if attempt < self.MAX_RETRIES - 1:
            print(f"[Agentforce] Error, retrying...")
            time.sleep(self.RETRY_DELAY)
            continue
        break

# All retries failed - return error as text (don't raise)
return (
    f"[Agentforce API Error]\n"
    f"Endpoint: {endpoint}\n"
    f"Error: {str(last_exception)}\n\n"
    f"→ Falling back to placeholder output.\n"
    f"Prompt sent: {prompt[:200]}..."
)
```

**Critical Details:**

- ✅ Endpoint: `/execute` (no `/actions`)
- ✅ Payload: `"input": {...}` (singular)
- ✅ Response parsing: `data["output"]` (FIXED - not `data["text"]`)
- ✅ System prompt: `self.system_prompt`
- ✅ Errors: Return text, never raise

### 5. Pass System Prompt to Provider

**File:** [`app/ui/pages/review_session.py`](app/ui/pages/review_session.py)

Update line 95-106, add system_prompt parameter:

```python
provider = ProviderFactory.create_provider(
    provider_name,
    agent_id=st.session_state.llm_config.get('agent_id'),
    instance_url=st.session_state.llm_config.get('instance_url'),
    auth_type=st.session_state.llm_config.get('auth_type'),
    client_id=st.session_state.llm_config.get('client_id'),
    client_secret=st.session_state.llm_config.get('client_secret'),
    username=st.session_state.llm_config.get('username'),
    password=st.session_state.llm_config.get('password'),
    private_key=st.session_state.llm_config.get('private_key'),
    session_id=st.session_state.llm_config.get('session_id'),
    system_prompt=st.session_state.llm_config.get('system_prompt'),  # NEW
)
```

### 6. Update Tests

**File:** [`tests/unit/test_agentforce_provider.py`](tests/unit/test_agentforce_provider.py)

Update test_generate_text_with_session_id:

```python
# Mock successful Agentforce response
mock_response = Mock()
mock_response.status_code = 200
mock_response.json.return_value = {
    "output": {
        "text": "Real agent response from Salesforce"
    }
}

mock_client.post.return_value = mock_response
```

Verify endpoint does NOT include `/actions`.

## Files to Modify

1. `app/llm/agentforce_provider.py` - API_VERSION, system_prompt, real API
2. `app/ui/pages/llm_settings.py` - system_prompt textarea (3 places)
3. `app/ui/pages/review_session.py` - Pass system_prompt
4. `tests/unit/test_agentforce_provider.py` - Update mocks

## What NOT to Change

❌ Authentication methods

❌ Constructor signature

❌ Other provider methods

❌ Provider factory

❌ Agent logic

## Acceptance Criteria

- ✅ Endpoint: `/execute` (no `/actions`)
- ✅ Payload: `"input": {}` (singular)
- ✅ Response: Parse `data["output"]["text"]` correctly
- ✅ System prompt: `self.system_prompt = kwargs.get('system_prompt') or ""`
- ✅ API_VERSION as class attribute
- ✅ Errors return text
- ✅ All tests pass
- ✅ Works with live org

### To-dos

- [x] Update ReviewerAgent base class to accept previous_feedback parameter
- [x] Update reviewer prompt templates to include previous feedback context
- [x] Update Orchestrator to pass previous feedback to reviewers
- [x] Update confidence_model to calculate improvement delta
- [x] Update ReviewerManager in workflow_engine for previous feedback
- [x] Run full test suite and fix any failures
- [x] Create documentation of the improvement tracking feature