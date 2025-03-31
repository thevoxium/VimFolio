#!/usr/bin/env python3

import yaml
import os
import json
import markdown
import frontmatter
from pathlib import Path
import sys
import traceback
import html # For basic HTML escaping

# --- Configuration ---
CONFIG_FILE = 'config.yaml'
CONTENT_DIR = Path('content')
BLOG_DIR = CONTENT_DIR / 'blogs'
# ABOUT_FILE = CONTENT_DIR / 'about.md' # No longer hardcoded
# PROJECTS_FILE = CONTENT_DIR / 'projects.md' # No longer hardcoded
OUTPUT_DIR = Path('public')
OUTPUT_FILE = OUTPUT_DIR / 'index.html'

# Special View IDs that have custom processing logic
SPECIAL_VIEWS = {'blogs-list-view', 'blog-content-view', 'socials-view'}

# --- Helper Functions ---

def markdown_to_lines(md_content):
    """
    Converts a Markdown string to a list of line data dictionaries suitable for JS.
    Each line from the resulting HTML becomes an item in the list.
    Handles potential Markdown errors gracefully.
    """
    if not md_content:
        return []
    try:
        # Use common extensions, nl2br helps preserve line breaks from Markdown
        html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables', 'nl2br'])
        lines = html_content.splitlines()
        # Create line data, marking as HTML, filter empty lines
        line_data = [{'text': line, 'isHtml': True} for line in lines if line.strip()]
        return line_data
    except Exception as e:
        print(f"    Warning: Markdown processing error: {e}", file=sys.stderr)
        # Fallback: return plain text lines if markdown fails badly
        lines = md_content.splitlines()
        return [{'text': line, 'isHtml': False} for line in lines if line.strip()]

def create_info_line(text="-- Press Esc to go back --"):
     """Creates the standard dictionary for an info/navigation hint line."""
     return {'text': text, 'type': 'info', 'isHtml': False}

# --- Main Build Logic ---

