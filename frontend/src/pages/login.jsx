import { useNavigate } from 'react-router-dom'

function Login() {
  const navigate = useNavigate()

  const entrar = () => {
    navigate('/dashboard')
  }

  return (
    <div className="login-container">
      <h2>OrderSync</h2>
      <input type="text" placeholder="Usuário" />
      <input type="password" placeholder="Senha" />
      <button onClick={entrar}>Entrar</button>
    </div>
  )
}

export default Login
