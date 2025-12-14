import React from 'react'
import { Link } from 'react-router-dom'

function Dashboard() {
    return (
        <>
            <header>
                <div className="navbar">
                    <button className="menu-btn" id="menu-button">&#9776;</button>
                    <img src="/logo.png" alt="Logo" className="logo" />
                </div>
            </header>

            <main className="cards-container">
                <div className="cards-grid">
                    <Link to="/cliente" className="card card-cliente">
                        <span className="card-text">Cadastrar Cliente</span>
                        <img src="/icons/cliente.png" alt="Ícone Cliente" />
                    </Link>

                    <section className="card card-catalogo">
                        <span className="card-text">Atualizar Catálogo</span>
                        <img src="/icons/catalogo.png" alt="Ícone Catálogo" />
                    </section>

                    <Link to="/pedidos" className="card card-pedido">
                        <span className="card-text">Consultar Pedidos</span>
                        <img src="/icons/pedido.png" alt="Ícone Pedido" />
                    </Link>

                    <section className="card card-relatorios">
                        <span className="card-text">Exportar Relatórios</span>
                        <img src="/icons/relatorio.png" alt="Ícone Relatório" />
                    </section>

                    <section className="card card-precos">
                        <a href="/tabela_preco/criacao_tabela_preco.html" className="card card-precos">
                            <span className="card-text">Tabela de Preço</span>
                            <img src="/icons/price-tag.png" alt="Ícone Preço" />
                        </a>
                    </section>

                    <section className="card card-config_email">
                        <a href="https://ordersync-backend-59d2.onrender.com/static/config_email/config_email.html" className="card card-config_email">
                            <span className="card-text">Configuração email</span>
                            <img src="/icons/price-tag.png" alt="Ícone config_email" />
                        </a>
                    </section>

                    <section className="card card-produto">
                        <a href="/produto/produto.html" className="card card-produto">
                            <span className="card-text">Cadastrar Produto</span>
                            <img src="/icons/price-tag.png" alt="Ícone Produto" />
                        </a>
                    </section>
                </div>
            </main>
        </>
    )
}

export default Dashboard
