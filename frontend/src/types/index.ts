export type Frequency = 'once' | 'daily' | 'weekly' | 'monthly' | 'custom'
export type SkipPolicy = 'move' | 'overdue' | 'skip'
export type Priority = 'low' | 'medium' | 'high'
export type MemberRole = 'admin' | 'member' | 'limited'
export type EventStatus = 'done' | 'skipped' | 'overdue' | 'moved'

export interface User {
  id: string
  email: string
  name: string
  is_active?: boolean
}

export interface Room {
  id: string
  house_id: string
  name: string
  icon: string
  color: string
}

export interface Member {
  id: string
  house_id: string
  user_id: string
  role: MemberRole
  color: string
  allowed_room_ids: string[]
  user?: User
}

export interface Task {
  id: string
  house_id: string
  room_id: string | null
  assignee_id: string | null
  title: string
  description: string
  priority: Priority
  frequency: Frequency
  skip_policy: SkipPolicy
  start_date: string
  days_of_week: number[] | null
  custom_interval_days: number | null
  window_days: number
  effort_hours: number
  is_active: boolean
  created_at: string
}

export interface House {
  id: string
  name: string
  created_at: string
}

export interface TaskEvent {
  id: string
  task_id: string
  actor_id: string
  occurrence_date: string
  status: EventStatus
  moved_to: string | null
  note: string | null
  created_at: string
}

export interface TaskHistoryItem {
  id: string
  task_id: string
  actor_id: string
  occurrence_date: string
  status: EventStatus
  moved_to: string | null
  note: string | null
  created_at: string

  task_title: string
  task_priority: Priority
  room_id: string | null
  room_name: string | null
  room_icon: string | null

  actor_name: string
  actor_color: string
}

export interface Advice {
  id: string
  title: string
  content: string
  steps: string[]
  room_names: string[]
  task_keywords: string[]
  season?: string | null
  category: string
  is_active: boolean
}

export interface DailyPoint {
  date: string
  done: number
  total: number
  rate: number
}

export interface Metrics {
  adherence_rate: number
  streak: number
  completion_ratio: number
  overdue_rate: number
  total_planned: number
  total_done: number
  total_overdue: number
  consistency_score: number
}

export interface LoadItem {
  member_id: string
  member_name: string
  color: string
  done_count: number
  effort_hours: number
  percentage: number
}

export interface RoomAnalyticsItem {
  room_id: string | null
  room_name: string
  room_icon: string
  total_planned: number
  total_done: number
  total_overdue: number
  adherence_rate: number
}

export interface Analytics {
  metrics: Metrics
  daily_trend: DailyPoint[]
  load_distribution: LoadItem[]
  room_stats: RoomAnalyticsItem[]
}

// ---- RAG / AI ----

export interface AdviceSource {
  id: string
  title: string
  score: number
}

export interface HistorySummary {
  total: number
  done: number
  overdue: number
  completion_rate: number
}

export interface RagAdvice {
  main_advice: string
  steps: string[]
  warnings: string[]
  sources: AdviceSource[]
  delivery_id: string | null
  query_used?: string | null
  history?: HistorySummary | null
}

export type InsightSeverity = 'info' | 'warning' | 'critical'
export type InsightType =
  | 'good_streak'
  | 'declining_trend'
  | 'low_adherence_room'
  | 'most_overdue_task'
  | 'worst_weekday'
  | 'low_overall_adherence'

export interface HabitInsight {
  type: InsightType
  severity: InsightSeverity
  title: string
  description: string
  metric: number
  advice: RagAdvice | null
}

export interface HabitInsights {
  adherence_summary: string
  overall_status: 'good' | 'attention' | 'critical'
  global_adherence: number
  streak: number
  total_planned: number
  total_done: number
  insights: HabitInsight[]
}

// ---- Suggestions ----

export interface SuggestedTask {
  title: string
  room_name: string | null
  frequency: Frequency
  effort_hours: number
  reason: string
  source: 'gap' | 'seasonal' | 'llm'
  is_reschedule: boolean
}

export interface TaskSuggestionsResponse {
  season: string
  suggestions: SuggestedTask[]
}

// ---- Completion probability ----

export interface CompletionSignals {
  task_rate: number
  member_rate: number
  weekday_rate: number
  room_rate: number
}

export interface CompletionProbability {
  probability: number
  confidence: 'high' | 'medium' | 'low'
  signals: CompletionSignals
  reason: string
}

// ---- Nudge ----

export interface Nudge {
  should_nudge: boolean
  due_count: number
  message: string
  best_weekdays: string[]
  is_productive_day: boolean
}

export interface TaskFormData {
  title: string
  description: string
  room_id: string
  assignee_id: string
  priority: Priority
  frequency: Frequency
  skip_policy: SkipPolicy
  start_date: string
  days_of_week: number[]
  custom_interval_days: number
  window_days: number
  effort_hours: number
}