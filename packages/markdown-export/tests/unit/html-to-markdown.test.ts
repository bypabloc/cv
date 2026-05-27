/**
 * @description Tests para htmlToMarkdown (turndown + GFM).
 */
import { describe, expect, it } from 'vitest'

import { htmlToMarkdown } from '../../src/lib/html-to-markdown'

describe('htmlToMarkdown', () => {
  it('Given HTML con H1+p When convert Then devuelve Markdown ATX con trailing newline', () => {
    const out = htmlToMarkdown({ html: '<h1>Pablo</h1><p>Lorem</p>' })

    expect(out).toBe('# Pablo\n\nLorem\n')
  })

  it('Given HTML con table simple When convert Then devuelve GFM table', () => {
    const html =
      '<table><thead><tr><th>A</th><th>B</th></tr></thead>' +
      '<tbody><tr><td>1</td><td>2</td></tr></tbody></table>'

    const out = htmlToMarkdown({ html })

    expect(out).toContain('| A | B |')
    expect(out).toContain('| 1 | 2 |')
  })

  it('Given HTML con script inline When convert Then descarta el script', () => {
    const out = htmlToMarkdown({
      html: '<p>OK</p><script>alert(1)</script>',
    })

    expect(out).toBe('OK\n')
  })

  it('Given HTML con style inline When convert Then descarta el style', () => {
    const out = htmlToMarkdown({
      html: '<style>.x { color: red }</style><p>OK</p>',
    })

    expect(out).toBe('OK\n')
  })

  it('Given HTML con link When convert Then preserva el href como Markdown link', () => {
    const out = htmlToMarkdown({
      html: '<p>Visita <a href="https://x.com">X</a> ahora</p>',
    })

    expect(out).toBe('Visita [X](https://x.com) ahora\n')
  })

  it('Given HTML con ul When convert Then usa - como bullet marker', () => {
    const out = htmlToMarkdown({
      html: '<ul><li>uno</li><li>dos</li></ul>',
    })

    // turndown 7.x renderiza bullets como "-   item" (3 espacios) para
    // dejar alineado contenido multi-linea dentro del bullet.
    expect(out).toBe('-   uno\n-   dos\n')
  })

  it('Given HTML con code block When convert Then usa fenced code block', () => {
    const out = htmlToMarkdown({
      html: '<pre><code>const x = 1\n</code></pre>',
    })

    expect(out).toBe('```\nconst x = 1\n```\n')
  })

  it('Given HTML vacio When convert Then devuelve string vacio', () => {
    expect(htmlToMarkdown({ html: '' })).toBe('')
  })

  it('Given HTML solo con whitespace When convert Then devuelve string vacio', () => {
    expect(htmlToMarkdown({ html: '   \n\n  ' })).toBe('')
  })

  it('Given HTML con strong+em When convert Then usa ** y _ como delimitadores', () => {
    const out = htmlToMarkdown({
      html: '<p><strong>bold</strong> y <em>cursivo</em></p>',
    })

    expect(out).toBe('**bold** y _cursivo_\n')
  })
})
