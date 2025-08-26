# File: KryptoMarkup_Tag_Comparison.md

# KryptoMarkup Tag-by-Tag Comparison Guide

## Complete Syntax Reference: KryptoMarkup vs HTML vs Wiki Markup vs Markdown

---

## 📝 Text Formatting Tags

### **Bold Text**
| Language | Syntax | Example Output |
|----------|--------|----------------|
| **KryptoMarkup** | `{bold}text{/bold}` or `{b}text{/b}` | **text** |
| **HTML** | `<strong>text</strong>` or `<b>text</b>` | **text** |
| **Wiki Markup** | `'''text'''` | **text** |
| **Markdown** | `**text**` or `__text__` | **text** |

### **Italic Text**
| Language | Syntax | Example Output |
|----------|--------|----------------|
| **KryptoMarkup** | `{italic}text{/italic}` or `{i}text{/i}` | *text* |
| **HTML** | `<em>text</em>` or `<i>text</i>` | *text* |
| **Wiki Markup** | `''text''` | *text* |
| **Markdown** | `*text*` or `_text_` | *text* |

### **Underline Text**
| Language | Syntax | Example Output |
|----------|--------|----------------|
| **KryptoMarkup** | `{underline}text{/underline}` or `{u}text{/u}` | <u>text</u> |
| **HTML** | `<u>text</u>` | <u>text</u> |
| **Wiki Markup** | `<u>text</u>` (HTML fallback) | <u>text</u> |
| **Markdown** | Not supported (use HTML) | N/A |

### **Strikethrough Text**
| Language | Syntax | Example Output |
|----------|--------|----------------|
| **KryptoMarkup** | `{strike}text{/strike}` or `{s}text{/s}` | ~~text~~ |
| **HTML** | `<s>text</s>` or `<del>text</del>` | ~~text~~ |
| **Wiki Markup** | `<s>text</s>` | ~~text~~ |
| **Markdown** | `~~text~~` | ~~text~~ |

### **Code (Inline)**
| Language | Syntax | Example Output |
|----------|--------|----------------|
| **KryptoMarkup** | `{code}text{/code}` | `text` |
| **HTML** | `<code>text</code>` | `text` |
| **Wiki Markup** | `<code>text</code>` | `text` |
| **Markdown** | `` `text` `` | `text` |

---

## 🎯 Heading Tags

### **Heading Levels**
| Language | H1 | H2 | H3 | H4 | H5 | H6 |
|----------|----|----|----|----|----|----|
| **KryptoMarkup** | `{h1}Title{/h1}` | `{h2}Title{/h2}` | `{h3}Title{/h3}` | `{h4}Title{/h4}` | `{h5}Title{/h5}` | `{h6}Title{/h6}` |
| **HTML** | `<h1>Title</h1>` | `<h2>Title</h2>` | `<h3>Title</h3>` | `<h4>Title</h4>` | `<h5>Title</h5>` | `<h6>Title</h6>` |
| **Wiki Markup** | `= Title =` | `== Title ==` | `=== Title ===` | `==== Title ====` | `===== Title =====` | `====== Title ======` |
| **Markdown** | `# Title` | `## Title` | `### Title` | `#### Title` | `##### Title` | `###### Title` |

---

## 📋 List Tags

### **Unordered Lists**
| Language | Syntax | Nested Syntax |
|----------|--------|---------------|
| **KryptoMarkup** | `{ul}`<br>`{li}Item 1{/li}`<br>`{li}Item 2{/li}`<br>`{/ul}` | `{ul}`<br>`{li}Item`<br>`{ul}`<br>`{li}Nested{/li}`<br>`{/ul}`<br>`{/li}`<br>`{/ul}` |
| **HTML** | `<ul>`<br>`<li>Item 1</li>`<br>`<li>Item 2</li>`<br>`</ul>` | `<ul>`<br>`<li>Item`<br>`<ul>`<br>`<li>Nested</li>`<br>`</ul>`<br>`</li>`<br>`</ul>` |
| **Wiki Markup** | `* Item 1`<br>`* Item 2` | `* Item`<br>`** Nested` |
| **Markdown** | `- Item 1`<br>`- Item 2`<br>or<br>`* Item 1`<br>`* Item 2` | `- Item`<br>`  - Nested` |

