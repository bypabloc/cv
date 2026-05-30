/**
 * @description Tests para applyStagger + bindStaggerOnLoad.
 *   Cubre: marcado de items (--stagger-idx + stagger-pending), el fallback
 *   sin IntersectionObserver, el observe + callback (isIntersecting true/
 *   false) y el escaneo de [data-stagger] de bindStaggerOnLoad.
 *
 *   Nota: happy-dom NO soporta el selector `:scope` (devuelve 0), asi que
 *   estos tests pasan selectores planos (`article`, `li`). En el browser
 *   real el codigo usa `:scope > *`; el comportamiento de marcado/observe
 *   es identico — solo cambia el selector de entrada.
 */
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { applyStagger, bindStaggerOnLoad } from '../../src/lib/stagger'

describe('applyStagger', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
  })

  it('Given items When apply Then sets --stagger-idx + stagger-pending', () => {
    document.body.innerHTML = `
      <div id="c"><article></article><article></article><article></article></div>
    `
    const container = document.querySelector('#c') as HTMLElement

    applyStagger(container, 'article')

    const items = Array.from(container.querySelectorAll<HTMLElement>('article'))
    expect(items.map((i) => i.style.getPropertyValue('--stagger-idx'))).toEqual(
      ['0', '1', '2'],
    )
    expect(items.every((i) => i.classList.contains('stagger-pending'))).toBe(
      true,
    )
  })

  it('Given IntersectionObserver undefined When apply Then marks all visible (fallback)', () => {
    const original = globalThis.IntersectionObserver
    Object.defineProperty(globalThis, 'IntersectionObserver', {
      configurable: true,
      writable: true,
      value: undefined,
    })

    document.body.innerHTML = '<div id="c"><article></article></div>'
    const container = document.querySelector('#c') as HTMLElement

    const observer = applyStagger(container, 'article')

    const item = container.querySelector<HTMLElement>('article') as HTMLElement
    expect(observer).toBe(null)
    expect(item.classList.contains('stagger-pending')).toBe(false)
    expect(item.classList.contains('stagger-visible')).toBe(true)

    globalThis.IntersectionObserver = original
  })

  it('Given IO available When item intersects Then adds stagger-visible + unobserves', () => {
    const observed: Element[] = []
    const unobserved: Element[] = []
    let cbRef: IntersectionObserverCallback | undefined

    const FakeIO = class {
      constructor(cb: IntersectionObserverCallback) {
        cbRef = cb
      }
      observe(el: Element) {
        observed.push(el)
      }
      unobserve(el: Element) {
        unobserved.push(el)
      }
      disconnect() {
        // no-op
      }
      takeRecords() {
        return []
      }
      root = null
      rootMargin = ''
      thresholds = []
    }
    const original = globalThis.IntersectionObserver
    globalThis.IntersectionObserver =
      FakeIO as unknown as typeof IntersectionObserver

    document.body.innerHTML = `
      <div id="c"><article id="a"></article><article id="b"></article></div>
    `
    const container = document.querySelector('#c') as HTMLElement

    const observer = applyStagger(container, 'article')
    expect(observer).not.toBe(null)
    expect(observed.length).toBe(2)

    const items = Array.from(container.querySelectorAll<HTMLElement>('article'))
    // a intersecta; b no -> solo a recibe stagger-visible + unobserve.
    const entries = [
      { target: items[0] as HTMLElement, isIntersecting: true },
      { target: items[1] as HTMLElement, isIntersecting: false },
    ] as unknown as IntersectionObserverEntry[]
    cbRef?.(entries, observer as IntersectionObserver)

    expect(items[0]?.classList.contains('stagger-visible')).toBe(true)
    expect(items[1]?.classList.contains('stagger-visible')).toBe(false)
    expect(unobserved).toEqual([items[0]])

    globalThis.IntersectionObserver = original
  })
})

describe('bindStaggerOnLoad', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('Given [data-stagger] containers When bind Then returns one observer each', () => {
    const observed: Element[] = []
    const FakeIO = class {
      observe(el: Element) {
        observed.push(el)
      }
      unobserve() {
        // no-op
      }
      disconnect() {
        // no-op
      }
      takeRecords() {
        return []
      }
      root = null
      rootMargin = ''
      thresholds = []
    }
    const original = globalThis.IntersectionObserver
    globalThis.IntersectionObserver =
      FakeIO as unknown as typeof IntersectionObserver

    document.body.innerHTML = `
      <ul data-stagger><li></li><li></li></ul>
      <ol data-stagger><li></li></ol>
    `

    const observers = bindStaggerOnLoad('li')

    // 2 containers con IO -> 2 observers; 3 items observados en total.
    expect(observers.length).toBe(2)
    expect(observed.length).toBe(3)

    globalThis.IntersectionObserver = original
  })

  it('Given no IO When bind Then skips null observers', () => {
    const original = globalThis.IntersectionObserver
    Object.defineProperty(globalThis, 'IntersectionObserver', {
      configurable: true,
      writable: true,
      value: undefined,
    })

    document.body.innerHTML = '<ul data-stagger><li></li></ul>'

    const observers = bindStaggerOnLoad('li')

    // applyStagger devuelve null sin IO -> no se acumula ningun observer.
    expect(observers).toEqual([])

    globalThis.IntersectionObserver = original
  })
})
