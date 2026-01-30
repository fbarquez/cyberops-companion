"""
Custom CSS Styles for IR Companion

Professional, clean UI with clear visual hierarchy.
Supports light and dark themes via CSS custom properties.
"""

# Theme CSS custom properties
THEME_VARIABLES = """
<style>
:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f0f2f6;
    --bg-tertiary: #e9ecef;
    --text-primary: #262730;
    --text-secondary: #6c757d;
    --text-muted: #888888;
    --border-color: #e0e0e0;
    --accent-primary: #007bff;
    --accent-success: #28a745;
    --accent-warning: #ffc107;
    --accent-danger: #dc3545;
    --accent-info: #17a2b8;
    --card-bg: #ffffff;
    --card-shadow: rgba(0,0,0,0.05);
    --hover-bg: #f0f0f0;
    --phase-pending: #e9ecef;
    --phase-current: #007bff;
    --phase-completed: #28a745;
}

[data-theme="dark"] {
    --bg-primary: #0e1117;
    --bg-secondary: #262730;
    --bg-tertiary: #1a1a2e;
    --text-primary: #fafafa;
    --text-secondary: #a0a0a0;
    --text-muted: #888888;
    --border-color: #3d3d3d;
    --accent-primary: #4da6ff;
    --accent-success: #3dd56d;
    --accent-warning: #ffd93d;
    --accent-danger: #ff6b6b;
    --accent-info: #4fc3f7;
    --card-bg: #1e1e2e;
    --card-shadow: rgba(0,0,0,0.3);
    --hover-bg: #2d2d3d;
    --phase-pending: #3d3d4d;
    --phase-current: #4da6ff;
    --phase-completed: #3dd56d;
}

/* Apply theme to Streamlit app */
[data-theme="dark"] .stApp {
    background-color: var(--bg-primary);
    color: var(--text-primary);
}

[data-theme="dark"] .stSidebar {
    background-color: var(--bg-secondary);
}

[data-theme="dark"] .stTextInput > div > div > input,
[data-theme="dark"] .stTextArea > div > div > textarea,
[data-theme="dark"] .stSelectbox > div > div > select {
    background-color: var(--bg-tertiary);
    color: var(--text-primary);
    border-color: var(--border-color);
}

[data-theme="dark"] .stButton > button {
    background-color: var(--accent-primary);
    color: var(--text-primary);
}

[data-theme="dark"] .stExpander {
    background-color: var(--card-bg);
    border-color: var(--border-color);
}
</style>
"""

MAIN_STYLES = """
<style>
/* General improvements */
.stApp {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Phase progress bar */
.phase-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    margin: 20px 0;
}

.phase-step {
    flex: 1;
    text-align: center;
    position: relative;
    padding: 10px 5px;
}

.phase-step::after {
    content: '';
    position: absolute;
    top: 50%;
    right: -50%;
    width: 100%;
    height: 2px;
    background: #ddd;
    z-index: 0;
}

.phase-step:last-child::after {
    display: none;
}

.phase-dot {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    margin: 0 auto 5px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: bold;
    position: relative;
    z-index: 1;
}

.phase-dot.completed { background: #28a745; color: white; }
.phase-dot.current { background: #007bff; color: white; box-shadow: 0 0 0 3px rgba(0,123,255,0.3); }
.phase-dot.pending { background: #e9ecef; color: #6c757d; }

.phase-label {
    font-size: 11px;
    color: #666;
    margin-top: 4px;
}

.phase-label.current {
    color: #007bff;
    font-weight: 600;
}

/* Timer display */
.timer-display {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    color: #fff;
    padding: 12px 20px;
    border-radius: 8px;
    font-family: 'Monaco', 'Courier New', monospace;
    font-size: 24px;
    text-align: center;
    margin: 10px 0;
}

.timer-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #888;
    margin-bottom: 4px;
}

/* Status cards */
.status-card {
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 16px;
    margin: 8px 0;
}

.status-card.warning {
    border-left: 4px solid #ffc107;
    background: #fffbf0;
}

.status-card.danger {
    border-left: 4px solid #dc3545;
    background: #fff5f5;
}

.status-card.success {
    border-left: 4px solid #28a745;
    background: #f0fff4;
}

.status-card.info {
    border-left: 4px solid #17a2b8;
    background: #f0f9ff;
}

/* Forensic warning banner */
.forensic-banner {
    background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
    color: white;
    padding: 12px 16px;
    border-radius: 6px;
    margin: 10px 0;
    font-weight: 500;
}

.forensic-banner-icon {
    font-size: 18px;
    margin-right: 8px;
}

/* Checklist items */
.checklist-item {
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 12px 16px;
    margin: 8px 0;
    display: flex;
    align-items: center;
    transition: all 0.2s;
}

.checklist-item:hover {
    border-color: #007bff;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.checklist-item.mandatory {
    border-left: 3px solid #dc3545;
}

.checklist-item.forensic {
    border-left: 3px solid #ffc107;
}

.checklist-item.completed {
    background: #f8f9fa;
    opacity: 0.7;
}

/* Quick action buttons */
.quick-action {
    background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
    color: white;
    padding: 20px;
    border-radius: 8px;
    text-align: center;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    margin: 8px 0;
}

.quick-action:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.quick-action-icon {
    font-size: 24px;
    margin-bottom: 8px;
}

.quick-action-label {
    font-weight: 600;
    font-size: 14px;
}

/* Severity badges */
.severity-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
}

.severity-critical { background: #dc3545; color: white; }
.severity-high { background: #fd7e14; color: white; }
.severity-medium { background: #ffc107; color: #333; }
.severity-low { background: #28a745; color: white; }

/* Navigation highlight */
.nav-item {
    padding: 8px 12px;
    border-radius: 6px;
    margin: 4px 0;
    cursor: pointer;
    transition: background 0.2s;
}

.nav-item:hover {
    background: #f0f0f0;
}

.nav-item.active {
    background: #e7f1ff;
    border-left: 3px solid #007bff;
}

/* Scenario cards */
.scenario-card {
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 20px;
    margin: 12px 0;
    cursor: pointer;
    transition: all 0.2s;
}

.scenario-card:hover {
    border-color: #007bff;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.scenario-difficulty {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
}

.difficulty-beginner { background: #d4edda; color: #155724; }
.difficulty-intermediate { background: #fff3cd; color: #856404; }
.difficulty-advanced { background: #f8d7da; color: #721c24; }

/* Hide streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""

def inject_styles(theme: str = "light"):
    """Inject custom CSS styles into the Streamlit app.

    Args:
        theme: "light" or "dark"
    """
    import streamlit as st

    # Inject theme variables
    st.markdown(THEME_VARIABLES, unsafe_allow_html=True)

    # Inject main styles
    st.markdown(MAIN_STYLES, unsafe_allow_html=True)

    # Apply theme attribute to root element
    theme_script = f"""
    <script>
        document.documentElement.setAttribute('data-theme', '{theme}');
    </script>
    """
    st.markdown(theme_script, unsafe_allow_html=True)


def get_theme_toggle_html(current_theme: str) -> str:
    """Generate HTML for theme toggle button.

    Args:
        current_theme: Current theme ("light" or "dark")

    Returns:
        HTML string for the toggle
    """
    icon = "☀️" if current_theme == "dark" else "🌙"
    label = "Light Mode" if current_theme == "dark" else "Dark Mode"
    return f"{icon} {label}"
