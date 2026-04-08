export type Frequency = 'once' | 'daily' | 'weekly' | 'monthly' | 'custom'
export type SkipPolicy = 'move' | 'overdue' | 'skip'
export type Priority = 'low' | 'medium' | 'high'
export type MemberRole = 'admin' | 'member' | 'limited'
export type EventStatus = 'done' | 'skipped' | 'overdue' | 'moved'

export interface User {
  id: string
  email: string
  name: string
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
  is_active: boolean
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

export interface Advice {
  id: string
  title: string
  content: string
  steps: string[]
  room_names: string[]
  task_keywords: string[]
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
}

export interface LoadItem {
  member_id: string
  member_name: string
  color: string
  done_count: number
  percentage: number
}

export interface Analytics {
  metrics: Metrics
  daily_trend: DailyPoint[]
  load_distribution: LoadItem[]
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
}