def build_site():
    """Reads config and content, generates the single index.html file."""
    print("Starting Neovim Portfolio build...")

    # 1. Load Config
    print(f"[*] Reading configuration from '{CONFIG_FILE}'...")
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        if not config:
            print(f"ERROR: Configuration file '{CONFIG_FILE}' is empty or invalid.", file=sys.stderr)
            sys.exit(1)
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found at '{CONFIG_FILE}'", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"ERROR: Failed to parse YAML configuration file '{CONFIG_FILE}': {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred reading config: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

    # --- Extract Config Values (with defaults) ---
    site_title = config.get('site_title', 'Portfolio')
    username = config.get('username', 'user')
    default_theme = config.get('default_theme', 'theme-dracula')
    config_themes = config.get('themes', [])
    main_navigation = config.get('main_navigation', [])
    socials_heading = config.get('socials_heading', 'Socials & Links')
    socials_links_config = config.get('socials_links', [])

    # 2. Process Content Dynamically
    print("[*] Processing content...")

    # Store processed content for standard markdown pages keyed by targetView
    content_view_data = {}
    # Store data for special views separately
    blogs_list_data = []
    blog_content_map = {}
    socials_view_data = []

    # Process main navigation to find content files
    print(f"  - Processing navigation items and associated content...")
    for item in main_navigation:
        target_view = item.get('targetView')
        filename = item.get('filename')

        if not target_view or not filename:
            print(f"    Warning: Skipping navigation item due to missing 'targetView' or 'filename': {item.get('text', 'N/A')}", file=sys.stderr)
            continue

        # Handle standard content pages (assume .md in content/)
        if target_view not in SPECIAL_VIEWS and filename.endswith('.md'):
            content_file_path = CONTENT_DIR / filename
            print(f"    - Processing content page: '{filename}' for view '{target_view}'")
            page_lines = []
            if content_file_path.exists() and content_file_path.is_file():
                try:
                    content_post = frontmatter.load(content_file_path)
                    page_lines = markdown_to_lines(content_post.content)
                    page_lines.append(create_info_line()) # Add standard back hint
                except Exception as e:
                    print(f"      Warning: Failed to process '{content_file_path}': {e}", file=sys.stderr)
            else:
                print(f"      Warning: Content file not found at '{content_file_path}'", file=sys.stderr)
            content_view_data[target_view] = page_lines # Store processed lines (or empty list)

        elif target_view == 'socials-view':
             # Mark socials for processing later (avoids duplicating config read)
             pass # Logic below handles this

        elif target_view == 'blogs-list-view':
             # Mark blogs for processing later (avoids duplicating config read)
             pass # Logic below handles this

    # Process Blogs (if configured in navigation)
    if any(item.get('targetView') == 'blogs-list-view' for item in main_navigation):
        if BLOG_DIR.exists() and BLOG_DIR.is_dir():
            print(f"  - Processing blogs from '{BLOG_DIR}'...")
            blog_files = sorted([f for f in os.listdir(BLOG_DIR) if f.endswith(".md")], reverse=True)
            for filename in blog_files:
                filepath = BLOG_DIR / filename
                blog_id = filename[:-3]
                # print(f"    - Processing blog: '{filename}' (ID: '{blog_id}')") # Less verbose now
                try:
                    post = frontmatter.load(filepath)
                    title = post.metadata.get('title', blog_id.replace('-', ' ').title())
                    date_str = str(post.metadata.get('date', ''))
                    blogs_list_data.append({'title': title, 'id': blog_id})
                    content_lines = markdown_to_lines(post.content)
                    blog_view_lines = []
                    if date_str: blog_view_lines.append({'text': date_str, 'type': 'blog-date'})
                    blog_view_lines.append({'text': title, 'type': 'blog-title'})
                    blog_view_lines.append({'text': ''})
                    blog_view_lines.extend(content_lines)
                    blog_view_lines.append(create_info_line("-- Press Esc to return to blog list --"))
                    blog_content_map[blog_id] = blog_view_lines
                except Exception as e:
                    print(f"    Warning: Failed to process blog post '{filepath}': {e}", file=sys.stderr)
        else:
            print(f"  - Warning: Blog directory '{BLOG_DIR}' not found or not a directory.", file=sys.stderr)

    # Process Socials (if configured in navigation)
    if any(item.get('targetView') == 'socials-view' for item in main_navigation):
        print(f"  - Processing Socials data from config")
        socials_view_data.append({'text': socials_heading, 'type': 'heading'})
        socials_view_data.append({'text': ''})
        for link_config in socials_links_config:
            name = link_config.get('name', '')
            url = link_config.get('url', '#')
            display = link_config.get('display_text', url)
            safe_display = html.escape(display) # Use standard html escape
            safe_name = html.escape(name)
            link_html = f'<span class="link-name">{safe_name}:</span> <a href="{url}" target="_blank" rel="noopener noreferrer">{safe_display}</a>'
            socials_view_data.append({'text': link_html, 'type': 'list-item', 'isHtml': True})
        socials_view_data.append(create_info_line())

    # 3. Prepare Data for JavaScript Embedding
    print("[*] Preparing data for JavaScript embedding...")
    js_data = {
        # Data directly from config or processed lists
        "mainViewData": main_navigation,
        "blogsListData": blogs_list_data,
        "socialsViewData": socials_view_data, # Add processed socials data
        "themes": config_themes,
        "portfolioUsername": username,
        "defaultTheme": default_theme,
        # Dictionaries keyed by ID/targetView
        "blogContentData": blog_content_map,
        "contentViewData": content_view_data # Contains data for about, projects, etc.
    }

    # Convert Python data to JSON strings suitable for embedding
    js_data_json = {}
    try:
        for key, value in js_data.items():
            json_string = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
            sanitized_json = json_string.replace('</script>', '<\\/script>') # Basic sanitization
            js_data_json[key] = sanitized_json
    except Exception as e:
        print(f"ERROR: Failed to serialize data to JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # 4. Load/Define CSS and JS Logic (as strings)
    print("[*] Preparing CSS and JS logic strings...")

    # --- CSS String --- (Keep this block, paste CSS inside)
    # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    css_string = """
/* --- Theme Variables --- */
:root {
    --font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    /* Default: Dracula-like */
    --bg-primary: #282a36;
    --bg-secondary: #44475a;
    --bg-highlight: #44475a; /* Active line / Popup bg */
    --bg-popup: #3a3d4e; /* Slightly different for popup */
    --fg-primary: #f8f8f2;
    --fg-secondary: #6272a4; /* Line numbers, comments, date */
    --fg-highlight: #f8f8f2; /* Active line number */
    --fg-on-accent: #282a36; /* Text on Mode BG */
    --icon-fill: #282a36;    /* Fill for SVG icons on colored bg */
    --color-red: #ff5555;
    --color-green: #50fa7b;
    --color-yellow: #f1fa8c;
    --color-blue: #8abeb7; /* Mode bg, links */
    --color-purple: #bd93f9; /* Blog title, list bullet */
    --color-cyan: #8be9fd;
    --color-orange: #ffb86c; /* Socials Title */
    --color-pink: #ff79c6; /* Folder icon bg */
    --border-color: #6272a4;
}

/* Gruvbox Dark */
body.theme-gruvbox {
    --bg-primary: #282828; --bg-secondary: #3c3836; --bg-highlight: #504945;
    --bg-popup: #32302f; --fg-primary: #ebdbb2; --fg-secondary: #928374;
    --fg-highlight: #ebdbb2; --fg-on-accent: #282828; --icon-fill: #282828;
    --color-red: #cc241d; --color-green: #98971a; --color-yellow: #d79921;
    --color-blue: #458588; --color-purple: #b16286; --color-cyan: #689d6a;
    --color-orange: #d65d0e; --color-pink: #b16286; --border-color: #7c6f64;
}

/* Monokai */
body.theme-monokai {
    --bg-primary: #272822; --bg-secondary: #3E3D32; --bg-highlight: #49483E;
    --bg-popup: #30312a; --fg-primary: #F8F8F2; --fg-secondary: #75715E;
    --fg-highlight: #F8F8F2; --fg-on-accent: #272822; --icon-fill: #272822;
    --color-red: #F92672; --color-green: #A6E22E; --color-yellow: #E6DB74;
    --color-blue: #66D9EF; --color-purple: #AE81FF; --color-cyan: #66D9EF;
    --color-orange: #FD971F; --color-pink: #F92672; --border-color: #75715E;
}

/* Tokyo Night */
body.theme-tokyo-night {
    --bg-primary: #1a1b26; --bg-secondary: #414868; --bg-highlight: #292e42;
    --bg-popup: #24283b; --fg-primary: #c0caf5; --fg-secondary: #565f89;
    --fg-highlight: #c0caf5; --fg-on-accent: #1a1b26; --icon-fill: #1a1b26;
    --color-red: #f7768e; --color-green: #9ece6a; --color-yellow: #e0af68;
    --color-blue: #7aa2f7; --color-purple: #bb9af7; --color-cyan: #7dcfff;
    --color-orange: #ff9e64; --color-pink: #ff79c6; --border-color: #414868;
}

/* Catppuccin Macchiato */
body.theme-catppuccin {
    --bg-primary: #24273a; --bg-secondary: #363a4f; --bg-highlight: #494d64;
    --bg-popup: #363a4f; --fg-primary: #cad3f5; --fg-secondary: #747c9c;
    --fg-highlight: #cad3f5; --fg-on-accent: #24273a; --icon-fill: #24273a;
    --color-red: #ed8796; --color-green: #a6da95; --color-yellow: #eed49f;
    --color-blue: #8aadf4; --color-purple: #c6a0f6; --color-cyan: #91d7e3;
    --color-orange: #f5a97f; --color-pink: #f5bde6; --border-color: #5b6078;
}

/* Nightfox */
body.theme-nightfox {
    --bg-primary: #192330; --bg-secondary: #394b5f; --bg-highlight: #2a3c4e;
    --bg-popup: #233343; --fg-primary: #d4d4d4; --fg-secondary: #7c8f8f;
    --fg-highlight: #d4d4d4; --fg-on-accent: #192330; --icon-fill: #192330;
    --color-red: #e46a78; --color-green: #86cd81; --color-yellow: #dbc074;
    --color-blue: #71a6d0; --color-purple: #a78bfa; --color-cyan: #6cb6eb;
    --color-orange: #de9b70; --color-pink: #e588be; --border-color: #4a6074;
}

/* OneNord */
body.theme-onenord {
     --bg-primary: #2e3440; --bg-secondary: #3b4252; --bg-highlight: #434c5e;
     --bg-popup: #3b4252; --fg-primary: #d8dee9; --fg-secondary: #616e88;
     --fg-highlight: #eceff4; --fg-on-accent: #2e3440; --icon-fill: #2e3440;
     --color-red: #bf616a; --color-green: #a3be8c; --color-yellow: #ebcb8b;
     --color-blue: #81a1c1; --color-purple: #b48ead; --color-cyan: #88c0d0;
     --color-orange: #d08770; --color-pink: #b48ead; --border-color: #4c566a;
}

/* === Light Themes === */

/* One Light */
body.theme-one-light {
    --bg-primary: #fafafa; --bg-secondary: #eaeaeb; --bg-highlight: #e8f2ff;
    --bg-popup: #f0f0f0; --fg-primary: #383a42; --fg-secondary: #a0a1a7;
    --fg-highlight: #202328; --fg-on-accent: #fafafa; --icon-fill: #fafafa; /* White fill on colored bg */
    --color-red: #e45649; --color-green: #50a14f; --color-yellow: #c18401;
    --color-blue: #4078f2; --color-purple: #a626a4; --color-cyan: #0184bc;
    --color-orange: #986801; --color-pink: #e45649; --border-color: #d9d8d9;
}

/* Github Light */
 body.theme-github-light {
    --bg-primary: #ffffff; --bg-secondary: #f6f8fa; --bg-highlight: #cce5ff;
    --bg-popup: #f1f3f5; --fg-primary: #24292e; --fg-secondary: #6a737d;
    --fg-highlight: #1b1f23; --fg-on-accent: #ffffff; --icon-fill: #ffffff; /* White fill on colored bg */
    --color-red: #d73a49; --color-green: #22863a; --color-yellow: #b08800;
    --color-blue: #0366d6; --color-purple: #5a32a3; --color-cyan: #11637c;
    --color-orange: #f66a0a; --color-pink: #d73a49; --border-color: #e1e4e8;
}


/* --- Base Styles using Variables --- */
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { height: 100%; font-family: var(--font-family); overflow: hidden; }
body { background-color: var(--bg-primary); color: var(--fg-primary); transition: background-color 0.1s ease, color 0.1s ease; }

.neovim-editor { display: flex; flex-direction: column; height: 100vh; background-color: var(--bg-primary); color: var(--fg-primary); }
.editor-pane { flex-grow: 1; font-size: 1.1em; line-height: 1.5; overflow-y: auto; padding-top: 10px; padding-bottom: 10px; }
.view { display: none; height: 100%; }
.view.active { display: block; }

.editor-line { display: flex; align-items: flex-start; padding: 0 15px 0 0; min-height: calc(1.1em * 1.5); position: relative; }
.line-number { color: var(--fg-secondary); display: inline-block; user-select: none; text-align: right; min-width: 3.5em; padding-right: 15px; flex-shrink: 0; line-height: inherit; }
.line-text { flex-grow: 1; white-space: pre-wrap; word-break: break-word; line-height: inherit; }
.editor-line.line-active { background-color: var(--bg-highlight); }
.editor-line.line-active > .line-number { color: var(--fg-highlight); font-weight: bold; }
/* Ensure text color on active line provides contrast, especially for light themes */
.editor-line.line-active > .line-text { color: var(--fg-highlight); }

#main-view .editor-line, #blogs-list-view .editor-line { cursor: pointer; }
#main-view .editor-line .line-text a, #blogs-list-view .editor-line .line-text a { color: inherit; text-decoration: none; display: block; pointer-events: none; }

.content-view .is-heading .line-text { font-weight: bold; }
#about-view .is-heading .line-text,
#projects-view .is-heading .line-text { /* Apply to multiple content views */
    color: var(--color-green);
}
#socials-view .is-heading .line-text { color: var(--color-orange); }
#blog-content-view .is-blog-title .line-text { color: var(--color-purple); font-size: 1.2em; }
#blog-content-view .is-blog-date .line-text { color: var(--fg-secondary); font-size: 0.9em; }
.content-view .is-info .line-text { color: var(--fg-secondary); font-style: italic;} /* Style for info lines */

.content-view .is-list-item .line-text { padding-left: 2em; position: relative; }
.content-view .is-list-item .line-text::before { content: "-"; position: absolute; left: 0.8em; color: var(--color-purple); }
.content-view .line-text a { color: var(--color-blue); }
.content-view .line-text a:hover { text-decoration: underline; }
.content-view .link-name { color: var(--color-yellow); }

/* Status Bar and Icons adjust with theme */
.status-bar { display: flex; justify-content: space-between; align-items: center; background-color: var(--bg-secondary); color: var(--fg-primary); padding: 3px 10px; font-size: 0.9em; white-space: nowrap; height: 25px; line-height: 19px; flex-shrink: 0; }
.status-left, .status-right { display: flex; align-items: center; }
.mode { background-color: var(--color-blue); color: var(--fg-on-accent); font-weight: bold; padding: 1px 8px; margin-right: 10px; border-radius: 3px; letter-spacing: 0.5px; background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="var(--icon-fill)"><polygon points="15,15 15,85 40,85 40,65 60,65 60,85 85,85 85,15"/></svg>'); background-repeat: no-repeat; background-size: 1em 1em; background-position: 6px center; padding-left: 28px; }

.icon { display: inline-flex; align-items: center; justify-content: center; padding: 1px 4px; border-radius: 3px; margin: 0 4px; color: var(--fg-on-accent); }
.list-icon { color: var(--fg-primary); padding: 0; margin-right: 5px; font-size: 0.9em; background-color: transparent; }
.folder-icon { background-color: var(--color-pink); width: 1.1em; height: 1.1em; background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="var(--icon-fill)"><path d="M10 4H4c-1.11 0-2 .89-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8c0-1.11-.9-2-2-2h-8l-2-2z"/></svg>'); background-size: contain; background-repeat: no-repeat; background-position: center; font-size: 0.8em; }
.folder-icon span { display: none; }
.file-status-icon { background-color: var(--color-green); font-size: 0.9em; }
.filename, .username, .file-count { color: var(--fg-primary); }
.username { margin: 0 5px; }
.file-status-extra { color: var(--fg-secondary); margin-left: 8px; }
.cursor { display: none; }

/* Command Line */
#command-line {
    position: fixed; bottom: 0; left: 0; width: 100%;
    background-color: var(--bg-primary); color: var(--fg-primary);
    padding: 3px 10px; font-size: 0.9em; height: 25px; line-height: 19px;
    z-index: 100; display: none; white-space: nowrap; overflow: hidden;
}
#command-line-cursor {
    background-color: var(--fg-primary); color: var(--fg-primary);
    display: inline-block; width: 0.6em; height: 1.1em; vertical-align: text-bottom;
    margin-left: 1px; animation: blink 1s step-end infinite;
}
@keyframes blink { 50% { background-color: transparent; } }

/* Theme Popup */
#theme-popup {
    position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
    min-width: 280px; background-color: var(--bg-popup);
    border: 1px solid var(--border-color); box-shadow: 0 5px 20px rgba(0, 0, 0, 0.4);
    z-index: 101; max-height: 60vh; overflow-y: auto;
    display: none; color: var(--fg-primary); border-radius: 4px;
}
#theme-list .theme-item { padding: 6px 12px; cursor: pointer; white-space: nowrap; font-size: 0.95em; }
#theme-list .theme-item:not(.disabled):hover { background-color: rgba(128, 128, 128, 0.1); } /* Generic subtle hover, ignore disabled */
#theme-list .theme-item.active { background-color: var(--color-blue); color: var(--fg-on-accent); font-weight: bold; }
#theme-list .theme-item.disabled { opacity: 0.6; cursor: default; text-align: center; font-style: italic; padding-top: 8px; padding-bottom: 8px; background-color: transparent !important;} /* Style for disabled separator */

