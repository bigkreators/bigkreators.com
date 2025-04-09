# Kryptopedia Frontend

Cryptopedia uses a template-based frontend system that integrates directly with the FastAPI backend. This document describes the frontend architecture and how to work with it.

## Frontend Architecture

The frontend uses a combination of:

1. **Jinja2 Templates**: Server-side HTML templates rendered by FastAPI
2. **Static CSS**: For styling the application
3. **Vanilla JavaScript**: For handling client-side interactions
4. **API Integration**: Direct calls to the backend API

## Template Structure

Templates are stored in the `templates` directory and include:

- `index.html`: The homepage
- `article.html`: Individual article view
- `articles_list.html`: List of articles
- `search_results.html`: Search results
- `create_article.html`: Article creation form
- `404.html`: Error page

## Static Assets

Static files are stored in the `static` directory:

- `style.css`: Main stylesheet
- `script.js`: Main JavaScript file

## Frontend Features

### Authentication

- Login/register modal dialogs
- JWT-based authentication with token storage in localStorage
- Conditional display based on login status

### Articles

- View articles with support for rich HTML content
- Create and edit articles with WYSIWYG editor
- Support for categories and tags
- Article metadata display

### Search

- Integrated search with API backend
- Support for both simple and advanced search

### Media

- Support for image uploads and display
- Media embedding in articles

## Working with Templates

The templates use Jinja2's template language. Key features used include:

- Template inheritance
- Conditional blocks
- Loops
- Variable interpolation
- Custom filters (like datetime formatting)

Example of template variables:

```html
<h1>{{ article.title }}</h1>
<p>Last updated: {{ article.lastUpdatedAt|strftime('%Y-%m-%d') }}</p>
```

## Adding New Pages

To add a new page:

1. Create a new template in the `templates` directory
2. Add a route in `main.py` that renders the template
3. Add any necessary links in the navigation

## JavaScript Functionality

The frontend JavaScript handles:

- Modal dialogs
- Form submissions
- API integration
- User interface interactions

Most API calls use the Fetch API and handle token-based authentication.

## Customizing the Frontend

You can customize the frontend by:

- Modifying the CSS in `static/style.css`
- Adding new templates in the `templates` directory
- Extending the JavaScript functionality in `static/script.js`
- Adding new static assets in the `static` directory

## Media Storage

Media files are served based on the configured storage backend:

- When using local storage, files are served directly from the `/media` directory
- When using S3 storage, files are served from the S3 bucket URL

## Mobile Responsiveness

The frontend includes responsive styles to work well on mobile devices. Key breakpoints:

- Below 768px: Mobile layout
- Above 768px: Desktop layout
