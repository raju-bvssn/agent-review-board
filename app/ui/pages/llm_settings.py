"""LLM Settings page for configuring LLM providers."""

import streamlit as st
from app.llm.provider_factory import ProviderFactory


def render():
    """Render the LLM Settings page.
    
    This page allows users to:
    - Select LLM provider (including FREE options)
    - Enter API key (masked, stored in memory only)
    - Test connection
    - View available models
    """
    
    # Header
    st.title("⚙️ LLM Settings")
    st.subheader("Configure Your LLM Provider")
    
    # Security notice
    st.info("🔒 **Privacy Notice** — API keys are stored in memory only and never saved to disk")
    
    st.markdown("---")
    
    # Provider selection
    st.header("Select Provider")
    
    # Get available providers
    available_providers = ProviderFactory.get_available_providers()
    free_providers = ProviderFactory.get_free_providers()
    
    # Create display names with FREE indicators
    provider_display = {
        "mock": "Mock Provider (Testing - No Setup Required)",
        "openai": "OpenAI (GPT-4, GPT-3.5) - Paid",
        "anthropic": "Anthropic (Claude 3.5 Sonnet) - Paid",
        "gemini": "🆓 Google Gemini (gemini-1.5-flash FREE)",
        "huggingface": "🆓 HuggingFace (falcon-7b FREE)",
        "ollama": "🆓 Ollama (Local - llama3, mistral, phi3, etc.)"
    }
    
    provider_options = [provider_display.get(p, p) for p in available_providers]
    
    selected_display = st.selectbox(
        "LLM Provider",
        provider_options,
        help="Select the LLM provider you want to use. 🆓 = Free or has free tier"
    )
    
    # Get actual provider name
    selected_provider = None
    for key, value in provider_display.items():
        if value == selected_display:
            selected_provider = key
            break
    
    # Show provider information
    provider_info = ProviderFactory.get_provider_info(selected_provider)
    if provider_info:
        if provider_info.get('free'):
            st.success(f"✅ {provider_info['description']}")
        else:
            st.info(f"ℹ️ {provider_info['description']}")
    
    st.markdown("---")
    
    # Provider-specific configuration
    api_key = None
    
    # GEMINI CONFIGURATION
    if selected_provider == 'gemini':
        st.subheader("🔑 Gemini API Configuration")
        
        st.caption(
            "Get your FREE API key from: "
            "[Google AI Studio](https://makersuite.google.com/app/apikey)"
        )
        
        api_key = st.text_input(
            "GEMINI_API_KEY",
            type="password",
            placeholder="Enter your Gemini API key",
            help="FREE tier: 15 requests per minute with gemini-1.5-flash"
        )
        
        if not api_key:
            st.warning("⚠️ API key required for Gemini")
    
    # HUGGINGFACE CONFIGURATION
    elif selected_provider == 'huggingface':
        st.subheader("🔑 HuggingFace API Configuration")
        
        st.caption(
            "Get your FREE API token from: "
            "[HuggingFace Settings](https://huggingface.co/settings/tokens)"
        )
        
        api_key = st.text_input(
            "HUGGINGFACE_API_KEY",
            type="password",
            placeholder="Enter your HuggingFace API token",
            help="FREE models available: falcon-7b-instruct, mistral-7b, etc."
        )
        
        if not api_key:
            st.warning("⚠️ API token required for HuggingFace")
    
    # OLLAMA CONFIGURATION (LOCAL - NO KEY)
    elif selected_provider == 'ollama':
        st.subheader("🖥️ Ollama Local Setup")
        
        st.info(
            "**Ollama runs locally on your machine - No API key required!**\n\n"
            "1. Download Ollama: [https://ollama.com/download](https://ollama.com/download)\n"
            "2. Install and start Ollama\n"
            "3. Pull models: `ollama pull llama3` or `ollama pull mistral`\n"
            "4. Ollama runs at `http://localhost:11434`"
        )
        
        # Check connection button
        col1, col2 = st.columns([1, 2])
        with col1:
            check_ollama = st.button(
                "🔍 Check Local Connection",
                use_container_width=True,
                type="secondary"
            )
        
        if check_ollama:
            with st.spinner("Checking Ollama connection..."):
                try:
                    from app.llm.ollama_provider import OllamaProvider
                    
                    provider = OllamaProvider()
                    
                    if provider.is_running():
                        st.success("✅ Ollama is running!")
                        
                        version = provider.get_ollama_version()
                        if version:
                            st.caption(f"Version: {version}")
                        
                        # Show available models
                        models = provider.list_models()
                        if models:
                            st.info(f"Found {len(models)} local models")
                    else:
                        st.error(
                            "❌ Ollama is not running. "
                            "Please start Ollama first."
                        )
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # OPENAI CONFIGURATION
    elif selected_provider == 'openai':
        st.subheader("🔑 OpenAI API Configuration")
        
        st.caption(
            "Get your API key from: "
            "[OpenAI Platform](https://platform.openai.com/api-keys)"
        )
        
        api_key = st.text_input(
            "OPENAI_API_KEY",
            type="password",
            placeholder="Enter your OpenAI API key",
            help="Required for GPT-4, GPT-3.5-turbo, etc."
        )
        
        if not api_key:
            st.warning("⚠️ API key required for OpenAI")
    
    # ANTHROPIC CONFIGURATION
    elif selected_provider == 'anthropic':
        st.subheader("🔑 Anthropic API Configuration")
        
        st.caption(
            "Get your API key from: "
            "[Anthropic Console](https://console.anthropic.com/)"
        )
        
        api_key = st.text_input(
            "ANTHROPIC_API_KEY",
            type="password",
            placeholder="Enter your Anthropic API key",
            help="Required for Claude 3.5 Sonnet, Claude 3 Opus, etc."
        )
        
        if not api_key:
            st.warning("⚠️ API key required for Anthropic")
    
    # MOCK CONFIGURATION
    elif selected_provider == 'mock':
        st.success("✅ Mock Provider selected - No API key required (for testing)")
        st.caption("The Mock Provider returns deterministic responses for testing purposes")
    
    st.markdown("---")
    
    # Model selection (if provider is configured)
    if 'llm_config' in st.session_state and st.session_state.llm_config.get('provider') == selected_provider:
        if 'available_models' in st.session_state and st.session_state.available_models:
            st.header("📋 Select Model")
            
            models = st.session_state.available_models
            
            # Get default/recommended model for free providers
            default_model = None
            if selected_provider == 'gemini':
                default_model = 'gemini-1.5-flash'
            elif selected_provider == 'huggingface':
                default_model = 'tiiuae/falcon-7b-instruct'
            elif selected_provider == 'ollama':
                default_model = 'llama3'
            
            # Pre-select default if available
            default_index = 0
            if default_model and default_model in models:
                default_index = models.index(default_model)
            
            selected_model = st.selectbox(
                "Model",
                models,
                index=default_index,
                help="Select the specific model to use"
            )
            
            # Highlight free models
            if selected_provider == 'gemini' and 'flash' in selected_model.lower():
                st.success("✅ FREE tier model selected")
            elif selected_provider == 'huggingface':
                st.success("✅ FREE model selected")
            elif selected_provider == 'ollama':
                st.success("✅ FREE local model")
            
            # Store selected model
            st.session_state.llm_config['model'] = selected_model
    
    st.markdown("---")
    
    # Connection testing section
    st.header("🔌 Test Connection")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        test_button_clicked = st.button(
            "Test Connection",
            use_container_width=True,
            type="primary",
            disabled=(ProviderFactory.requires_api_key(selected_provider) and not api_key)
        )
    
    if test_button_clicked:
        with st.spinner("Testing connection..."):
            try:
                # Create provider instance
                provider = ProviderFactory.create_provider(
                    selected_provider,
                    api_key=api_key if api_key else None
                )
                
                # Test connection
                is_valid = provider.validate_connection()
                
                if is_valid:
                    st.success("✅ Connection successful!")
                    
                    # Get and display available models
                    st.subheader("Available Models")
                    
                    models = provider.list_models()
                    
                    if models:
                        st.info(f"Found {len(models)} models:")
                        
                        # Display models in columns
                        cols = st.columns(2)
                        for i, model in enumerate(models):
                            with cols[i % 2]:
                                # Highlight free models
                                if selected_provider == 'gemini' and 'flash' in model.lower():
                                    st.text(f"🆓 {model}")
                                elif selected_provider in ('huggingface', 'ollama', 'mock'):
                                    st.text(f"🆓 {model}")
                                else:
                                    st.text(f"• {model}")
                        
                        # Store configuration in session state
                        if 'llm_config' not in st.session_state:
                            st.session_state.llm_config = {}
                        
                        st.session_state.llm_config['provider'] = selected_provider
                        st.session_state.llm_config['api_key'] = api_key
                        st.session_state.available_models = models
                        
                        # Auto-select default free model
                        if selected_provider == 'gemini':
                            default = 'gemini-1.5-flash'
                            if default in models:
                                st.session_state.llm_config['model'] = default
                        elif selected_provider == 'huggingface':
                            default = 'tiiuae/falcon-7b-instruct'
                            if default in models:
                                st.session_state.llm_config['model'] = default
                        elif selected_provider == 'ollama':
                            if 'llama3' in models:
                                st.session_state.llm_config['model'] = 'llama3'
                            elif models:
                                st.session_state.llm_config['model'] = models[0]
                        
                        st.success("✅ Configuration saved to session!")
                    else:
                        st.warning("No models found")
                else:
                    st.error("❌ Connection failed - Please check your configuration")
            
            except ValueError as e:
                st.error(f"❌ Configuration error: {str(e)}")
            
            except ImportError as e:
                st.error(f"❌ Missing dependency: {str(e)}")
                st.caption("Run: `pip install -r requirements.txt`")
            
            except Exception as e:
                st.error(f"❌ Connection failed: {str(e)}")
    
    st.markdown("---")
    
    # Current configuration display
    st.header("📊 Current Configuration")
    
    if 'llm_config' in st.session_state and st.session_state.llm_config.get('provider'):
        config = st.session_state.llm_config
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            provider_name = config.get('provider', 'Not configured').upper()
            st.metric("Provider", provider_name)
        
        with col2:
            if config.get('model'):
                st.metric("Model", config.get('model'))
            else:
                st.metric("Model", "Not selected")
        
        with col3:
            if ProviderFactory.requires_api_key(config.get('provider')):
                api_key_status = "✅ Set" if config.get('api_key') else "❌ Missing"
            else:
                api_key_status = "Not required"
            st.metric("API Key", api_key_status)
        
        if 'available_models' in st.session_state:
            st.caption(f"📋 {len(st.session_state.available_models)} models available")
            
            with st.expander("View All Models"):
                for model in st.session_state.available_models:
                    st.text(f"• {model}")
    else:
        st.info("No provider configured yet. Select a provider and test connection.")
    
    st.markdown("---")
    
    # Advanced settings
    with st.expander("🔧 Advanced Settings"):
        st.caption("Configure default generation parameters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            temperature = st.slider(
                "Default Temperature",
                0.0, 2.0, 0.7, 0.1,
                help="Controls randomness in generation (0=deterministic, 2=very random)"
            )
        
        with col2:
            max_tokens = st.number_input(
                "Default Max Tokens",
                value=2000,
                min_value=100,
                max_value=8000,
                step=100,
                help="Maximum number of tokens to generate"
            )
        
        timeout = st.number_input(
            "Request Timeout (seconds)",
            value=30,
            min_value=10,
            max_value=120,
            step=5,
            help="Timeout for API requests"
        )
        
        if st.button("Save Advanced Settings"):
            if 'llm_config' not in st.session_state:
                st.session_state.llm_config = {}
            
            st.session_state.llm_config['temperature'] = temperature
            st.session_state.llm_config['max_tokens'] = max_tokens
            st.session_state.llm_config['timeout'] = timeout
            
            st.success("✅ Advanced settings saved!")
    
    # Quick links
    st.markdown("---")
    st.caption("**Quick Links:**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.caption("[OpenAI API](https://platform.openai.com/api-keys)")
    with col2:
        st.caption("[Anthropic Console](https://console.anthropic.com/)")
    with col3:
        st.caption("[Google AI Studio](https://makersuite.google.com/app/apikey)")
    with col4:
        st.caption("[Ollama Download](https://ollama.com/download)")