"""
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    # --- JavaScript Logic String --- (Keep this block, paste JS inside)
    # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    # PASTE THE CORE JS LOGIC HERE (State Vars, DOM Refs, Functions, Handlers)
    # Make sure it uses the new data structure with contentViewData
    js_logic_string = """
// --- State Variables ---
let currentViewId = 'main-view';
let previousViewId = null;
let isCommandMode = false;
let commandInput = "";
let isThemePopupActive = false;
let themePopupItems = [];
let currentThemePopupIndex = 0;
// Use the defaultTheme passed from Python
let appliedThemeClassName = defaultTheme || 'theme-dracula';

// Consolidate view state management
let viewStates = {}; // Will be populated in initialize

// --- DOM References ---
const editorPane = document.getElementById('editor-pane');
const views = document.querySelectorAll('.view'); // Get all view divs
const statusBar = document.querySelector('.status-bar');
const statusFilename = document.getElementById('status-filename');
const lineIndicator = document.getElementById('line-indicator');
const statusExtra = document.getElementById('status-extra');
const commandLine = document.getElementById('command-line');
const commandInputText = document.getElementById('command-input-text');
const themePopup = document.getElementById('theme-popup');
const themeListContainer = document.getElementById('theme-list');
const statusUsername = document.getElementById('status-username');

