"""
Keyboard Shortcuts for ISORA

Provides keyboard navigation and shortcuts for common actions.
Uses JavaScript injection since Streamlit has limited native keyboard support.
"""

import streamlit as st
from typing import Dict, List, Optional


# Shortcut definitions
SHORTCUTS = {
    "Ctrl+1": {"action": "nav_phase_1", "description": "Go to Phase 1 (Detection)"},
    "Ctrl+2": {"action": "nav_phase_2", "description": "Go to Phase 2 (Analysis)"},
    "Ctrl+3": {"action": "nav_phase_3", "description": "Go to Phase 3 (Containment)"},
    "Ctrl+4": {"action": "nav_phase_4", "description": "Go to Phase 4 (Eradication)"},
    "Ctrl+5": {"action": "nav_phase_5", "description": "Go to Phase 5 (Recovery)"},
    "Ctrl+6": {"action": "nav_phase_6", "description": "Go to Phase 6 (Post-Incident)"},
    "Ctrl+E": {"action": "new_evidence", "description": "Add new evidence entry"},
    "Ctrl+D": {"action": "export", "description": "Export/Download report"},
    "Ctrl+H": {"action": "home", "description": "Go to home/dashboard"},
    "Ctrl+/": {"action": "help", "description": "Show keyboard shortcuts help"},
    "Escape": {"action": "close_modal", "description": "Close modal/dialog"},
}

SHORTCUT_TRANSLATIONS = {
    "en": {
        "title": "Keyboard Shortcuts",
        "navigation": "Navigation",
        "actions": "Actions",
        "general": "General",
        "press_to_close": "Press Escape or click outside to close",
    },
    "de": {
        "title": "Tastenkurzel",
        "navigation": "Navigation",
        "actions": "Aktionen",
        "general": "Allgemein",
        "press_to_close": "Escape drucken oder ausserhalb klicken zum Schliessen",
    },
}


def get_keyboard_shortcuts_js() -> str:
    """Generate JavaScript for keyboard shortcut handling.

    Returns:
        JavaScript code as string
    """
    return """
    <script>
    (function() {
        // Prevent duplicate listeners
        if (window.irCompanionShortcutsInitialized) return;
        window.irCompanionShortcutsInitialized = true;

        // Shortcut action handlers
        const shortcutActions = {
            'nav_phase_1': () => navigateToView('checklist', 'detection'),
            'nav_phase_2': () => navigateToView('checklist', 'analysis'),
            'nav_phase_3': () => navigateToView('checklist', 'containment'),
            'nav_phase_4': () => navigateToView('checklist', 'eradication'),
            'nav_phase_5': () => navigateToView('checklist', 'recovery'),
            'nav_phase_6': () => navigateToView('checklist', 'post_incident'),
            'new_evidence': () => navigateToView('evidence'),
            'export': () => navigateToView('export'),
            'home': () => navigateToView('dashboard'),
            'help': () => toggleShortcutsHelp(),
            'close_modal': () => closeShortcutsHelp(),
        };

        // Navigate by clicking sidebar buttons
        function navigateToView(view, phase) {
            // Find and click the appropriate sidebar button
            const buttons = document.querySelectorAll('[data-testid="stSidebar"] button');
            buttons.forEach(btn => {
                if (btn.textContent.toLowerCase().includes(view.toLowerCase())) {
                    btn.click();
                }
            });

            // For phase navigation, we need to store the target phase
            if (phase) {
                sessionStorage.setItem('cyberops_companion_target_phase', phase);
            }
        }

        // Show/hide shortcuts help modal
        function toggleShortcutsHelp() {
            const modal = document.getElementById('shortcuts-help-modal');
            if (modal) {
                modal.style.display = modal.style.display === 'none' ? 'flex' : 'none';
            }
        }

        function closeShortcutsHelp() {
            const modal = document.getElementById('shortcuts-help-modal');
            if (modal) {
                modal.style.display = 'none';
            }
        }

        // Key event handler
        document.addEventListener('keydown', function(e) {
            // Don't trigger shortcuts when typing in inputs
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                // Allow Escape to close modals even in inputs
                if (e.key === 'Escape') {
                    shortcutActions['close_modal']();
                }
                return;
            }

            let shortcutKey = '';

            // Build the shortcut key string
            if (e.ctrlKey || e.metaKey) shortcutKey += 'Ctrl+';
            if (e.altKey) shortcutKey += 'Alt+';
            if (e.shiftKey) shortcutKey += 'Shift+';

            // Handle special keys
            if (e.key === 'Escape') {
                shortcutKey = 'Escape';
            } else if (e.key === '/') {
                shortcutKey += '/';
            } else if (e.key >= '1' && e.key <= '9') {
                shortcutKey += e.key;
            } else if (e.key.length === 1) {
                shortcutKey += e.key.toUpperCase();
            }

            // Shortcut mappings
            const shortcuts = {
                'Ctrl+1': 'nav_phase_1',
                'Ctrl+2': 'nav_phase_2',
                'Ctrl+3': 'nav_phase_3',
                'Ctrl+4': 'nav_phase_4',
                'Ctrl+5': 'nav_phase_5',
                'Ctrl+6': 'nav_phase_6',
                'Ctrl+E': 'new_evidence',
                'Ctrl+D': 'export',
                'Ctrl+H': 'home',
                'Ctrl+/': 'help',
                'Escape': 'close_modal',
            };

            if (shortcuts[shortcutKey]) {
                e.preventDefault();
                const action = shortcuts[shortcutKey];
                if (shortcutActions[action]) {
                    shortcutActions[action]();
                }
            }
        });

        console.log('ISORA keyboard shortcuts initialized');
    })();
    </script>
    """


