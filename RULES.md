# 📘 **AGENT REVIEW BOARD - PROJECT RULES**

This document contains the **mandatory rules** that all contributors and development must follow.

---

## **Architecture & Code Quality Rules**

### 1. Strict Separation of Concerns

Maintain strict separation between:

* `ui/` — Streamlit-only UI components
* `core/` — State management, session orchestration
* `agents/` — Agent classes + shared memory format
* `llm/` — Provider interfaces, model selection logic
* `models/` — Pydantic models for states, messages, feedback
* `utils/` — File utils, logging

### 2. No Streamlit in Core Logic

**NO** Streamlit imports inside `core/`, `agents/`, `llm/`, or `models/`.

UI components must only call into `core` through clean functions/classes.

### 3. Single Responsibility Principle

* Use small, single-responsibility functions
* Include docstrings for all public functions
* Use type hints everywhere
* Keep classes focused on one concern

### 4. LLM Provider Interface

All LLM providers **MUST** implement a single interface with:

* `generate_text(prompt: str, **kwargs) -> str`
* `list_models() -> List[str]`
* Unified error handling

### 5. Dependency Injection

Agents receive LLM provider instances via dependency injection.

No hard-coded provider instantiation inside agent classes.

### 6. Incognito Mode (No Persistence)

* Session state stays **in memory only**
* No database, no file persistence of session data
* Optional session temp folder allowed **only** under `/tmp/<session_id>/`
* Temp folder cleaned on session end

---

## **HITL (Human-In-The-Loop) Rules**

### 1. HITL is Mandatory

Human-In-The-Loop is **mandatory** for every iteration.

### 2. No Auto-Advancement

System must **never** auto-advance to next iteration without explicit human approval.

### 3. Reviewer Constraints

Each reviewer agent produces **maximum 5–8 bullet points** of feedback.

### 4. Presenter Input Control

Presenter reads **only approved** feedback from the previous iteration.

---

## **Security Rules**

### 1. API Key Protection

* Never store API keys to disk
* Use environment variables or in-memory session state only
* Keys are cleared on session end

### 2. File Upload Security

* Never store user-uploaded files beyond temporary session folder
* Clean up temp files on session termination
* No persistence of uploaded content

---

## **Testing Rules**

### 1. Test Coverage

For every module created, generate corresponding unit tests.

### 2. Test Success Requirement

All tests must pass before committing code.

### 3. Mock LLM Providers

Use mock LLM providers for tests (no real API calls in test suite).

### 4. Test Isolation

Tests must not depend on external services or persistent state.

---

## **Code Style Rules**

### 1. Type Hints

All function signatures must include type hints for parameters and return values.

### 2. Docstrings

All public functions and classes must have docstrings following Google style.

### 3. Error Handling

* Use explicit exception handling
* Provide meaningful error messages
* Log errors appropriately

### 4. Naming Conventions

* Classes: PascalCase
* Functions/methods: snake_case
* Constants: UPPER_SNAKE_CASE
* Private members: _leading_underscore

---

## **Version Control Rules**

### 1. Commit Messages

Use clear, descriptive commit messages following conventional commits format.

### 2. Branch Strategy

* `main` — stable production code
* `develop` — integration branch
* Feature branches from `develop`

### 3. Code Review

All changes require code review before merging.

---

**These rules are non-negotiable and must be followed strictly.**

