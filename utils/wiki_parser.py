"""
Wiki markup parser for Kryptopedia.
"""
import re
from typing import Tuple, Optional, Dict, Any, List

def parse_wiki_markup(markup: str) -> Tuple[str, Optional[str]]:
    """
    Parse wiki markup into HTML.
    
    Args:
        markup: The wiki markup to parse
        
    Returns:
        Tuple[str, Optional[str]]: The parsed HTML and extracted short description (if any)
    """
    # Extract short description if present
    short_description = None
    short_desc_match = re.search(r'\{\{Short description\|(.*?)\}\}', markup)
    if short_desc_match:
        short_description = short_desc_match.group(1).strip()
        markup = markup.replace(short_desc_match.group(0), '')
    
    # Handle text formatting
    markup = re.sub(r"'''(.*?)'''", r'<strong>\1</strong>', markup)  # Bold
    markup = re.sub(r"''(.*?)''", r'<em>\1</em>', markup)  # Italic
    markup = re.sub(r'<u>(.*?)</u>', r'<u>\1</u>', markup)  # Underline (already HTML)
    markup = re.sub(r'<s>(.*?)</s>', r'<s>\1</s>', markup)  # Strikethrough (already HTML)
    markup = re.sub(r'<sup>(.*?)</sup>', r'<sup>\1</sup>', markup)  # Superscript (already HTML)
    markup = re.sub(r'<sub>(.*?)</sub>', r'<sub>\1</sub>', markup)  # Subscript (already HTML)
    
    # Handle headings
    markup = re.sub(r'======\s*(.*?)\s*======', r'<h6 class="wiki-heading-6">\1</h6>', markup)
    markup = re.sub(r'=====\s*(.*?)\s*=====', r'<h5 class="wiki-heading-5">\1</h5>', markup)
    markup = re.sub(r'====\s*(.*?)\s*====', r'<h4 class="wiki-heading-4">\1</h4>', markup)
    markup = re.sub(r'===\s*(.*?)\s*===', r'<h3 class="wiki-heading-3">\1</h3>', markup)
    markup = re.sub(r'==\s*(.*?)\s*==', r'<h2 class="wiki-heading-2">\1</h2>', markup)
    markup = re.sub(r'=\s*(.*?)\s*=', r'<h1 class="wiki-heading-1">\1</h1>', markup)
    
    # Handle links
    # Internal links [[Page name]]
    markup = re.sub(r'\[\[(.*?)\]\]', lambda m: f'<a href="/articles/{m.group(1).replace(" ", "_")}">{m.group(1)}</a>', markup)
    # Internal links with display text [[Page name|Display text]]
    markup = re.sub(r'\[\[(.*?)\|(.*?)\]\]', r'<a href="/articles/\1">\2</a>', markup)
    # External links [http://example.com Display text]
    markup = re.sub(r'\[(https?://[^\s\]]+)\s+(.*?)\]', r'<a href="\1" target="_blank" rel="noopener">\2</a>', markup)
    # External links without display text [http://example.com]
    markup = re.sub(r'\[(https?://[^\s\]]+)\]', r'<a href="\1" target="_blank" rel="noopener">\1</a>', markup)
    
    # Handle lists
    lines = markup.split('\n')
    in_list = False
    list_type = None
    list_level = 0
    result_lines = []
    
    for line in lines:
        # Unordered list
        if line.startswith('* '):
            if not in_list or list_type != 'ul':
                if in_list:
                    result_lines.append(f'</{list_type}>')
                result_lines.append('<ul>')
                in_list = True
                list_type = 'ul'
            result_lines.append(f'<li>{line[2:]}</li>')
        # Ordered list
        elif line.startswith('# '):
            if not in_list or list_type != 'ol':
                if in_list:
                    result_lines.append(f'</{list_type}>')
                result_lines.append('<ol>')
                in_list = True
                list_type = 'ol'
            result_lines.append(f'<li>{line[2:]}</li>')
        # Not a list item
        else:
            if in_list:
                result_lines.append(f'</{list_type}>')
                in_list = False
                list_type = None
            result_lines.append(line)
    
    # Close any open list
    if in_list:
        result_lines.append(f'</{list_type}>')
    
    markup = '\n'.join(result_lines)
    
    # Handle templates
    # Simple templates like {{TemplateName|param1=value1|param2=value2}}
    markup = re.sub(r'\{\{([^|{}]+)(\|(.*?))?\}\}', process_template, markup)
    
    # Handle tables
    markup = re.sub(r'\{\|(.*?)\|\}', process_table, markup, flags=re.DOTALL)
    
    # Handle images
    # [[File:filename.jpg|options|caption]]
    markup = re.sub(r'\[\[File:(.*?)(\|(.*?))?\]\]', process_image, markup)
    
    # Handle references
    references = []
    
    def ref_replacer(match):
        ref_content = match.group(1)
        ref_name = None
        
        # Check if this is a named reference
        name_match = re.search(r'name="([^"]+)"', match.group(0))
        if name_match:
            ref_name = name_match.group(1)
        
        # Generate reference number
        ref_num = len(references) + 1
        references.append(f'<li id="ref-{ref_num}">{ref_content}</li>')
        
        return f'<sup class="wiki-reference">[{ref_num}]</sup>'
    
    markup = re.sub(r'<ref(?:\s+name="[^"]+")?>(.*?)</ref>', ref_replacer, markup, flags=re.DOTALL)
    
    # Handle reference list
    if '<references />' in markup:
        ref_list = '<div class="wiki-references"><h2>References</h2><ol>'
        ref_list += ''.join(references)
        ref_list += '</ol></div>'
        markup = markup.replace('<references />', ref_list)
    
    # Handle paragraphs
    paragraphs = markup.split('\n\n')
    for i, para in enumerate(paragraphs):
        if not (para.startswith('<') and para.endswith('>')):
            if para.strip():
                paragraphs[i] = f'<p>{para}</p>'
    
    markup = '\n'.join(paragraphs)
    
    return markup, short_description

