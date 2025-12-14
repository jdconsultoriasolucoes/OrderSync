import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function Pedidos() {
    const [pedidos, setPedidos] = useState([])
    const [loading, setLoading] = useState(true)
    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)

    useEffect(() => {
        fetchPedidos()
    }, [page])

    const fetchPedidos = async () => {
        try {
            setLoading(true)
            const res = await fetch(`${API_URL}/api/pedidos?page=${page}&pageSize=10`)
            const data = await res.json()
            setPedidos(data.data)
            setTotalPages(Math.ceil(data.total / 10))
        } catch (error) {
            console.error("Erro ao buscar pedidos:", error)
        } finally {
            setLoading(false)
        }
    }

    const getStatusColor = (status) => {
        switch (status) {
            case 'ABERTO': return '#3b82f6';
            case 'CONFIRMADO': return '#10b981';
            case 'CANCELADO': return '#ef4444';
            default: return '#6b7280';
        }
    }

    return (
        <div className="page-container" style={{ padding: '2rem' }}>
            <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <h1 style={{ fontSize: '2rem', fontWeight: 'bold', color: '#1f2937' }}>Pedidos</h1>
                <Link to="/dashboard" style={{ padding: '0.5rem 1rem', background: '#333', color: 'white', borderRadius: '6px', textDecoration: 'none' }}>
                    Voltar
                </Link>
            </header>

            <div style={{ background: 'white', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)', overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead style={{ background: '#f9fafb' }}>
                        <tr>
                            <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600', color: '#4b5563' }}>ID</th>
                            <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600', color: '#4b5563' }}>Cliente</th>
                            <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600', color: '#4b5563' }}>Data</th>
                            <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600', color: '#4b5563' }}>Total</th>
                            <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600', color: '#4b5563' }}>Status</th>
                            <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600', color: '#4b5563' }}>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan="6" style={{ padding: '2rem', textAlign: 'center' }}>Carregando...</td></tr>
                        ) : pedidos.length === 0 ? (
                            <tr><td colSpan="6" style={{ padding: '2rem', textAlign: 'center' }}>Nenhum pedido encontrado.</td></tr>
                        ) : (
                            pedidos.map((p) => (
                                <tr key={p.numero_pedido} style={{ borderTop: '1px solid #e5e7eb' }}>
                                    <td style={{ padding: '1rem' }}>#{p.numero_pedido}</td>
                                    <td style={{ padding: '1rem' }}>
                                        <div style={{ fontWeight: '500' }}>{p.cliente_nome}</div>
                                        <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>{p.cliente_codigo}</div>
                                    </td>
                                    <td style={{ padding: '1rem' }}>{new Date(p.data_pedido).toLocaleDateString()}</td>
                                    <td style={{ padding: '1rem', fontWeight: '600' }}>R$ {p.valor_total.toFixed(2)}</td>
                                    <td style={{ padding: '1rem' }}>
                                        <span style={{
                                            padding: '0.25rem 0.75rem',
                                            borderRadius: '9999px',
                                            fontSize: '0.85rem',
                                            fontWeight: '500',
                                            background: getStatusColor(p.status_codigo) + '20', // Opacity 20%
                                            color: getStatusColor(p.status_codigo)
                                        }}>
                                            {p.status_codigo}
                                        </span>
                                    </td>
                                    <td style={{ padding: '1rem' }}>
                                        <button style={{ color: '#3b82f6', background: 'none', border: 'none', cursor: 'pointer', fontWeight: '500' }}>Ver Detalhes</button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'center', gap: '1rem' }}>
                <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    style={{ padding: '0.5rem 1rem', border: '1px solid #d1d5db', background: 'white', borderRadius: '6px', cursor: page === 1 ? 'not-allowed' : 'pointer' }}
                >
                    Anterior
                </button>
                <span style={{ display: 'flex', alignItems: 'center' }}>Página {page} de {totalPages}</span>
                <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    style={{ padding: '0.5rem 1rem', border: '1px solid #d1d5db', background: 'white', borderRadius: '6px', cursor: page === totalPages ? 'not-allowed' : 'pointer' }}
                >
                    Próxima
                </button>
            </div>
        </div>
    )
}

export default Pedidos
