import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  ArrowUpRight,
  ChevronLeft,
  LayoutDashboard,
  LogOut,
  Menu,
  PanelLeft,
  ReceiptText,
  Tags,
  X,
} from 'lucide-react'
import { useAuth } from '../../auth/AuthContext'
import { cn } from '../../lib/cn'

const NAV_ITEMS = [
  { to: '/app/dashboard', label: 'Dashboard', icon: LayoutDashboard, hint: 'Spending insights' },
  { to: '/app/transactions', label: 'Transactions', icon: ReceiptText, hint: 'Browse & recategorize' },
  { to: '/app/categories', label: 'Categories', icon: Tags, hint: 'Keyword rules' },
]

function Logo({ collapsed }: { collapsed: boolean }) {
  return (
    <div className={cn('flex items-center gap-2.5', collapsed && 'justify-center')}>
      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-900/40">
        <span className="font-display text-sm font-extrabold text-white">E</span>
      </div>
      {!collapsed && (
        <div className="min-w-0">
          <p className="font-display text-base font-bold leading-none text-white">Expensify</p>
          <p className="mt-0.5 text-[10px] font-medium uppercase tracking-widest text-indigo-300/70">
            Classification
          </p>
        </div>
      )}
    </div>
  )
}

function SidebarContent({
  collapsed,
  onNavigate,
  onToggle,
}: {
  collapsed: boolean
  onNavigate?: () => void
  onToggle?: () => void
}) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const initials = (user?.name || user?.email || '?')
    .split(' ')
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  return (
    <div className="flex h-full flex-col bg-ink-950">
      <div className={cn('flex items-center px-5 pb-6 pt-6', collapsed ? 'justify-center px-3' : 'justify-between')}>
        <Logo collapsed={collapsed} />
        {onToggle && !collapsed && (
          <button
            type="button"
            onClick={onToggle}
            title="Collapse sidebar"
            className="hidden rounded-lg p-2 text-slate-500 transition hover:bg-white/10 hover:text-white lg:block"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        )}
      </div>

      <nav className={cn('flex-1 space-y-1', collapsed ? 'px-2' : 'px-3')}>
        {collapsed && onToggle && (
          <button
            type="button"
            onClick={onToggle}
            title="Expand sidebar"
            className="mb-2 hidden w-full items-center justify-center rounded-xl p-2.5 text-slate-500 transition hover:bg-white/10 hover:text-white lg:flex"
          >
            <PanelLeft className="h-[18px] w-[18px]" />
          </button>
        )}
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            title={collapsed ? item.label : undefined}
            className={({ isActive }) =>
              cn(
                'group flex items-center gap-3 rounded-xl py-2.5 text-sm font-semibold transition-all',
                collapsed ? 'justify-center px-0' : 'px-3',
                isActive
                  ? 'bg-gradient-to-r from-indigo-600/90 to-violet-600/80 text-white shadow-lg shadow-indigo-950/50'
                  : 'text-slate-400 hover:bg-white/5 hover:text-white',
              )
            }
          >
            <item.icon className="h-[18px] w-[18px] shrink-0" strokeWidth={2.2} />
            {!collapsed && <span className="flex-1">{item.label}</span>}
            {!collapsed && (
              <ArrowUpRight className="h-3.5 w-3.5 opacity-0 transition group-hover:opacity-60" />
            )}
          </NavLink>
        ))}
      </nav>

      <div className={cn('mx-3 mb-3 rounded-2xl border border-white/5 bg-white/[0.04] p-3', collapsed && 'mx-2 p-2')}>
        <div className={cn('flex items-center gap-3', collapsed && 'justify-center')}>
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-fuchsia-500 to-indigo-500 text-xs font-bold text-white">
            {initials}
          </div>
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-white">{user?.name || 'Account'}</p>
              <p className="truncate text-[11px] text-slate-400">{user?.email}</p>
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={handleLogout}
          title="Sign out"
          className={cn(
            'mt-3 flex w-full items-center justify-center gap-2 rounded-lg border border-white/10 py-2 text-xs font-semibold text-slate-300 transition hover:border-rose-500/40 hover:bg-rose-500/10 hover:text-rose-300',
          )}
        >
          <LogOut className="h-3.5 w-3.5" />
          {!collapsed && 'Sign out'}
        </button>
      </div>
    </div>
  )
}

export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [collapsed, setCollapsed] = useState(
    () => localStorage.getItem('sidebarCollapsed') === '1',
  )
  const location = useLocation()
  const { user } = useAuth()

  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  const toggleCollapsed = () => {
    setCollapsed((current) => {
      localStorage.setItem('sidebarCollapsed', current ? '0' : '1')
      return !current
    })
  }

  const firstName = (user?.name || user?.email || 'there').split(' ')[0]

  return (
    <div className="min-h-screen bg-[#f4f5fb]">
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 hidden transition-[width] duration-200 lg:block',
          collapsed ? 'w-[76px]' : 'w-64',
        )}
      >
        <SidebarContent collapsed={collapsed} onToggle={toggleCollapsed} />
      </aside>

      {mobileOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-ink-950/60 backdrop-blur-sm animate-fade-in"
            onClick={() => setMobileOpen(false)}
          />
          <div className="relative h-full w-72 shadow-pop animate-fade-in">
            <button
              type="button"
              onClick={() => setMobileOpen(false)}
              className="absolute right-3 top-4 z-10 rounded-lg p-2 text-slate-400 hover:bg-white/10 hover:text-white"
              aria-label="Close menu"
            >
              <X className="h-4 w-4" />
            </button>
            <SidebarContent collapsed={false} onNavigate={() => setMobileOpen(false)} />
          </div>
        </div>
      ) : null}

      <div className={cn('transition-[padding] duration-200', collapsed ? 'lg:pl-[76px]' : 'lg:pl-64')}>
        <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/80 backdrop-blur-lg">
          <div className="flex h-16 items-center gap-3 px-4 sm:px-6 lg:px-8">
            <button
              type="button"
              onClick={() => setMobileOpen(true)}
              className="rounded-lg border border-slate-200 bg-white p-2 text-slate-600 shadow-sm transition hover:bg-slate-50 lg:hidden"
              aria-label="Open menu"
            >
              <Menu className="h-4 w-4" />
            </button>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-slate-500">
                Welcome back, <span className="text-slate-900">{firstName}</span>
              </p>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
