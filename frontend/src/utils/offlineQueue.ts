import { openDB, type IDBPDatabase } from 'idb'

const DB_NAME = 'hometask-offline'
const DB_VERSION = 1
const STORE = 'pending-events'

export interface PendingEvent {
  localId: string
  payload: {
    task_id: string
    occurrence_date: string
    status: 'done' | 'skipped' | 'overdue' | 'moved'
    moved_to?: string | null
    note?: string | null
  }
  createdAt: number
  retries: number
}

let _db: IDBPDatabase | null = null

async function getDB(): Promise<IDBPDatabase> {
  if (_db) return _db
  _db = await openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: 'localId' })
      }
    },
  })
  return _db
}

export async function enqueueEvent(event: Omit<PendingEvent, 'createdAt' | 'retries'>): Promise<void> {
  const db = await getDB()
  await db.put(STORE, { ...event, createdAt: Date.now(), retries: 0 })
}

export async function getPendingEvents(): Promise<PendingEvent[]> {
  const db = await getDB()
  return db.getAll(STORE)
}

export async function removeEvent(localId: string): Promise<void> {
  const db = await getDB()
  await db.delete(STORE, localId)
}

export async function incrementRetry(localId: string): Promise<void> {
  const db = await getDB()
  const tx = db.transaction(STORE, 'readwrite')
  const item = await tx.store.get(localId)
  if (item) await tx.store.put({ ...item, retries: item.retries + 1 })
  await tx.done
}

export async function clearQueue(): Promise<void> {
  const db = await getDB()
  await db.clear(STORE)
}
