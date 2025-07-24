function Login() {
  const entrar = () => {
    window.location.href = "/clientes"
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
