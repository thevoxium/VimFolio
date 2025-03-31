
## 🚀 Getting Started

### Prerequisites

*   **Python:** Version 3.7 or higher recommended.
*   **Pip:** Python package installer (usually comes with Python).

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/thevoxium/VimFolio.git # Replace with your repo URL
    cd vimfolio
    ```

2.  **(Optional but Recommended) Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Usage

1.  **Configure:**
    *   Edit `config.yaml` to set your site title, username, default theme, navigation items, and social links. **Make sure to replace placeholder URLs/usernames!**
    *   Add/edit content in the `content/` directory:
        *   Modify `content/about.md`.
        *   Add other `.md` pages (like `projects.md`) if you configured them in `main_navigation`.
        *   Add your blog posts as `.md` files inside `content/blogs/`. Use YAML front matter for `title` and `date`.

2.  **Build:**
    *   Run the build script from the project root directory:
        ```bash
        python build.py
        ```
    *   This will process your configuration and content, generating the final `index.html` file inside the `public/` directory.

3.  **Deploy:**
    *   Upload the generated `public/index.html` file to your static hosting provider (GitHub Pages, Netlify, Vercel, Cloudflare Pages, etc.).

## ⚙️ Configuration (`config.yaml`)

This file controls the overall structure and metadata of your site.

*   `site_title`: Sets the `<title>` tag of the HTML page.
*   `username`: Displayed in the status bar.
*   `default_theme`: The `className` of the theme loaded initially.
*   `themes`: A list of available themes for the `:themes` popup. Each theme needs a `name` (display text) and `className` (CSS class). Use `disabled: true` for non-selectable separators.
*   `main_navigation`: Defines the items in the primary menu list.
    *   `text`: Display text in the menu.
    *   `targetView`: The HTML `id` of the view `div` to activate (e.g., `about-view`). The build script automatically creates containers for views defined here unless they are special (like `blogs-list-view`).
    *   `filename`: Text displayed in the status bar for this section. If it ends in `.md` and isn't a special view, the script looks for a matching file in `content/`.
*   `socials_heading`: Title for the socials section.
*   `socials_links`: List of your social media/other links.
    *   `name`: Label (e.g., "GitHub").
    *   `url`: The actual link URL.
    *   `display_text` (Optional): Custom text shown for the link; defaults to the URL.

## ✍️ Content Management (`content/`)

*   **Standard Pages (e.g., `about.md`, `projects.md`):**
    *   Create a Markdown file (e.g., `mypage.md`) in the `content/` directory.
    *   Add a corresponding entry in the `main_navigation` section of `config.yaml` with a unique `targetView` (e.g., `mypage-view`) and the matching `filename` (`mypage.md`).
    *   The build script will automatically process this Markdown file and make it accessible via the main menu.
*   **Blog Posts (`content/blogs/`):**
    *   Create individual `.md` files within the `content/blogs/` directory.
    *   Use **YAML Front Matter** at the top of each file to specify at least `title` and `date` (YYYY-MM-DD format recommended).
        ```yaml
        ---
        title: My Awesome Blog Post
        date: 2023-11-15
        ---

        Your blog content starts here...
        ```
    *   The filename (without `.md`) is used as the unique ID for the blog post.
    *   Posts are automatically listed in the "Blogs" view (if configured in `main_navigation`) and sorted by filename (descending by default, assuming newer posts have later filenames/dates).

##🎨 Customization

*   **Adding Themes:**
    1.  Define the CSS variables for your new theme in `build.py` within the `css_string` variable, following the pattern of existing themes (e.g., create a `body.theme-my-new-theme { ... }` block).
    2.  Add an entry for your theme to the `themes` list in `config.yaml`.
    3.  Re-run `python build.py`.
*   **CSS/JS:** You can modify the base styles or JavaScript logic directly within the `css_string` and `js_logic_string` variables in `build.py`. *Note: This requires understanding the existing code structure.*

##🤝 Contributing

Contributions are welcome! If you find bugs, have suggestions, or want to add features, feel free to open an issue or submit a pull request.

##📜 License

This project is licensed under the **MIT License**. 