// --- Functions ---
function createEditorLine(lineNumber, text, isHtml = false) {
    const lineDiv = document.createElement('div');
    lineDiv.classList.add('editor-line');
    const numberSpan = document.createElement('span');
    numberSpan.classList.add('line-number');
    numberSpan.textContent = lineNumber;
    lineDiv.appendChild(numberSpan);
    const textSpan = document.createElement('span');
    textSpan.classList.add('line-text');
    if (isHtml) {
        textSpan.innerHTML = (text && String(text).trim()) ? text : ' ';
    } else {
        textSpan.textContent = text || ' ';
         if (String(text).trim() === '') { textSpan.innerHTML = ' '; }
    }
    lineDiv.appendChild(textSpan);
    return lineDiv;
}

// Populates a view using the corresponding data source
function populateView(viewId, data) {
    const viewElement = document.getElementById(viewId);
    if (!viewElement) { console.warn("Populate: View element not found:", viewId); return []; }
    viewElement.innerHTML = ''; // Clear previous content
    let lines = [];

    if (!Array.isArray(data)) {
        console.warn(`Populate: Data for view '${viewId}' is not an array.`);
        return []; // Expecting an array of line objects
    }

    data.forEach((itemData, index) => {
        const lineNumber = index + 1;
        let lineElement;
        // Determine text content based on view type
        const isListViewItem = (viewId === 'main-view' || viewId === 'blogs-list-view');
        const textContent = isListViewItem ? (itemData.text || itemData.title || '') : (itemData.text || '');

        // Create the basic line element
        lineElement = createEditorLine(lineNumber, textContent, itemData.isHtml || false);
        lineElement.dataset.index = index; // Store index on the element

        // Specific adjustments for list views (main menu, blog list)
        if (isListViewItem) {
             // Rebuild line content to wrap text in <a> for consistent styling & structure
             lineElement.innerHTML = ''; // Clear initial simple creation
             const numberSpan = createEditorLine(lineNumber, '').querySelector('.line-number');
             const textSpan = document.createElement('span');
             textSpan.classList.add('line-text');
             textSpan.innerHTML = `<a>${textContent || ' '}</a>`; // Wrap text in link
             lineElement.appendChild(numberSpan);
             lineElement.appendChild(textSpan);

             // Attach event listeners for list items
             lineElement.addEventListener('click', handleListClick);
             lineElement.addEventListener('mouseover', handleListMouseOver);

             // Add navigation data attributes
             if (viewId === 'main-view') {
                 lineElement.dataset.targetView = itemData.targetView;
                 lineElement.dataset.filename = itemData.filename;
             } else { // blogs-list-view
                 lineElement.dataset.blogId = itemData.id;
                 lineElement.dataset.targetView = 'blog-content-view';
             }
         } else { // Content Views (About, Socials, Blog Content, Projects etc.)
             // Add styling classes based on type property from Python data
             if(itemData.type) lineElement.classList.add(`is-${itemData.type.replace('_','-')}`);
             // Make links within content clickable
             const links = lineElement.querySelectorAll('a');
             links.forEach(link => {
                 link.addEventListener('click', (e) => { /* Allow default for now */ });
             });
         }
        viewElement.appendChild(lineElement);
        lines.push(lineElement);
    });
    return lines;
}

