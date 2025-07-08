import { marked } from 'marked'
import katex from 'katex'

// Regular expressions for LaTeX patterns
const INLINE_LATEX_REGEX = /\$([^$\n]+?)\$|\\\(([^)]+?)\\\)|\( ([^)]+?) \)/g
const BLOCK_LATEX_REGEX = /\$\$([^$]+?)\$\$|\\\[([^\]]+?)\\\]|\[ ([^\]]+?) \]/g

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

  // Process markdown
  const htmlContent = marked(processedContent, {
    breaks: true,
    gfm: true
  }) as string

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