def process_template(match) -> str:
    """Process a template match and return HTML."""
    template_name = match.group(1).strip()
    params_str = match.group(3) if match.group(2) else ""
    
    # Parse parameters
    params = {}
    if params_str:
        param_pairs = params_str.split('|')
        for pair in param_pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                params[key.strip()] = value.strip()
            elif pair.strip():
                # Positional parameter
                pos = len(params)
                params[str(pos + 1)] = pair.strip()
    
    # Handle special templates
    if template_name.lower() == 'infobox':
        return process_infobox_template(params)
    elif template_name.lower() == 'quote':
        return process_quote_template(params)
    elif template_name.lower() == 'cite':
        return process_citation_template(params)
    elif template_name.lower() == 'reflist':
        return '<references />'
    else:
        # Generic template display
        params_html = ''.join([f'<div><strong>{k}:</strong> {v}</div>' for k, v in params.items()])
        return f'<div class="wiki-template"><strong>{template_name}</strong>{params_html}</div>'

def process_infobox_template(params: Dict[str, str]) -> str:
    """Process an infobox template and return HTML."""
    html = '<table class="wiki-infobox">'
    
    # Title row
    if 'title' in params:
        html += f'<tr><th colspan="2" class="wiki-infobox-title">{params["title"]}</th></tr>'
    
    # Image row
    if 'image' in params:
        caption = params.get('caption', '')
        html += '<tr><td colspan="2" class="wiki-infobox-image">'
        html += f'<img src="/media/{params["image"]}" alt="{caption}">'
        if caption:
            html += f'<div>{caption}</div>'
        html += '</td></tr>'
    
    # Data rows
    i = 1
    while f'label{i}' in params:
        label = params[f'label{i}']
        data = params.get(f'data{i}', '')
        html += f'<tr><th class="wiki-infobox-label">{label}</th><td class="wiki-infobox-data">{data}</td></tr>'
        i += 1
    
    html += '</table>'
    return html