function updateStatusBar(filename, lineNum, totalLines, extra = '') {
    statusFilename.textContent = filename || '';
    if (totalLines > 0) {
         lineIndicator.textContent = `${lineNum}/${totalLines}`;
    } else {
         lineIndicator.textContent = '--';
    }
    statusExtra.textContent = extra || '';
}

function setActiveLine(viewId) {
     const state = viewStates[viewId];
     if (!state || !state.lines || state.lines.length === 0) return; // Exit if no state or lines

     // Ensure currentIndex is valid
     if (state.currentIndex < 0 || state.currentIndex >= state.lines.length) {
         state.currentIndex = 0; // Reset if out of bounds
     }

     state.lines.forEach((line, index) => {
         if (!line) return; // Skip if line element is somehow null
         if (index === state.currentIndex) {
             line.classList.add('line-active');
             if(typeof line.scrollIntoView === 'function') {
                 line.scrollIntoView({ block: 'nearest', inline: 'nearest' });
             }
         } else {
             line.classList.remove('line-active');
         }
     });
}

// More robust switchView using dynamic data lookup
function switchView(targetViewId, options = {}) {
    if (isCommandMode || isThemePopupActive) return;

    const targetViewElement = document.getElementById(targetViewId);
    if (!targetViewElement) {
        console.error("SwitchView: Target view element not found:", targetViewId);
        return; // Don't switch if view doesn't exist
    }

    // Ensure state object exists for the target view
    if (!viewStates[targetViewId]) {
        viewStates[targetViewId] = { lines: [], currentIndex: 0, data: [] };
    }
    const state = viewStates[targetViewId];

    previousViewId = currentViewId;
    currentViewId = targetViewId;

    views.forEach(view => view.classList.remove('active')); // Hide all

    let filename = options.filename;
    let extraStatus = options.extra || '';

    // Determine data source and populate if necessary
    let sourceData = null;
    if (targetViewId === 'main-view') {
        sourceData = mainViewData;
        filename = filename || 'index'; // Default filename for main view
    } else if (targetViewId === 'blogs-list-view') {
        sourceData = blogsListData;
        filename = filename || 'blogs.list';
    } else if (targetViewId === 'socials-view') {
        sourceData = socialsViewData; // Use specific socials data
        filename = filename || 'socials.md';
        extraStatus = '[+] R';
    } else if (targetViewId === 'blog-content-view') {
        const blogId = options.blogId;
        if (blogId && blogContentData[blogId]) {
            sourceData = blogContentData[blogId]; // Use specific blog content data
            state.blogId = blogId; // Store current blogId on state
            filename = filename || `${blogId}.md`;
            extraStatus = '[+] R';
        } else {
            console.error("SwitchView: Invalid blogId or blog data not found:", blogId);
            switchView(previousViewId || 'main-view'); // Go back
            return;
        }
    } else if (contentViewData[targetViewId]) { // Handle generic content pages
        sourceData = contentViewData[targetViewId];
        // Try to find filename from main navigation config item
        const navItem = mainViewData.find(item => item.targetView === targetViewId);
        filename = filename || navItem?.filename || targetViewId.replace('-view','.md');
        extraStatus = '[+] R';
    } else {
        console.warn("SwitchView: No data source identified for view:", targetViewId);
        sourceData = []; // Default to empty if no data found
    }

    // Populate view only if lines array is empty or data source changed
    if (state.lines.length === 0 || state.data !== sourceData) {
         state.data = sourceData || []; // Assign the determined data source
         state.lines = populateView(targetViewId, state.data);
    }

    targetViewElement.classList.add('active');
    editorPane.scrollTop = 0; // Scroll to top

    // Reset index, set active line, update status bar
    state.currentIndex = 0; // Always start at top of new view
    setActiveLine(targetViewId);
    updateStatusBar(filename, state.currentIndex + 1, state.lines.length, extraStatus);
}


