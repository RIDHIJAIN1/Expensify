import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import Protected from './components/Protected'
import Categories from './pages/Categories'
import Dashboard from './pages/Dashboard'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Transactions from './pages/Transactions'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route
        element={
          <Protected>
            <AppShell />
          </Protected>
        }
      >
        <Route path="/app/dashboard" element={<Dashboard />} />
        <Route path="/app/transactions" element={<Transactions />} />
        <Route path="/app/categories" element={<Categories />} />
      </Route>
      <Route path="/app" element={<Navigate to="/app/dashboard" replace />} />
      <Route path="/app/uploads" element={<Navigate to="/app/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
