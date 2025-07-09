// Test to understand placeholder issue
import { marked } from 'marked'

// Test content with both inline and block LaTeX
const testContent = `Here is some inline math: $x = y + z$ and some text.

And here is a block equation:

$$\\int_0^1 x^2 dx = \\frac{1}{3}$$

Some **markdown** formatting.`

console.log('=== Original Content ===')
console.log(testContent)

// Step 1: Replace LaTeX with placeholders (as described in problem statement)
let placeholderCounter = 0
const latexReplacements: Record<string, string> = {}

// Replace block LaTeX with placeholders
let processedContent = testContent.replace(/\$\$([^$]+?)\$\$/g, (match, latex) => {
  const placeholder = `__LATEX_BLOCK_${placeholderCounter++}__`
  latexReplacements[placeholder] = `<div class="latex-block-container">RENDERED_BLOCK_${latex}</div>`
  return placeholder
})

// Replace inline LaTeX with placeholders  
processedContent = processedContent.replace(/\$([^$\n]+?)\$/g, (match, latex) => {
  const placeholder = `__LATEX_INLINE_${placeholderCounter++}__`
  latexReplacements[placeholder] = `<span class="latex-inline-container">RENDERED_INLINE_${latex}</span>`
  return placeholder
})

console.log('\n=== Content with Placeholders ===')
console.log(processedContent)

console.log('\n=== LaTeX Replacements Map ===')
console.log(latexReplacements)

// Step 2: Process markdown (this wraps placeholders in HTML tags)
let htmlContent = marked(processedContent, {
  breaks: true,
  gfm: true
}) as string

console.log('\n=== After Markdown Processing ===')
console.log(htmlContent)

// Step 3: Try current problematic replacement (exact string match)
console.log('\n=== Trying Exact String Replacement (Current Broken Approach) ===')
Object.keys(latexReplacements).forEach(placeholder => {
  const before = htmlContent
  htmlContent = htmlContent.replace(new RegExp(placeholder, 'g'), latexReplacements[placeholder])
  if (before === htmlContent) {
    console.log(`Failed to replace: ${placeholder}`)
  } else {
    console.log(`Successfully replaced: ${placeholder}`)
  }
})

console.log('\n=== Final Result (Broken) ===')
console.log(htmlContent)

export { }