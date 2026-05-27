/**
 * @description Tests para extractMainContent — aisla el contenido principal
 *   de un HTML rendered antes de convertirlo a Markdown.
 */
import { describe, expect, it } from 'vitest'

import { extractMainContent } from '../../src/lib/extract-main-content'

describe('extractMainContent', () => {
  it('Given HTML con main+nav+footer When extract Then solo devuelve el contenido del main', () => {
    const html =
      '<body><nav>NAV</nav><main><h1>T</h1><p>OK</p></main><footer>F</footer></body>'

    const out = extractMainContent(html)

    expect(out).toBe('<h1>T</h1><p>OK</p>')
  })

  it('Given HTML sin main pero con article When extract Then devuelve el article', () => {
    const html = '<body><article><p>X</p></article></body>'

    const out = extractMainContent(html)

    expect(out).toBe('<p>X</p>')
  })

  it('Given HTML sin main ni article When extract Then devuelve el body innerHTML sin nav/footer', () => {
    const html = '<body><nav>N</nav><p>Y</p><footer>F</footer></body>'

    const out = extractMainContent(html)

    expect(out).toBe('<p>Y</p>')
  })

  it('Given HTML con script/style dentro del main When extract Then los elimina', () => {
    const html =
      '<body><main><script>alert(1)</script><p>OK</p><style>.x{}</style></main></body>'

    const out = extractMainContent(html)

    expect(out).toBe('<p>OK</p>')
  })

  it('Given HTML con elemento .tracking-pixel When extract Then lo elimina', () => {
    const html =
      '<body><main><p>OK</p><div class="tracking-pixel">px</div></main></body>'

    const out = extractMainContent(html)

    expect(out).toBe('<p>OK</p>')
  })

  it('Given HTML con elemento [data-tracking] When extract Then lo elimina', () => {
    const html = '<body><main><p>OK</p><img data-tracking="px"/></main></body>'

    const out = extractMainContent(html)

    expect(out).toBe('<p>OK</p>')
  })

  it('Given HTML con aside dentro del main When extract Then lo elimina', () => {
    const html = '<body><main><aside>A</aside><p>OK</p></main></body>'

    const out = extractMainContent(html)

    expect(out).toBe('<p>OK</p>')
  })
})
