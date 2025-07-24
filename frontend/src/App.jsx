import { Routes, Route } from 'react-router-dom'
import Login from './pages/Login'
import Cliente from './pages/Cliente'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route path="/cliente" element={<Cliente />} />
    </Routes>
  )
}

export default App
