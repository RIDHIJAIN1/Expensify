export interface User {
  id: number
  email: string
  name: string | null
}

export interface Category {
  id: number
  name: string
  keywords: string[]
  is_custom: boolean
  color: string | null
}

export interface Transaction {
  id: number
  date: string
  description: string
  amount: string
  type: string
  reference: string | null
  category_id: number | null
  category_name: string | null
}

export interface Upload {
  id: number
  filename: string
  status: string
  total_rows: number
  imported_count: number
  duplicate_count: number
  error_summary: string[] | null
  created_at: string
}

export interface CategoryTotal {
  category_id: number | null
  category_name: string
  total: string
  count: number
}

export interface MonthlyTotal {
  month: string
  debit: string
  credit: string
  count: number
}

export interface MerchantTotal {
  name: string
  total: string
  count: number
}

export interface Summary {
  total_income: string
  total_spent: string
  net: string
  transaction_count: number
  by_category: CategoryTotal[]
  by_month: MonthlyTotal[]
  top_merchants: MerchantTotal[]
}

export interface TransactionList {
  total: number
  items: Transaction[]
}

export interface Budget {
  category_id: number
  category_name: string
  color: string | null
  limit: string
  spent: string
  remaining: string
  percent: number
  over: boolean
}

export interface Insight {
  icon: string
  tone: string
  title: string
  detail: string
}

export interface TransactionUpdateResult {
  transaction: Transaction
  learned_keyword: string | null
  reclassified: number
}

export interface DateRange {
  from: string
  to: string
}