### **Ordered Lists**
| Language | Syntax | Nested Syntax |
|----------|--------|---------------|
| **KryptoMarkup** | `{ol}`<br>`{li}First{/li}`<br>`{li}Second{/li}`<br>`{/ol}` | `{ol}`<br>`{li}First`<br>`{ol}`<br>`{li}Nested{/li}`<br>`{/ol}`<br>`{/li}`<br>`{/ol}` |
| **HTML** | `<ol>`<br>`<li>First</li>`<br>`<li>Second</li>`<br>`</ol>` | `<ol>`<br>`<li>First`<br>`<ol>`<br>`<li>Nested</li>`<br>`</ol>`<br>`</li>`<br>`</ol>` |
| **Wiki Markup** | `# First`<br>`# Second` | `# First`<br>`## Nested` |
| **Markdown** | `1. First`<br>`2. Second` | `1. First`<br>`   1. Nested` |

---

## 🔗 Links & References

### **Basic Links**
| Language | Syntax | Example |
|----------|--------|---------|
| **KryptoMarkup** | `{link url="https://example.com"}Text{/link}` | `{link url="https://google.com"}Google{/link}` |
| **HTML** | `<a href="https://example.com">Text</a>` | `<a href="https://google.com">Google</a>` |
| **Wiki Markup** | `[https://example.com Text]` | `[https://google.com Google]` |
| **Markdown** | `[Text](https://example.com)` | `[Google](https://google.com)` |

### **Internal/Anchor Links**
| Language | Syntax | Example |
|----------|--------|---------|
| **KryptoMarkup** | `{anchor id="section"}Text{/anchor}` | `{link href="#section"}Go to Section{/link}` |
| **HTML** | `<a id="section">Text</a>` | `<a href="#section">Go to Section</a>` |
| **Wiki Markup** | `[[#section|Text]]` | `[[PageName#section]]` |
| **Markdown** | `[Text](#section)` | `[Go to Section](#section)` |

---

## 🖼️ Media Tags

### **Images**
| Language | Syntax | With Attributes |
|----------|--------|-----------------|
| **KryptoMarkup** | `{img src="image.jpg"/}` | `{img src="image.jpg" alt="Description" width="300"/}` |
| **HTML** | `<img src="image.jpg">` | `<img src="image.jpg" alt="Description" width="300">` |
| **Wiki Markup** | `[[File:image.jpg]]` | `[[File:image.jpg|300px|Description]]` |
| **Markdown** | `![](image.jpg)` | `![Description](image.jpg)` |

### **Videos**
| Language | Syntax | Example |
|----------|--------|---------|
| **KryptoMarkup** | `{video src="video.mp4" controls="true"/}` | `{video src="movie.mp4" width="640" height="480"/}` |
| **HTML** | `<video src="video.mp4" controls></video>` | `<video src="movie.mp4" width="640" height="480"></video>` |
| **Wiki Markup** | Not natively supported | Use HTML fallback |
| **Markdown** | Not supported | Use HTML fallback |

---

## 📊 Table Tags

### **Basic Tables**

#### KryptoMarkup
```
{table}
  {thead}
    {tr}
      {th}Header 1{/th}
      {th}Header 2{/th}
    {/tr}
  {/thead}
  {tbody}
    {tr}
      {td}Cell 1{/td}
      {td}Cell 2{/td}
    {/tr}
  {/tbody}
{/table}
```

#### HTML
```html
<table>
  <thead>
    <tr>
      <th>Header 1</th>
      <th>Header 2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Cell 1</td>
      <td>Cell 2</td>
    </tr>
  </tbody>
</table>
```

#### Wiki Markup
```
{| class="wikitable"
! Header 1
! Header 2
|-
| Cell 1
| Cell 2
|}
```

#### Markdown
```
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
```

---

## 💻 Code Blocks

### **Multiline Code Blocks**

#### KryptoMarkup
```
{codeblock lang="python"}
def hello():
    print("Hello World")
{/codeblock}
```

#### HTML
```html
<pre><code class="language-python">
def hello():
    print("Hello World")
</code></pre>
```

#### Wiki Markup
```
<syntaxhighlight lang="python">
def hello():
    print("Hello World")
</syntaxhighlight>
```

#### Markdown
````
```python
def hello():
    print("Hello World")
```
````

---

## 📦 Container/Structural Tags

