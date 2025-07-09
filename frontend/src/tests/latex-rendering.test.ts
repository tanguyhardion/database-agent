/**
 * Test for LaTeX rendering with placeholder replacement
 * This test validates the fix for the bug where markdown processing
 * wrapped LaTeX placeholders in HTML tags, breaking replacement.
 */
import { renderMarkdownWithLatex } from '../utils/markdown'

// Test cases to validate the LaTeX placeholder fix
const testCases = [
  {
    name: 'Mixed inline and block LaTeX',
    input: `Here's inline math: $x = y + z$ and block:

$$\\int_0^1 x^2 dx = \\frac{1}{3}$$

More text.`,
    shouldContain: ['latex-inline-container', 'latex-block-container'],
    shouldNotContain: ['__LATEX_BLOCK_', '__LATEX_INLINE_']
  },
  {
    name: 'LaTeX with markdown formatting',
    input: `**Bold** text with $E = mc^2$ and more **bold**.`,
    shouldContain: ['<strong>Bold</strong>', 'latex-inline-container'],
    shouldNotContain: ['__LATEX_INLINE_']
  },
  {
    name: 'Multiple inline expressions',
    input: `Start $a=b$ middle $c=d$ end $e=f$ done.`,
    shouldContain: ['latex-inline-container'],
    shouldNotContain: ['__LATEX_INLINE_']
  },
  {
    name: 'LaTeX with underscores (potential markdown conflict)',
    input: `Variables $x_1 = y_2$ and block $$z_3 = w_4$$`,
    shouldContain: ['latex-inline-container', 'latex-block-container'],
    shouldNotContain: ['__LATEX_BLOCK_', '__LATEX_INLINE_']
  }
]

function runTests() {
  console.log('Running LaTeX placeholder replacement tests...\n')
  
  let passed = 0
  let failed = 0
  
  testCases.forEach((testCase, index) => {
    console.log(`Test ${index + 1}: ${testCase.name}`)
    
    try {
      const result = renderMarkdownWithLatex(testCase.input)
      
      // Check for required content
      const missingRequired = testCase.shouldContain.filter(content => !result.includes(content))
      const foundProhibited = testCase.shouldNotContain.filter(content => result.includes(content))
      
      if (missingRequired.length === 0 && foundProhibited.length === 0) {
        console.log('✅ PASSED\n')
        passed++
      } else {
        console.log('❌ FAILED')
        if (missingRequired.length > 0) {
          console.log(`  Missing required content: ${missingRequired.join(', ')}`)
        }
        if (foundProhibited.length > 0) {
          console.log(`  Found prohibited content: ${foundProhibited.join(', ')}`)
        }
        console.log('  Result:', result)
        console.log('')
        failed++
      }
    } catch (error) {
      console.log('❌ FAILED with error:', error)
      console.log('')
      failed++
    }
  })
  
  console.log(`Tests completed: ${passed} passed, ${failed} failed`)
  
  if (failed === 0) {
    console.log('🎉 All tests passed! LaTeX placeholder replacement is working correctly.')
  } else {
    console.log('⚠️  Some tests failed. Please check the implementation.')
  }
  
  return failed === 0
}

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const success = runTests()
  process.exit(success ? 0 : 1)
}

export { runTests }