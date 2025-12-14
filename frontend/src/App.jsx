import { Routes, Route } from 'react-router-dom'
import Login from './pages/Login'
import Cliente from './pages/Cliente'
import Dashboard from './pages/Dashboard'
import Pedidos from './pages/Pedidos'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/pedidos" element={<Pedidos />} />
      <Route path="/cliente" element={<Cliente />} />
    </Routes>
  )
}

export default App