function enterCommandMode() { if (isThemePopupActive) return; isCommandMode = true; commandInput = ""; commandInputText.textContent = ""; statusBar.style.display = 'none'; commandLine.style.display = 'block'; }
function exitCommandMode() { isCommandMode = false; commandInput = ""; commandLine.style.display = 'none'; statusBar.style.display = 'flex'; }
function processCommand() { const cmd = commandInput.trim(); if (cmd === 'themes') { openThemePopup(); } else if (cmd === 'q' || cmd === 'quit') { window.close(); } exitCommandMode(); }
function applyTheme(themeClassName) { if(themeClassName) document.body.className = themeClassName; }
function previewTheme(index) { if (index >= 0 && index < themes.length && !themes[index].disabled) { currentThemePopupIndex = index; applyTheme(themes[index].className); highlightThemeItem(index); } }
function highlightThemeItem(activeIndex) { themePopupItems.forEach((item, index) => { if (!item) return; if (!themes[index]?.disabled) { if (index === activeIndex) { item.classList.add('active'); item.scrollIntoView({ block: 'nearest', inline: 'nearest' }); } else { item.classList.remove('active'); } } else { item.classList.remove('active'); } }); }
function closeThemePopup(revertTheme = false) { isThemePopupActive = false; themePopup.style.display = 'none'; if (revertTheme) { applyTheme(appliedThemeClassName); } }
function confirmThemeSelection() { if (!isThemePopupActive || themes[currentThemePopupIndex]?.disabled) return; appliedThemeClassName = themes[currentThemePopupIndex].className; closeThemePopup(false); }

