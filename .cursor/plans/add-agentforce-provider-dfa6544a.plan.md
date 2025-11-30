<!-- dfa6544a-0759-4e0d-8719-9815019f6aed f9c461b7-0820-4c40-a580-04dfe3a2b92d -->
# Add Salesforce Agentforce Provider to ARB

## Overview

Add Agentforce as a new LLM provider alongside OpenAI, Anthropic, Gemini, HuggingFace, and Ollama. This is a pure provider addition using ARB's existing dependency injection pattern.

## Implementation Steps

### 1. Create AgentforceProvider Class

**File:** `app/llm/agentforce_provider.py`

Implement `AgentforceProvider(BaseLLMProvider)` with:

- **Required methods** (per `BaseLLMProvider` interface):
  - `generate_text(prompt, **kwargs)` - Main execution method
  - `list_models()` - Returns configured agent ID as the "model"
  - `validate_connection()` - Tests Salesforce auth & agent accessibility

- **Authentication support** (all configurable):
  - OAuth 2.0 JWT Bearer Flow
  - OAuth 2.0 Username-Password Flow
  - Direct Session ID

- **Configuration parameters**:
  - `agent_id` (e.g., "0XxdM0000029q33SAA")
  - `instance_url` (e.g., "https://yourorg.salesforce.com")
  - `auth_type` ("oauth_jwt" | "oauth_password" | "session_id")
  - `client_id`, `client_secret`, `username`, `password`
  - `private_key_path` (for JWT flow)
  - `session_id` (for direct session auth)

- **TODO placeholders** for:
  - Salesforce OAuth token endpoint
  - Agentforce agent execution endpoint
  - Request payload schema
  - Response parsing logic

**Pattern to follow:** [`app/llm/gemini_provider.py`](app/llm/gemini_provider.py) (uses httpx for REST API calls)

### 2. Register in Provider Factory

**File:** `app/llm/provider_factory.py`

Add Agentforce to the `PROVIDERS` registry:

```python
from app.llm.agentforce_provider import AgentforceProvider

PROVIDERS = {
    'mock': MockLLMProvider,
    'openai': OpenAIProvider,
    'anthropic': AnthropicProvider,
    'gemini': GeminiProvider,
    'huggingface': HuggingFaceProvider,
    'ollama': OllamaProvider,
    'agentforce': AgentforceProvider,  # NEW
}
```

Note: Follow existing conditional registration pattern if needed (like Ollama's cloud check).

### 3. Add UI Configuration

**File:** `app/ui/pages/llm_settings.py`

Add Agentforce configuration section with:

- **Provider info display** (add to `provider_display` dict)
- **Configuration form** with fields:
  - Agent ID (text input)
  - Instance URL (text input)
  - Auth Type (selectbox: oauth_jwt, oauth_password, session_id)
  - **Conditional fields** based on auth_type:
    - For JWT: client_id, private_key (textarea)
    - For Password: client_id, client_secret, username, password
    - For Session: session_id

- **Test Connection button** - calls `provider.validate_connection()`
- **Save to** `st.session_state.llm_config`
- **Glass card styling** - wrap in `<div class="glass-card">` to match existing theme

**Pattern to follow:** Gemini configuration section (lines 150-200 approx)

### 4. Add Unit Tests

**File:** `tests/unit/test_agentforce_provider.py`

Create tests for:

- Provider initialization with various auth types
- `list_models()` returns agent ID
- `generate_text()` with mocked Salesforce API
- `validate_connection()` success/failure scenarios
- Error handling for missing credentials
- All three auth methods

**Pattern to follow:** [`tests/test_provider_gemini.py`](tests/test_provider_gemini.py) (mock httpx responses)

### 5. Update Documentation

**File:** `README.md`

Add Agentforce section:

- Installation (no extra packages needed, uses httpx)
- Configuration instructions
- Supported auth methods
- Example agent ID format
- Link to Salesforce Agentforce docs

## Key Design Decisions

1. **Method signature:** Use `generate_text(prompt, **kwargs)` not `generate()` (matches `BaseLLMProvider`)
2. **Model concept:** The Agentforce agent ID acts as the "model" in ARB's UI
3. **Auth storage:** Store credentials in `st.session_state.llm_config['agentforce']` (encrypted in production)
4. **Placeholder behavior:** Return informative placeholder text until Salesforce API details are finalized
5. **Error messages:** Clear, actionable errors for auth failures, missing config, API issues

## What NOT to Modify

❌ `app/agents/` - No changes to PresenterAgent, ReviewerAgents, ConfidenceAgent

❌ `app/orchestration/` - No changes to WorkflowEngine, ReviewerManager, Aggregator

❌ `app/core/` - No changes to Orchestrator, SessionManager

❌ `app/ui/theme/` - No CSS or theme changes

❌ Agent prompts or execution logic

❌ Iteration tracking or confidence scoring

## Acceptance Criteria

- ✅ Agentforce appears in LLM Settings provider dropdown
- ✅ Configuration form saves successfully
- ✅ "Test Connection" shows placeholder success message
- ✅ Agents can be created with AgentforceProvider
- ✅ `generate_text()` returns placeholder responses
- ✅ All existing tests still pass (339/339)
- ✅ New Agentforce tests pass
- ✅ No regressions in other providers or agents

## Implementation Order

1. Create `agentforce_provider.py` with full scaffolding
2. Register in `provider_factory.py`
3. Add UI configuration in `llm_settings.py`
4. Write unit tests
5. Update README
6. Test end-to-end (create session with Agentforce provider)
7. Document TODO items for Salesforce API integration

### To-dos

- [ ] Create app/llm/agentforce_provider.py with BaseLLMProvider implementation
- [ ] Register AgentforceProvider in app/llm/provider_factory.py
- [ ] Add Agentforce configuration UI in app/ui/pages/llm_settings.py
- [ ] Create tests/unit/test_agentforce_provider.py
- [ ] Update README.md with Agentforce setup instructions
- [ ] End-to-end test: Create session with Agentforce provider