def get_shortcuts_help_modal_html(lang: str = "en") -> str:
    """Generate HTML for the shortcuts help modal.

    Args:
        lang: Language code

    Returns:
        HTML string for the modal
    """
    labels = SHORTCUT_TRANSLATIONS.get(lang, SHORTCUT_TRANSLATIONS["en"])

    return f"""
    <div id="shortcuts-help-modal" style="
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        z-index: 9999;
        justify-content: center;
        align-items: center;
    " onclick="if(event.target === this) this.style.display='none'">
        <div style="
            background: var(--bg-primary, #ffffff);
            color: var(--text-primary, #262730);
            padding: 24px 32px;
            border-radius: 12px;
            max-width: 500px;
            width: 90%;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        " onclick="event.stopPropagation()">
            <h2 style="margin-top: 0; margin-bottom: 20px; border-bottom: 1px solid var(--border-color, #e0e0e0); padding-bottom: 12px;">
                {labels['title']}
            </h2>

            <h4 style="margin-bottom: 8px; color: var(--accent-primary, #007bff);">
                {labels['navigation']}
            </h4>
            <table style="width: 100%; margin-bottom: 16px; font-size: 14px;">
                <tr><td style="padding: 4px 0;"><kbd style="background: var(--bg-secondary, #f0f2f6); padding: 2px 6px; border-radius: 4px; font-family: monospace;">Ctrl+1-6</kbd></td><td>Navigate to Phase 1-6</td></tr>
                <tr><td style="padding: 4px 0;"><kbd style="background: var(--bg-secondary, #f0f2f6); padding: 2px 6px; border-radius: 4px; font-family: monospace;">Ctrl+H</kbd></td><td>Go to Dashboard</td></tr>
            </table>

            <h4 style="margin-bottom: 8px; color: var(--accent-primary, #007bff);">
                {labels['actions']}
            </h4>
            <table style="width: 100%; margin-bottom: 16px; font-size: 14px;">
                <tr><td style="padding: 4px 0;"><kbd style="background: var(--bg-secondary, #f0f2f6); padding: 2px 6px; border-radius: 4px; font-family: monospace;">Ctrl+E</kbd></td><td>Add Evidence</td></tr>
                <tr><td style="padding: 4px 0;"><kbd style="background: var(--bg-secondary, #f0f2f6); padding: 2px 6px; border-radius: 4px; font-family: monospace;">Ctrl+D</kbd></td><td>Export/Download</td></tr>
            </table>

            <h4 style="margin-bottom: 8px; color: var(--accent-primary, #007bff);">
                {labels['general']}
            </h4>
            <table style="width: 100%; margin-bottom: 16px; font-size: 14px;">
                <tr><td style="padding: 4px 0;"><kbd style="background: var(--bg-secondary, #f0f2f6); padding: 2px 6px; border-radius: 4px; font-family: monospace;">Ctrl+/</kbd></td><td>Show this help</td></tr>
                <tr><td style="padding: 4px 0;"><kbd style="background: var(--bg-secondary, #f0f2f6); padding: 2px 6px; border-radius: 4px; font-family: monospace;">Escape</kbd></td><td>Close modal</td></tr>
            </table>

            <p style="font-size: 12px; color: var(--text-secondary, #6c757d); margin-bottom: 0; text-align: center;">
                {labels['press_to_close']}
            </p>
        </div>
    </div>
    """


def inject_keyboard_shortcuts(lang: str = "en") -> None:
    """Inject keyboard shortcut handling JavaScript and help modal into the page.

    Args:
        lang: Language code for help modal labels
    """
    # Inject the JavaScript handler
    st.markdown(get_keyboard_shortcuts_js(), unsafe_allow_html=True)

    # Inject the help modal HTML
    st.markdown(get_shortcuts_help_modal_html(lang), unsafe_allow_html=True)


def render_shortcuts_help_button(lang: str = "en") -> bool:
    """Render a button that shows the shortcuts help when clicked.

    Args:
        lang: Language code

    Returns:
        True if button was clicked
    """
    labels = SHORTCUT_TRANSLATIONS.get(lang, SHORTCUT_TRANSLATIONS["en"])

    # Create a button that triggers the help modal via JavaScript
    clicked = st.button(
        f"? {labels['title']}",
        key="shortcuts_help_btn",
        help="Press Ctrl+/ to toggle",
    )

    if clicked:
        # Use JavaScript to show the modal
        st.markdown("""
        <script>
            const modal = document.getElementById('shortcuts-help-modal');
            if (modal) modal.style.display = 'flex';
        </script>
        """, unsafe_allow_html=True)

    return clicked


def get_shortcuts_summary(lang: str = "en") -> str:
    """Get a text summary of available shortcuts.

    Args:
        lang: Language code

    Returns:
        Formatted string with shortcuts
    """
    labels = SHORTCUT_TRANSLATIONS.get(lang, SHORTCUT_TRANSLATIONS["en"])

    summary = f"**{labels['title']}**\n\n"
    summary += f"_{labels['navigation']}_\n"
    summary += "- `Ctrl+1-6` - Navigate to Phase 1-6\n"
    summary += "- `Ctrl+H` - Go to Dashboard\n\n"
    summary += f"_{labels['actions']}_\n"
    summary += "- `Ctrl+E` - Add Evidence\n"
    summary += "- `Ctrl+D` - Export/Download\n\n"
    summary += f"_{labels['general']}_\n"
    summary += "- `Ctrl+/` - Show help\n"
    summary += "- `Escape` - Close modal\n"

    return summary
