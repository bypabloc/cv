/**
 * @module client
 * @description Interaccion del sitio (un solo bundle): toggle de tema,
 *   boton copiar en bloques de codigo y capitulo activo en el TOC.
 */
import {
  nextTheme,
  readStoredTheme,
  storeTheme,
} from '@portfolio/ui/lib/theme-toggle'

function setupThemeToggle(): void {
  const btn = document.querySelector<HTMLButtonElement>('.theme-toggle')
  if (!btn) return
  const names = JSON.parse(btn.dataset.names ?? '{}') as Record<string, string>
  const template = btn.dataset.label ?? '{theme}'
  const label = (theme: string) =>
    btn.setAttribute(
      'aria-label',
      template.replace('{theme}', names[theme] ?? theme),
    )
  label(readStoredTheme())
  btn.addEventListener('click', () => {
    const next = nextTheme(readStoredTheme())
    storeTheme(next)
    label(next)
  })
}

function setupCopyButtons(): void {
  const strings = document.body.dataset
  for (const pre of document.querySelectorAll<HTMLPreElement>('.prose pre')) {
    const wrap = document.createElement('div')
    wrap.className = 'code-block'
    pre.replaceWith(wrap)
    wrap.append(pre)
    const btn = document.createElement('button')
    btn.type = 'button'
    btn.className = 'copy-btn'
    btn.textContent = strings.copy ?? 'Copy'
    btn.addEventListener('click', async () => {
      await navigator.clipboard.writeText(pre.innerText)
      btn.textContent = strings.copied ?? 'Copied'
      btn.dataset.copied = ''
      setTimeout(() => {
        btn.textContent = strings.copy ?? 'Copy'
        delete btn.dataset.copied
      }, 2000)
    })
    wrap.append(btn)
  }
}

function setupTocHighlight(): void {
  const links = new Map(
    [...document.querySelectorAll<HTMLAnchorElement>('.toc a')].map((a) => [
      a.hash.slice(1),
      a,
    ]),
  )
  if (links.size === 0) return
  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue
        for (const a of links.values()) a.removeAttribute('aria-current')
        const id = (entry.target as HTMLElement).dataset.chapter ?? ''
        links.get(id)?.setAttribute('aria-current', 'true')
      }
    },
    { rootMargin: '-20% 0px -70% 0px' },
  )
  for (const section of document.querySelectorAll('section[data-chapter]')) {
    observer.observe(section)
  }
}

// En movil el TOC arranca plegado para no empujar el contenido.
if (!matchMedia('(min-width: 1024px)').matches) {
  document.querySelector('.toc details')?.removeAttribute('open')
}

setupThemeToggle()
setupCopyButtons()
setupTocHighlight()