function populateThemeList() {
    themeListContainer.innerHTML = ''; themePopupItems = [];
    themes.forEach((theme, index) => {
        const item = document.createElement('div'); item.classList.add('theme-item'); item.textContent = theme.name; item.dataset.index = index;
        if (theme.disabled) {
            item.style.opacity = "0.6"; item.style.cursor = "default"; item.style.textAlign = "center"; item.style.fontStyle = "italic"; item.style.paddingTop = "8px"; item.style.paddingBottom = "8px"; item.classList.add('disabled');
        } else {
            item.addEventListener('click', () => { previewTheme(index); confirmThemeSelection(); });
            item.addEventListener('mouseover', () => { previewTheme(index); });
        }
        themeListContainer.appendChild(item); themePopupItems.push(item);
    });
     themeListContainer.addEventListener('mouseleave', () => { if (isThemePopupActive) { applyTheme(appliedThemeClassName); highlightThemeItem(themes.findIndex(t => t.className === appliedThemeClassName && !t.disabled)); } });
}

function openThemePopup() {
    if(isCommandMode) exitCommandMode(); populateThemeList();
    const currentAppliedIndex = themes.findIndex(t => t.className === appliedThemeClassName && !t.disabled);
    let initialValidIndex = 0;
    for(let i = 0; i < themes.length; i++) { if (!themes[i].disabled) { initialValidIndex = i; break; } }
    currentThemePopupIndex = (currentAppliedIndex >= 0 && !themes[currentAppliedIndex]?.disabled) ? currentAppliedIndex : initialValidIndex;
    highlightThemeItem(currentThemePopupIndex); applyTheme(themes[currentThemePopupIndex].className);
    isThemePopupActive = true; themePopup.style.display = 'block';
}

// --- Event Handlers ---
function handleListClick(event) { const lineElement = event.target.closest('.editor-line'); if (!lineElement || isCommandMode || isThemePopupActive) return; const state = viewStates[currentViewId]; if (!state) return; const index = parseInt(lineElement.dataset.index, 10); if (!isNaN(index)) { state.currentIndex = index; const targetView = lineElement.dataset.targetView; const blogId = lineElement.dataset.blogId; if (targetView) { switchView(targetView, { blogId: blogId }); } } }
function handleListMouseOver(event) { const lineElement = event.target.closest('.editor-line'); if (!lineElement || isCommandMode || isThemePopupActive) return; const state = viewStates[currentViewId]; if (!state) return; const index = parseInt(lineElement.dataset.index, 10); if (!isNaN(index)) { state.currentIndex = index; setActiveLine(currentViewId); } }
function goBack() { let targetView = 'main-view'; if (currentViewId === 'blog-content-view') { targetView = 'blogs-list-view'; } else if (currentViewId !== 'main-view') { targetView = 'main-view'; } if(currentViewId !== 'main-view') { switchView(targetView); } }

function handleKeyDown(event) {
    let processed = false;
    if (isThemePopupActive) { /* Theme Popup Keys */ let newIndex = currentThemePopupIndex; let direction = 0; switch (event.key) { case 'j': case 'ArrowDown': direction = 1; processed = true; break; case 'k': case 'ArrowUp': direction = -1; processed = true; break; case 'Enter': confirmThemeSelection(); processed = true; break; case 'Escape': closeThemePopup(true); processed = true; break; } if (direction !== 0) { let potentialIndex = currentThemePopupIndex + direction; while(potentialIndex >= 0 && potentialIndex < themes.length) { if (!themes[potentialIndex]?.disabled) { newIndex = potentialIndex; break; } potentialIndex += direction; } if (newIndex !== currentThemePopupIndex && !themes[newIndex]?.disabled) { previewTheme(newIndex); } }
    } else if (isCommandMode) { /* Command Mode Keys */ switch (event.key) { case 'Enter': processCommand(); processed = true; break; case 'Escape': exitCommandMode(); processed = true; break; case 'Backspace': commandInput = commandInput.slice(0, -1); commandInputText.textContent = commandInput; processed = true; break; default: if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) { commandInput += event.key; commandInputText.textContent = commandInput; processed = true; } break; }
    } else { /* Normal View Keys */ const state = viewStates[currentViewId]; if (!state) { return; } let newIndex = state.currentIndex; switch (event.key) { case ':': enterCommandMode(); processed = true; break; case 'j': case 'ArrowDown': if (state.lines.length > 0) { newIndex = Math.min(state.lines.length - 1, state.currentIndex + 1); } processed = true; break; case 'k': case 'ArrowUp': if (state.lines.length > 0) { newIndex = Math.max(0, state.currentIndex - 1); } processed = true; break; case 'Enter': if ((currentViewId === 'main-view' || currentViewId === 'blogs-list-view') && state.lines.length > 0) { const activeLine = state.lines[state.currentIndex]; if (activeLine) { const targetView = activeLine.dataset.targetView; const blogId = activeLine.dataset.blogId; if(targetView) switchView(targetView, { blogId: blogId }); } } processed = true; break; case 'Escape': goBack(); processed = true; break; case 'h': case 'ArrowLeft': case 'l': case 'ArrowRight': processed = true; break; } if (processed && newIndex !== state.currentIndex && state.lines.length > 0) { state.currentIndex = newIndex; setActiveLine(currentViewId); const filename = document.getElementById('status-filename').textContent; const extra = document.getElementById('status-extra').textContent; updateStatusBar(filename, state.currentIndex + 1, state.lines.length, extra); } }
    if (processed) { event.preventDefault(); }
}