### **Divs/Sections**
| Language | Syntax | With Attributes |
|----------|--------|-----------------|
| **KryptoMarkup** | `{div}Content{/div}` | `{div class="container" id="main"}Content{/div}` |
| **HTML** | `<div>Content</div>` | `<div class="container" id="main">Content</div>` |
| **Wiki Markup** | `<div>Content</div>` | Uses HTML |
| **Markdown** | Not supported | Use HTML fallback |

### **Paragraphs**
| Language | Syntax | Example |
|----------|--------|---------|
| **KryptoMarkup** | `{p}Paragraph text{/p}` | `{p class="intro"}Introduction text{/p}` |
| **HTML** | `<p>Paragraph text</p>` | `<p class="intro">Introduction text</p>` |
| **Wiki Markup** | Blank line separation | Double newline creates paragraph |
| **Markdown** | Blank line separation | Double newline creates paragraph |

---

## 🔐 KryptoMarkup Exclusive Tags

### **Security & Encryption Tags**
| Tag | Syntax | Purpose |
|-----|--------|---------|
| **Encrypted Content** | `{encrypt key="xyz"}Sensitive data{/encrypt}` | Encrypts content with specified key |
| **Digital Signature** | `{signature wallet="0x123..."}Content{/signature}` | Signs content with wallet |
| **Secure Container** | `{secure level="high"}Protected{/secure}` | Creates secure content zone |
| **Hash Verification** | `{hash type="sha256"}Data{/hash}` | Generates/verifies content hash |

### **Blockchain Integration**
| Tag | Syntax | Purpose |
|-----|--------|---------|
| **Smart Contract** | `{contract address="0x..."}Interface{/contract}` | Embeds contract interaction |
| **Transaction** | `{tx hash="0x..."/}` | References blockchain transaction |
| **Wallet Connect** | `{wallet provider="metamask"/}` | Wallet connection interface |
| **NFT Display** | `{nft contract="0x..." tokenId="123"/}` | Displays NFT content |

### **Advanced Features**
| Tag | Syntax | Purpose |
|-----|--------|---------|
| **Custom Components** | `{component name="chart" data="..."/}` | Custom reusable components |
| **Data Binding** | `{bind var="userName"}Name{/bind}` | Two-way data binding |
| **Conditional** | `{if condition="true"}Show{/if}` | Conditional rendering |
| **Loop/Iteration** | `{foreach items="list"}{item}{/foreach}` | Iterative rendering |

---

## 📝 Quotes & Citations

### **Blockquotes**
| Language | Syntax | Nested Quote |
|----------|--------|--------------|
| **KryptoMarkup** | `{blockquote}Quote text{/blockquote}` | `{blockquote}Main{blockquote}Nested{/blockquote}{/blockquote}` |
| **HTML** | `<blockquote>Quote text</blockquote>` | `<blockquote>Main<blockquote>Nested</blockquote></blockquote>` |
| **Wiki Markup** | `: Quote text` | `:: Nested quote` |
| **Markdown** | `> Quote text` | `> Main`<br>`>> Nested` |

### **Citations**
| Language | Syntax | Example |
|----------|--------|---------|
| **KryptoMarkup** | `{cite source="Author"}Text{/cite}` | `{cite source="Smith 2024"}Research{/cite}` |
| **HTML** | `<cite>Author</cite>` | `<cite>Smith 2024</cite>` |
| **Wiki Markup** | `<ref>Citation</ref>` | `<ref>Smith 2024</ref>` |
| **Markdown** | Not native (use footnotes) | `Text[^1]`<br>`[^1]: Citation` |

---

## 🎨 Styling & Formatting

### **CSS/Style Application**
| Language | Inline Style | Class Application |
|----------|--------------|-------------------|
| **KryptoMarkup** | `{span style="color:red"}Text{/span}` | `{div class="container"}Content{/div}` |
| **HTML** | `<span style="color:red">Text</span>` | `<div class="container">Content</div>` |
| **Wiki Markup** | Limited inline styles | Template-based styling |
| **Markdown** | Not supported | Use HTML fallback |

### **Color & Highlighting**
| Language | Text Color | Background Highlight |
|----------|------------|---------------------|
| **KryptoMarkup** | `{color value="red"}Text{/color}` | `{highlight color="yellow"}Text{/highlight}` |
| **HTML** | `<span style="color:red">Text</span>` | `<mark>Text</mark>` |
| **Wiki Markup** | `<span style="color:red">Text</span>` | Not native |
| **Markdown** | Not supported | Not supported |