def process_quote_template(params: Dict[str, str]) -> str:
    """Process a quote template and return HTML."""
    text = params.get('text', '')
    author = params.get('author', '')
    source = params.get('source', '')
    year = params.get('year', '')
    
    html = '<blockquote class="wiki-quote">'
    html += f'<p>{text}</p>'
    
    if author or source or year:
        html += '<footer>'
        if author:
            html += f'<cite>{author}</cite>'
        if source:
            html += f', {source}'
        if year:
            html += f' ({year})'
        html += '</footer>'
    
    html += '</blockquote>'
    return html

def process_citation_template(params: Dict[str, str]) -> str:
    """Process a citation template and return HTML."""
    citation_type = params.get('1', 'web')  # Default to web
    
    if citation_type == 'web':
        title = params.get('title', '')
        url = params.get('url', '')
        author = params.get('author', '')
        website = params.get('website', '')
        date = params.get('date', '')
        access_date = params.get('access-date', '')
        
        html = '<span class="wiki-citation">'
        if author:
            html += f'{author}. '
        if title:
            if url:
                html += f'"<a href="{url}" target="_blank" rel="noopener">{title}</a>". '
            else:
                html += f'"{title}". '
        if website:
            html += f'<em>{website}</em>. '
        if date:
            html += f'{date}. '
        if access_date:
            html += f'Retrieved {access_date}.'
        html += '</span>'
        return html
    
    # Other citation types can be added as needed
    return f'<span class="wiki-citation">[Citation: {str(params)}]</span>'

def process_table(match) -> str:
    """Process a table match and return HTML."""
    table_content = match.group(1)
    
    # Parse table attributes
    table_attrs = {}
    first_line = table_content.strip().split('\n')[0]
    
    # Extract class attribute if present
    class_match = re.search(r'class="([^"]+)"', first_line)
    if class_match:
        table_attrs['class'] = class_match.group(1)
    
    # Start building HTML table
    html = '<table class="wiki-table'
    if 'class' in table_attrs:
        html += ' ' + table_attrs['class']
    html += '">'
    
    # Process caption if present
    caption_match = re.search(r'\|\+(.*?)(?:\|-|$)', table_content, re.DOTALL)
    if caption_match:
        caption = caption_match.group(1).strip()
        html += f'<caption>{caption}</caption>'
    
    # Process rows
    rows = re.split(r'\|-', table_content)
    
    # Skip the first row if it contains table attributes
    start_index = 1 if rows[0].strip() == first_line.strip() else 0
    
    for row in rows[start_index:]:
        if not row.strip():
            continue
            
        html += '<tr>'
        
        # Process header cells (!), then regular cells (|)
        header_cells = re.findall(r'!(.*?)(?:\!|$)', row)
        for cell in header_cells:
            if not cell.strip():
                continue
            html += f'<th>{cell.strip()}</th>'
        
        data_cells = re.findall(r'\|(.*?)(?:\||$)', row)
        for cell in data_cells:
            if not cell.strip():
                continue
            html += f'<td>{cell.strip()}</td>'
            
        html += '</tr>'
    
    html += '</table>'
    return html

def process_image(match) -> str:
    """Process an image match and return HTML."""
    filename = match.group(1).strip()
    options_str = match.group(3) if match.group(2) else ""
    
    # Parse options
    options = options_str.split('|') if options_str else []
    
    # Set defaults
    image_class = "wiki-image"
    caption = ""
    
    # Process options
    for opt in options:
        opt = opt.strip()
        if opt in ["thumb", "thumbnail"]:
            image_class += " thumb"
        elif opt == "center":
            image_class += " center"
        elif opt == "right":
            image_class += " right"
        elif opt == "left":
            image_class += " left"
        elif opt.startswith("width="):
            width = opt.split('=')[1]
            image_class += f" width-{width}"
        else:
            # Assume it's a caption
            caption = opt
    
    # Generate HTML
    html = f'<div class="{image_class}">'
    html += f'<img src="/media/{filename}" alt="{caption}">'
    if caption:
        html += f'<div class="wiki-image-caption">{caption}</div>'
    html += '</div>'
    
    return html
