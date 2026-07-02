import { insightApi } from '@/features/insight/api/insightApi'
import type { Lang } from '@/features/insight/types/insight'

type Labelable = { label: string; labelEn?: string; labelZh?: string; labelJa?: string }

const FIELD = { en: 'labelEn', zh: 'labelZh', ja: 'labelJa' } as const

/** ko를 제외한 언어로 전환 시, 번역이 비어있는 토픽 라벨을 일괄 채워 넣는다 (in-place mutation). */
export async function fillTopicLabels(items: Labelable[], lang: Lang): Promise<void> {
  if (lang === 'ko') return
  const field = FIELD[lang]
  const missing = items.filter(t => !t[field])
  if (!missing.length) return
  try {
    const translations = await insightApi.translateLabels(missing.map(t => t.label), lang)
    missing.forEach((t, i) => { t[field] = translations[i] || t.label })
  } catch { /* 실패 시 한국어로 표시 유지 */ }
}

export function displayLabel(item: Labelable, lang: Lang): string {
  if (lang === 'ko') return item.label
  return item[FIELD[lang]] || item.label
}