---

## 🔄 Conversion Compatibility Matrix

| From ↓ To → | KryptoMarkup | HTML | Wiki Markup | Markdown |
|--------------|--------------|------|-------------|----------|
| **KryptoMarkup** | — | ✅ Full | ⚠️ Partial | ⚠️ Partial |
| **HTML** | ⚠️ Partial | — | ⚠️ Partial | ❌ Limited |
| **Wiki Markup** | ⚠️ Partial | ✅ Good | — | ⚠️ Partial |
| **Markdown** | ✅ Good | ✅ Full | ⚠️ Partial | — |

**Legend:**
- ✅ Full/Good = Most features convert cleanly
- ⚠️ Partial = Some features lost in conversion
- ❌ Limited = Significant feature loss

---

## 📊 Feature Support Comparison

| Feature | KryptoMarkup | HTML | Wiki Markup | Markdown |
|---------|--------------|------|-------------|----------|
| **Basic Text Formatting** | ✅ | ✅ | ✅ | ✅ |
| **Advanced Typography** | ✅ | ✅ | ⚠️ | ❌ |
| **Tables** | ✅ | ✅ | ✅ | ⚠️ |
| **Media Embedding** | ✅ | ✅ | ⚠️ | ⚠️ |
| **Interactive Elements** | ✅ | ✅ | ❌ | ❌ |
| **Forms** | ✅ | ✅ | ⚠️ | ❌ |
| **Scripting Support** | ✅ | ✅ | ⚠️ | ❌ |
| **Security Features** | ✅ | ⚠️ | ❌ | ❌ |
| **Blockchain Integration** | ✅ | ❌ | ❌ | ❌ |
| **Custom Components** | ✅ | ✅ | ⚠️ | ❌ |
| **Semantic Markup** | ✅ | ✅ | ⚠️ | ⚠️ |
| **Accessibility** | ✅ | ✅ | ⚠️ | ⚠️ |
| **Version Control Friendly** | ⚠️ | ❌ | ⚠️ | ✅ |
| **Human Readability** | ⚠️ | ❌ | ⚠️ | ✅ |
| **File Size Efficiency** | ⚠️ | ❌ | ✅ | ✅ |

---

## 🚀 Quick Reference Card

### Most Common Tags Comparison

| Action | KryptoMarkup | HTML | Wiki | Markdown |
|--------|--------------|------|------|----------|
| **Bold** | `{b}...{/b}` | `<b>...</b>` | `'''...'''` | `**...**` |
| **Italic** | `{i}...{/i}` | `<i>...</i>` | `''...''` | `*...*` |
| **Link** | `{link url=""}...{/link}` | `<a href="">...</a>` | `[url text]` | `[text](url)` |
| **Image** | `{img src=""/}` | `<img src="">` | `[[File:...]]` | `![](url)` |
| **Code** | `{code}...{/code}` | `<code>...</code>` | `<code>...</code>` | `` `...` `` |
| **List** | `{ul}{li}...{/li}{/ul}` | `<ul><li>...</li></ul>` | `* ...` | `- ...` |
| **Heading** | `{h1}...{/h1}` | `<h1>...</h1>` | `= ... =` | `# ...` |

---

## 💡 Best Practices & Tips

### KryptoMarkup
- Use semantic tags for better structure
- Leverage security features for sensitive content
- Utilize custom components for reusability
- Keep nesting clean and readable

### HTML
- Use semantic HTML5 elements
- Separate structure from presentation
- Validate markup for standards compliance
- Consider accessibility from the start

### Wiki Markup
- Keep formatting simple for collaboration
- Use templates for consistency
- Document custom extensions
- Prefer wiki syntax over HTML when possible

### Markdown
- Stick to CommonMark standard
- Use reference-style links for readability
- Keep tables simple
- Use HTML only when necessary

---

## 📚 Additional Resources

- **KryptoMarkup Spec**: [Future documentation site]
- **HTML Living Standard**: https://html.spec.whatwg.org/
- **MediaWiki Markup**: https://www.mediawiki.org/wiki/Help:Formatting
- **CommonMark**: https://commonmark.org/

---

*Last Updated: January 2025*
*Version: 1.0*