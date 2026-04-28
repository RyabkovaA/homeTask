import type { Priority, Frequency, SkipPolicy } from '../types'

export interface TaskTemplate {
  title: string
  description: string
  priority: Priority
  frequency: Frequency
  skip_policy: SkipPolicy
  days_of_week?: number[]
  custom_interval_days?: number
  window_days?: number
  effort_hours: number
}

interface RoomTemplateGroup {
  keywords: string[]
  templates: TaskTemplate[]
}

const TEMPLATE_GROUPS: RoomTemplateGroup[] = [
  {
    keywords: ['кухн'],
    templates: [
      { title: 'Помыть посуду', description: '', priority: 'low', frequency: 'daily', skip_policy: 'skip', window_days: 0, effort_hours: 0.2 },
      { title: 'Протереть столешницы и плиту', description: '', priority: 'low', frequency: 'daily', skip_policy: 'skip', window_days: 0, effort_hours: 0.1 },
      { title: 'Вынести мусор', description: '', priority: 'medium', frequency: 'daily', skip_policy: 'overdue', window_days: 1, effort_hours: 0.1 },
      { title: 'Помыть плиту', description: '', priority: 'medium', frequency: 'weekly', skip_policy: 'overdue', days_of_week: [5], window_days: 2, effort_hours: 0.3 },
      { title: 'Чистить вытяжку (фильтры)', description: 'Снять и отмочить алюминиевые фильтры в горячей воде со стиральным порошком.', priority: 'high', frequency: 'monthly', skip_policy: 'move', window_days: 3, effort_hours: 0.5 },
      { title: 'Мыть холодильник', description: 'Вынуть все продукты, протереть полки раствором воды с уксусом 1:1.', priority: 'medium', frequency: 'monthly', skip_policy: 'overdue', window_days: 7, effort_hours: 1.0 },
      { title: 'Разморозить холодильник', description: 'Выключить, вынуть продукты, дать льду растаять, просушить и включить.', priority: 'medium', frequency: 'custom', custom_interval_days: 90, skip_policy: 'move', window_days: 7, effort_hours: 1.5 },
      { title: 'Чистить духовку', description: 'Нанести пасту из соды на стенки, оставить на ночь, смыть уксусом.', priority: 'medium', frequency: 'monthly', skip_policy: 'move', window_days: 7, effort_hours: 1.0 },
      {
        title: 'Разобрать крупы и бакалею',
        description:
          'Проверить даты на упаковках (гречка — до 18 мес., рис — до 18 мес., пшено — до 9 мес., мука — до 12 мес.). ' +
          'Выбросить просроченное. Переложить в герметичные контейнеры. ' +
          'Положить лавровый лист в каждый контейнер от вредителей.',
        priority: 'low', frequency: 'custom', custom_interval_days: 90, skip_policy: 'skip', window_days: 14, effort_hours: 0.5,
      },
    ],
  },
  {
    keywords: ['ванн', 'туалет', 'санузел'],
    templates: [
      { title: 'Мыть унитаз', description: '', priority: 'medium', frequency: 'weekly', skip_policy: 'overdue', days_of_week: [5], window_days: 2, effort_hours: 0.2 },
      { title: 'Мыть ванну / душевую кабину', description: '', priority: 'medium', frequency: 'weekly', skip_policy: 'overdue', days_of_week: [5], window_days: 2, effort_hours: 0.3 },
      { title: 'Протереть зеркало', description: '', priority: 'low', frequency: 'weekly', skip_policy: 'skip', window_days: 3, effort_hours: 0.1 },
      { title: 'Помыть пол', description: '', priority: 'medium', frequency: 'weekly', skip_policy: 'overdue', days_of_week: [5], window_days: 2, effort_hours: 0.2 },
      { title: 'Убрать известковый налёт', description: 'Уксусный компресс на смесители на 1–2 часа, старая зубная щётка для швов.', priority: 'medium', frequency: 'monthly', skip_policy: 'overdue', window_days: 7, effort_hours: 0.5 },
      { title: 'Прочистить слив', description: 'Засыпать соду, залить уксусом, закрыть пробкой на 15 мин, смыть кипятком.', priority: 'medium', frequency: 'monthly', skip_policy: 'move', window_days: 7, effort_hours: 0.3 },
    ],
  },
  {
    keywords: ['гостин', 'зал', 'living'],
    templates: [
      { title: 'Пылесосить', description: '', priority: 'medium', frequency: 'weekly', skip_policy: 'overdue', days_of_week: [6], window_days: 2, effort_hours: 0.4 },
      { title: 'Протереть пыль', description: '', priority: 'low', frequency: 'weekly', skip_policy: 'skip', days_of_week: [6], window_days: 3, effort_hours: 0.3 },
      { title: 'Помыть пол', description: '', priority: 'medium', frequency: 'weekly', skip_policy: 'overdue', days_of_week: [6], window_days: 2, effort_hours: 0.3 },
      { title: 'Протереть технику и экраны', description: 'ТВ, колонки, приставки — мягкой сухой тряпкой или специальной салфеткой.', priority: 'low', frequency: 'weekly', skip_policy: 'skip', window_days: 5, effort_hours: 0.2 },
      { title: 'Помыть окна', description: 'Скомканная газета + стеклоочиститель — без разводов. Лучше в пасмурный день.', priority: 'low', frequency: 'monthly', skip_policy: 'move', window_days: 14, effort_hours: 0.5 },
    ],
  },
  {
    keywords: ['спальн', 'bedroom'],
    templates: [
      { title: 'Сменить постельное бельё', description: '', priority: 'high', frequency: 'weekly', skip_policy: 'overdue', days_of_week: [6], window_days: 2, effort_hours: 0.5 },
      { title: 'Пылесосить пол', description: '', priority: 'medium', frequency: 'weekly', skip_policy: 'overdue', days_of_week: [6], window_days: 2, effort_hours: 0.3 },
      { title: 'Протереть пыль', description: '', priority: 'low', frequency: 'weekly', skip_policy: 'skip', window_days: 3, effort_hours: 0.2 },
      { title: 'Проветрить комнату', description: '10–15 минут при открытом окне. Снижает влажность и CO₂.', priority: 'low', frequency: 'daily', skip_policy: 'skip', window_days: 0, effort_hours: 0.1 },
      { title: 'Постирать подушки', description: 'Проверить этикетку. Большинство синтетических подушек — в стирку при 40°C.', priority: 'medium', frequency: 'monthly', skip_policy: 'move', window_days: 7, effort_hours: 0.5 },
      { title: 'Пропылесосить матрас', description: 'С обеих сторон. Убивает пылевых клещей. После можно обработать содой на 30 мин.', priority: 'medium', frequency: 'monthly', skip_policy: 'move', window_days: 7, effort_hours: 0.5 },
    ],
  },
  {
    keywords: ['балкон', 'лоджи'],
    templates: [
      { title: 'Подмести / помыть пол', description: '', priority: 'low', frequency: 'weekly', skip_policy: 'skip', window_days: 3, effort_hours: 0.2 },
      { title: 'Поливать растения', description: '', priority: 'medium', frequency: 'custom', custom_interval_days: 2, skip_policy: 'skip', window_days: 1, effort_hours: 0.1 },
      { title: 'Генеральная уборка балкона', description: 'Разобрать накопившиеся вещи, протереть полки, помыть окна и пол.', priority: 'medium', frequency: 'custom', custom_interval_days: 90, skip_policy: 'move', window_days: 14, effort_hours: 1.5 },
    ],
  },
  {
    keywords: ['прихожа', 'коридор', 'hallway'],
    templates: [
      { title: 'Пылесосить коврик', description: '', priority: 'medium', frequency: 'weekly', skip_policy: 'overdue', days_of_week: [6], window_days: 2, effort_hours: 0.1 },
      { title: 'Протереть обувь', description: 'Щётка + крем или пропитка по типу материала.', priority: 'low', frequency: 'weekly', skip_policy: 'skip', window_days: 3, effort_hours: 0.2 },
      { title: 'Разобрать вещи (сезонная уборка)', description: 'Убрать несезонную одежду и обувь, разложить текущий сезон.', priority: 'medium', frequency: 'custom', custom_interval_days: 90, skip_policy: 'move', window_days: 14, effort_hours: 1.0 },
    ],
  },
]

const GENERIC_TEMPLATES: TaskTemplate[] = [
  { title: 'Пылесосить', description: '', priority: 'medium', frequency: 'weekly', skip_policy: 'overdue', days_of_week: [6], window_days: 2, effort_hours: 0.4 },
  { title: 'Протереть пыль', description: '', priority: 'low', frequency: 'weekly', skip_policy: 'skip', window_days: 3, effort_hours: 0.3 },
  { title: 'Помыть пол', description: '', priority: 'medium', frequency: 'weekly', skip_policy: 'overdue', days_of_week: [6], window_days: 2, effort_hours: 0.3 },
  { title: 'Генеральная уборка', description: '', priority: 'high', frequency: 'monthly', skip_policy: 'move', window_days: 7, effort_hours: 2.0 },
]

export function getTemplatesForRoom(roomName: string): TaskTemplate[] {
  const name = roomName.toLowerCase()
  const group = TEMPLATE_GROUPS.find(g => g.keywords.some(kw => name.includes(kw)))
  return group?.templates ?? GENERIC_TEMPLATES
}
