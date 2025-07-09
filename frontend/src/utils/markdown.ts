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
  // Step 1: Replace LaTeX expressions with placeholders to preserve them during markdown processing
  let placeholderCounter = 0
  const latexReplacements: Record<string, string> = {}
  
  // Replace block LaTeX expressions with placeholders
  let processedContent = content.replace(BLOCK_LATEX_REGEX, (match, latex1, latex2, latex3) => {
    // Determine which capture group has the content
    const latex = latex1 || latex2 || latex3
    
    if (!latex) return match
    
    const placeholder = `__LATEX_BLOCK_${placeholderCounter++}__`
    
    try {
      const rendered = katex.renderToString(latex.trim(), {
        displayMode: true,
        throwOnError: false,
        errorColor: '#cc0000',
        strict: 'warn'
      })
      latexReplacements[placeholder] = `<div class="latex-block-container">${rendered}</div>`
    } catch (error) {
      console.error('Block LaTeX rendering error:', error)
      latexReplacements[placeholder] = `<div class="latex-error">${match}</div>`
    }
    
    return placeholder
  })

  // Replace inline LaTeX expressions with placeholders
  processedContent = processedContent.replace(INLINE_LATEX_REGEX, (match, latex1, latex2, latex3) => {
    // Determine which capture group has the content
    const latex = latex1 || latex2 || latex3
    
    if (!latex) return match
    
    const placeholder = `__LATEX_INLINE_${placeholderCounter++}__`
    
    try {
      const rendered = katex.renderToString(latex.trim(), {
        displayMode: false,
        throwOnError: false,
        errorColor: '#cc0000',
        strict: 'warn'
      })
      latexReplacements[placeholder] = `<span class="latex-inline-container">${rendered}</span>`
    } catch (error) {
      console.error('Inline LaTeX rendering error:', error)
      latexReplacements[placeholder] = `<span class="latex-error">${match}</span>`
    }
    
    return placeholder
  })

  // Step 2: Process markdown (this may wrap placeholders in HTML tags)
  let htmlContent = marked(processedContent, {
    breaks: true,
    gfm: true
  }) as string

  // Step 3: Restore LaTeX placeholders with rendered content using regex to handle HTML wrapping
  Object.keys(latexReplacements).forEach(placeholder => {
    // Create regex to match placeholder even when wrapped in HTML tags like <strong>PLACEHOLDER</strong>
    // We need to handle the case where markdown wraps __PLACEHOLDER__ as <strong>PLACEHOLDER</strong>
    const placeholderWithoutUnderscores = placeholder.replace(/^__/, '').replace(/__$/, '')
    const escapedPlaceholder = placeholderWithoutUnderscores.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    
    // Match the placeholder with or without HTML tags
    const placeholderRegex = new RegExp(`(<[^>]*>)?(${escapedPlaceholder})(<[^>]*>)?`, 'g')
    
    htmlContent = htmlContent.replace(placeholderRegex, (match, openTag, core, closeTag) => {
      // If the placeholder was wrapped in tags (like <strong>), replace the entire match
      return latexReplacements[placeholder]
    })
    
    // Also handle the case where the full placeholder with underscores might still exist
    const fullPlaceholderRegex = new RegExp(placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g')
    htmlContent = htmlContent.replace(fullPlaceholderRegex, latexReplacements[placeholder])
  })

  // Step 4: Clean up block LaTeX that got wrapped in paragraph tags
  htmlContent = htmlContent.replace(/<p>(<div class="latex-block-container">.*?<\/div>)<\/p>/g, '$1')

  // Step 5: Wrap tables in responsive containers
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