// --- Initialization Function ---
function initialize() {
     // Initialize view state objects dynamically from known views
     views.forEach(viewDiv => {
         if (viewDiv.id && !viewStates[viewDiv.id]) {
            viewStates[viewDiv.id] = { lines: [], currentIndex: 0, data: [] };
         }
     });

     // Assign data sources to initial states where known
     if(mainViewData) viewStates['main-view'].data = mainViewData;
     // contentViewData holds data for 'about', 'projects', etc.
     // socialsViewData holds data for 'socials'
     // blogsListData holds data for 'blogs-list'
     // blogContentData holds data for 'blog-content' (loaded dynamically)

     if(statusUsername) statusUsername.textContent = portfolioUsername;
     appliedThemeClassName = defaultTheme || 'theme-dracula';
     applyTheme(appliedThemeClassName);

     // Populate and switch to initial view
     switchView('main-view'); // switchView now handles populating if needed

     document.addEventListener('keydown', handleKeyDown);
 }
"""
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    # 5. Assemble Final HTML
    print("[*] Assembling final HTML output...")

    # Dynamically create view divs based on main_navigation config
    view_divs_html = ""
    # Ensure main view always exists
    all_view_ids = set(['main-view'])
    for item in main_navigation:
        target_view = item.get('targetView')
        if target_view:
             all_view_ids.add(target_view)
    # Add special views not necessarily in main nav explicitly
    all_view_ids.add('blog-content-view')

    for view_id in sorted(list(all_view_ids)): # Sort for consistent order
        # Determine if it's a content view for styling purposes
        view_class = "view content-view" if view_id not in ['main-view', 'blogs-list-view'] else "view"
        # Mark initial active view
        active_class = " active" if view_id == 'main-view' else ""
        view_divs_html += f'            <div id="{view_id}" class="{view_class}{active_class}"></div>\n'


    final_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(site_title)}</title>
    <style>
{css_string}
    </style>
</head>
<body class="{html.escape(default_theme)}">
    <div class="neovim-editor">
        <div class="editor-pane" id="editor-pane">
{view_divs_html}        </div>
        <div class="status-bar">
             <div class="status-left"> <span class="mode"> NORMAL </span> <span class="icon list-icon">☰</span> <span class="filename" id="status-filename">index</span> </div>
             <div class="status-right"> <span class="icon folder-icon"><span>📁</span></span> <span class="username" id="status-username">{html.escape(username)}</span> <span class="icon file-status-icon">☰</span> <span class="file-count" id="line-indicator">1/?</span> <span class="file-status-extra" id="status-extra"></span> </div>
        </div>
        <div id="command-line"> <span id="command-prompt">:</span><span id="command-input-text"></span><span id="command-line-cursor"></span> </div>
        <div id="theme-popup"> <div id="theme-list"></div> </div>
    </div>

    <script>
        // --- Embedded Data (Generated from Python) ---
        const mainViewData = {js_data_json['mainViewData']};
        const blogsListData = {js_data_json['blogsListData']};
        const blogContentData = {js_data_json['blogContentData']};
        const contentViewData = {js_data_json['contentViewData']}; // Holds about, projects, etc.
        const socialsViewData = {js_data_json['socialsViewData']}; // Specific data for socials view
        const themes = {js_data_json['themes']};
        const portfolioUsername = {js_data_json['portfolioUsername']};
        const defaultTheme = {js_data_json['defaultTheme']};

        // --- Core JS Logic (Pasted from Python Variable) ---
{js_logic_string}

        // --- Initializer ---
        try {{
            document.addEventListener('DOMContentLoaded', initialize);
        }} catch (e) {{
            console.error("Error during initial script execution:", e);
            document.body.innerHTML = '<p style="color: red; padding: 20px;">Error initializing application. Please check the console.</p>';
        }}
    </script>
</body>
</html>"""

    # 6. Write Output File
    print(f"[*] Writing output to '{OUTPUT_FILE}'...")
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(final_html)
        print("[+] Build successful!")
        print(f"    Output file: {OUTPUT_FILE.resolve()}")
    except Exception as e:
        print(f"ERROR: Failed to write output file: {e}", file=sys.stderr)
        sys.exit(1)

# --- Run Build ---
if __name__ == "__main__":
    build_site()
