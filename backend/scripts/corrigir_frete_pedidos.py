import sys
import os

# Adiciona o diretório backend ao PYTHONPATH para importar módulos do app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import SessionLocal
from sqlalchemy import text
from models.pedido import PedidoModel

def run():
    db = SessionLocal()
    try:
        print("Buscando pedidos afetados...")
        
        # Encontra pedidos que estão como 'Com Frete' mas não possuem valor financeiro de frete.
        query = db.query(PedidoModel).filter(
            PedidoModel.usar_valor_com_frete == True,
            (PedidoModel.frete_total == None) | (PedidoModel.frete_total <= 0)
        )
        
        pedidos = query.all()
        print(f"Total de pedidos identificados para correção: {len(pedidos)}")
        
        if len(pedidos) == 0:
            print("Nenhuma correção necessária.")
            return

        print("\nLista de Pedidos Afetados:")
        for p in pedidos:
            print(f"- ID: {p.id} | Cliente: {p.cliente} | Total: R${p.total_pedido} | Criado em: {p.created_at}")

        # Pede confirmação se rodado iterativamente (opcional para logs em prod, mas aqui vamos aplicar e commitar)
        print("\nAplicando correções no banco de dados...")
        count = 0
        for p in pedidos:
            p.usar_valor_com_frete = False
            # Recalcular caso haja alguma divergência (segurança)
            p.total_pedido = p.total_sem_frete
            count += 1
            
        db.commit()
        print(f"Correção concluída com sucesso! {count} pedidos foram atualizados para 'Sem Frete' (Retirada).")

    except Exception as e:
        db.rollback()
        print(f"Ocorreu um erro: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run()
