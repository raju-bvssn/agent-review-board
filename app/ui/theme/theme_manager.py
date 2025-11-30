"""Theme Manager for Agent Review Board UI.

This module provides safe CSS injection for the Liquid Glass theme.
It does NOT modify any application logic, only visual presentation.

Usage:
    from app.ui.theme.theme_manager import apply_liquid_glass_theme
    apply_liquid_glass_theme()
"""

import os
from pathlib import Path
from typing import Optional


class ThemeManager:
    """Manages theme CSS loading and injection for Streamlit UI.
    
    This class handles safe CSS loading without modifying any application logic.
    It only affects visual presentation through CSS injection.
    """
    
    _css_cache: Optional[str] = None
    _theme_loaded: bool = False
    
    @staticmethod
    def get_theme_path() -> Path:
        """Get the absolute path to the theme directory.
        
        Returns:
            Path object pointing to the theme directory
        """
        current_file = Path(__file__).resolve()
        theme_dir = current_file.parent
        return theme_dir
    
    @staticmethod
    def load_css(css_filename: str = "liquid_glass.css") -> str:
        """Load CSS content from file.
        
        This method reads the CSS file and caches it for performance.
        It does NOT modify any application logic.
        
        Args:
            css_filename: Name of the CSS file to load
            
        Returns:
            CSS content as a string
            
        Raises:
            FileNotFoundError: If CSS file doesn't exist
        """
        # Return cached version if available
        if ThemeManager._css_cache is not None:
            return ThemeManager._css_cache
        
        # Load CSS file
        theme_path = ThemeManager.get_theme_path()
        css_file = theme_path / css_filename
        
        if not css_file.exists():
            raise FileNotFoundError(
                f"CSS file not found: {css_file}\n"
                f"Expected location: {theme_path}"
            )
        
        with open(css_file, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        # Cache the CSS
        ThemeManager._css_cache = css_content
        
        return css_content
    
    @staticmethod
    def get_css_injection_html(css_content: str) -> str:
        """Wrap CSS content in HTML style tags for injection.
        
        This creates the HTML string that can be safely injected via st.markdown().
        It does NOT modify any application logic.
        
        Args:
            css_content: Raw CSS content
            
        Returns:
            HTML string with style tags containing the CSS
        """
        return f"""
        <style>
        {css_content}
        </style>
        """
    
    @staticmethod
    def is_theme_loaded() -> bool:
        """Check if theme has been loaded in current session.
        
        Returns:
            True if theme is already loaded, False otherwise
        """
        return ThemeManager._theme_loaded
    
    @staticmethod
    def mark_theme_loaded():
        """Mark theme as loaded for current session."""
        ThemeManager._theme_loaded = True
    
    @staticmethod
    def reset_cache():
        """Reset CSS cache and loaded state.
        
        Useful for development/testing when CSS file changes.
        """
        ThemeManager._css_cache = None
        ThemeManager._theme_loaded = False


# ==============================================================================
# PUBLIC API - Use these functions to apply theme
# ==============================================================================

def get_liquid_glass_css() -> str:
    """Get the Liquid Glass theme CSS content.
    
    This is the main function to retrieve CSS for injection.
    It handles caching and error handling.
    
    Returns:
        CSS content as string
        
    Example:
        css = get_liquid_glass_css()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    """
    try:
        return ThemeManager.load_css("liquid_glass.css")
    except FileNotFoundError as e:
        # Fallback: return minimal CSS if file not found
        print(f"Warning: {str(e)}")
        return "/* Liquid Glass CSS file not found */"
    except Exception as e:
        print(f"Error loading theme CSS: {str(e)}")
        return "/* Error loading theme CSS */"


def get_theme_injection_html() -> str:
    """Get complete HTML for theme CSS injection via st.markdown().
    
    This returns ready-to-use HTML that can be directly passed to st.markdown()
    with unsafe_allow_html=True.
    
    Returns:
        HTML string with embedded CSS
        
    Example:
        st.markdown(get_theme_injection_html(), unsafe_allow_html=True)
    """
    css_content = get_liquid_glass_css()
    return ThemeManager.get_css_injection_html(css_content)


def apply_liquid_glass_theme_once():
    """Apply Liquid Glass theme only once per session.
    
    This function checks if theme is already loaded and only applies it once.
    Prevents duplicate CSS injection in Streamlit reruns.
    
    Returns:
        HTML string for injection, or empty string if already loaded
        
    Example:
        theme_html = apply_liquid_glass_theme_once()
        if theme_html:
            st.markdown(theme_html, unsafe_allow_html=True)
    """
    if ThemeManager.is_theme_loaded():
        return ""
    
    ThemeManager.mark_theme_loaded()
    return get_theme_injection_html()


def reset_theme_cache():
    """Reset theme cache - useful for development.
    
    Call this when CSS file changes and you want to reload it.
    """
    ThemeManager.reset_cache()


# ==============================================================================
# SAFE CSS INJECTION HELPERS
# ==============================================================================

def inject_custom_css(css_content: str) -> str:
    """Create HTML for injecting custom CSS.
    
    This is a utility function for injecting any custom CSS,
    not just the theme CSS.
    
    Args:
        css_content: Raw CSS content
        
    Returns:
        HTML string with style tags
        
    Example:
        custom_css = "body { color: red; }"
        st.markdown(inject_custom_css(custom_css), unsafe_allow_html=True)
    """
    return f"""
    <style>
    {css_content}
    </style>
    """


def get_neon_glow_css(color: str = "#00d4ff") -> str:
    """Generate CSS for neon glow effect on an element.
    
    Args:
        color: Hex color for the glow
        
    Returns:
        CSS snippet for neon glow
        
    Example:
        glow_css = get_neon_glow_css("#ff00e5")
        st.markdown(inject_custom_css(glow_css), unsafe_allow_html=True)
    """
    return f"""
    .neon-glow {{
        box-shadow: 0 0 10px {color}40,
                    0 0 20px {color}30,
                    0 0 30px {color}20;
        border: 1px solid {color}60;
    }}
    """


def get_glass_card_css(blur_amount: str = "16px", opacity: float = 0.05) -> str:
    """Generate CSS for a glass card effect.
    
    Args:
        blur_amount: Backdrop blur amount (e.g., "16px")
        opacity: Background opacity (0.0 to 1.0)
        
    Returns:
        CSS snippet for glass card
        
    Example:
        card_css = get_glass_card_css(blur_amount="20px", opacity=0.08)
        st.markdown(inject_custom_css(card_css), unsafe_allow_html=True)
    """
    return f"""
    .custom-glass-card {{
        background: rgba(255, 255, 255, {opacity});
        backdrop-filter: blur({blur_amount});
        -webkit-backdrop-filter: blur({blur_amount});
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 24px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }}
    """


# ==============================================================================
# DOCUMENTATION & USAGE EXAMPLES
# ==============================================================================

"""
USAGE EXAMPLES:

1. Basic Theme Application (in streamlit_app.py or any page):
   
   from app.ui.theme.theme_manager import get_theme_injection_html
   
   # At the top of your page
   st.markdown(get_theme_injection_html(), unsafe_allow_html=True)


2. Apply Theme Once Per Session:
   
   from app.ui.theme.theme_manager import apply_liquid_glass_theme_once
   
   # This will only inject CSS on first run
   theme_html = apply_liquid_glass_theme_once()
   if theme_html:
       st.markdown(theme_html, unsafe_allow_html=True)


3. Custom CSS Injection:
   
   from app.ui.theme.theme_manager import inject_custom_css
   
   custom_css = '''
   .my-element {
       color: blue;
   }
   '''
   st.markdown(inject_custom_css(custom_css), unsafe_allow_html=True)


4. Development - Reset Cache When CSS Changes:
   
   from app.ui.theme.theme_manager import reset_theme_cache
   
   # Call this when you edit liquid_glass.css
   reset_theme_cache()


IMPORTANT NOTES:

- This module ONLY handles CSS injection
- It does NOT modify any application logic
- It does NOT change function signatures
- It does NOT alter button callbacks or state management
- It does NOT interfere with agent execution or HITL workflow
- It is purely for visual presentation

The theme can be safely applied/removed without affecting functionality.
"""

