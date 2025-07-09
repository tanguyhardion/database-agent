import { marked } from 'marked'
import katex from 'katex'
import Prism from 'prismjs'

// Import only essential language components for syntax highlighting
// Keep it minimal - only commonly used languages
import 'prismjs/components/prism-clike' // Base for C-like languages (required first)
import 'prismjs/components/prism-javascript'
import 'prismjs/components/prism-typescript'
import 'prismjs/components/prism-python'
import 'prismjs/components/prism-sql'
import 'prismjs/components/prism-json'
import 'prismjs/components/prism-bash'
import 'prismjs/components/prism-css'
import 'prismjs/components/prism-markup' // HTML/XML

// Regular expressions for LaTeX patterns
const INLINE_LATEX_REGEX = /\$([^$\n]+?)\$|\\\(([^)]+?)\\\)|\( ([^)]+?) \)/g
const BLOCK_LATEX_REGEX = /\$\$([^$]+?)\$\$|\\\[([^\]]+?)\\\]|\[ ([^\]]+?) \]/g

// Configure marked with custom renderer for syntax highlighting
const renderer = new marked.Renderer()

// Override code block rendering to add syntax highlighting
renderer.code = function({ text, lang }: { text: string; lang?: string }) {
  // Default to plain text if no language specified
  let language = lang || 'text'
  
  // Handle common language aliases (keep it simple)
  const languageAliases: { [key: string]: string } = {
    'js': 'javascript',
    'ts': 'typescript',
    'py': 'python',
    'sh': 'bash',
    'shell': 'bash',
    'html': 'markup',
    'xml': 'markup'
  }
  
  // Apply alias if it exists
  if (languageAliases[language.toLowerCase()]) {
    language = languageAliases[language.toLowerCase()]
  }
  
  try {
    // Check if Prism supports this language
    const grammar = Prism.languages[language]
    if (grammar && typeof grammar === 'object') {
      const highlighted = Prism.highlight(text, grammar, language)
      return `<pre><code>${highlighted}</code></pre>`
    }
  } catch (error) {
    console.warn(`Syntax highlighting failed for language: ${language}`, error)
    // Fall through to plain text rendering
  }
  
  // Fallback to plain code block
  return `<pre><code>${text.replace(/[&<>"']/g, (match) => {
    const escapeMap: { [key: string]: string } = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    }
    return escapeMap[match]
  })}</code></pre>`
}

// Configure marked options
marked.setOptions({
  renderer,
  breaks: true,
  gfm: true
})

/**
 * Renders LaTeX expressions within markdown content
 * @param content - The markdown content that may contain LaTeX
 * @returns HTML string with rendered LaTeX
 */
export function renderMarkdownWithLatex(content: string): string {
  // First, replace block LaTeX expressions ($$...$$, \[...\], [ ... ])
  let processedContent = content.replace(BLOCK_LATEX_REGEX, (match, latex1, latex2, latex3) => {
    // Determine which capture group has the content
    const latex = latex1 || latex2 || latex3
    
    if (!latex) return match
    
    try {
      const rendered = katex.renderToString(latex.trim(), {
        displayMode: true,
        throwOnError: false,
        errorColor: '#cc0000',
        strict: 'warn'
      })
      return `<div class="latex-block-container">${rendered}</div>`
    } catch (error) {
      console.error('Block LaTeX rendering error:', error)
      return `<div class="latex-error">${match}</div>`
    }
  })

  // Then, replace inline LaTeX expressions ($...$, \(...\), ( ... ))
  processedContent = processedContent.replace(INLINE_LATEX_REGEX, (match, latex1, latex2, latex3) => {
    // Determine which capture group has the content
    const latex = latex1 || latex2 || latex3
    
    if (!latex) return match
    
    try {
      const rendered = katex.renderToString(latex.trim(), {
        displayMode: false,
        throwOnError: false,
        errorColor: '#cc0000',
        strict: 'warn'
      })
      return `<span class="latex-inline-container">${rendered}</span>`
    } catch (error) {
      console.error('Inline LaTeX rendering error:', error)
      return `<span class="latex-error">${match}</span>`
    }
  })

  // Process markdown with syntax highlighting
  const htmlContent = marked(processedContent) as string

  // Wrap tables in responsive containers
  return htmlContent
    .replace(/<table>/g, '<div class="table-wrapper"><table>')
    .replace(/<\/table>/g, '</table></div>')
}

/**
 * Check if content contains LaTeX expressions
 * @param content - The content to check
 * @returns boolean indicating if LaTeX is present
 */
export function containsLatex(content: string): boolean {
  return INLINE_LATEX_REGEX.test(content) || BLOCK_LATEX_REGEX.test(content)
}
