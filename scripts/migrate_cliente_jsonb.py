"""
Script de migração: converte colunas escalares de clientes para JSONB.
Execute uma única vez no banco de dados do Render.

Uso:
  cd backend
  python ../scripts/migrate_cliente_jsonb.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

print("Conectando ao banco...")
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = False
cur = conn.cursor()

try:
    print("Iniciando migração JSONB...")


    # ─── 1. Indica\u00e7\u00e3o do Cliente ───────────────────────────────────
    # Converte a coluna String existente → JSONB (array de strings)
    cur.execute("""
        ALTER TABLE t_cadastro_cliente_v2
        ADD COLUMN IF NOT EXISTS cadastro_indicacao_cliente_new JSONB DEFAULT '[]'::jsonb;
    """)
    cur.execute("""
        UPDATE t_cadastro_cliente_v2
        SET cadastro_indicacao_cliente_new =
            CASE
                WHEN cadastro_indicacao_cliente IS NOT NULL AND cadastro_indicacao_cliente != ''
                THEN jsonb_build_array(cadastro_indicacao_cliente)
                ELSE '[]'::jsonb
            END;
    """)
    cur.execute("""
        ALTER TABLE t_cadastro_cliente_v2
        DROP COLUMN IF EXISTS cadastro_indicacao_cliente;
    """)
    cur.execute("""
        ALTER TABLE t_cadastro_cliente_v2
        RENAME COLUMN cadastro_indicacao_cliente_new TO cadastro_indicacao_cliente;
    """)
    print("  ✓ cadastro_indicacao_cliente → JSONB[]")


    # ─── 2. Grupos Econômicos ─────────────────────────────────────
    cur.execute("""
        ALTER TABLE t_cadastro_cliente_v2
        ADD COLUMN IF NOT EXISTS grupos_economicos JSONB DEFAULT '[]'::jsonb;
    """)
    cur.execute("""
        UPDATE t_cadastro_cliente_v2
        SET grupos_economicos = CASE
            WHEN grupo_economico_codigo IS NOT NULL OR grupo_economico_nome IS NOT NULL THEN
                jsonb_build_array(
                    jsonb_build_object(
                        'codigo', COALESCE(grupo_economico_codigo, ''),
                        'nome',   COALESCE(grupo_economico_nome,   '')
                    )
                )
            ELSE '[]'::jsonb
        END;
    """)
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS grupo_economico_codigo;")
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS grupo_economico_nome;")
    print("  ✓ grupo_economico → grupos_economicos JSONB[]")


    # ─── 3. Referências Comerciais ────────────────────────────────
    cur.execute("""
        ALTER TABLE t_cadastro_cliente_v2
        ADD COLUMN IF NOT EXISTS referencias_comerciais JSONB DEFAULT '[]'::jsonb;
    """)
    cur.execute("""
        UPDATE t_cadastro_cliente_v2
        SET referencias_comerciais = CASE
            WHEN ref_comercial_empresa IS NOT NULL OR ref_comercial_cidade IS NOT NULL
              OR ref_comercial_telefone IS NOT NULL OR ref_comercial_contato IS NOT NULL THEN
                jsonb_build_array(
                    jsonb_build_object(
                        'empresa',  COALESCE(ref_comercial_empresa,  ''),
                        'cidade',   COALESCE(ref_comercial_cidade,   ''),
                        'telefone', COALESCE(ref_comercial_telefone, ''),
                        'contato',  COALESCE(ref_comercial_contato,  '')
                    )
                )
            ELSE '[]'::jsonb
        END;
    """)
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS ref_comercial_empresa;")
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS ref_comercial_cidade;")
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS ref_comercial_telefone;")
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS ref_comercial_contato;")
    print("  ✓ ref_comercial_* → referencias_comerciais JSONB[]")


    # ─── 4. Referências Bancárias ─────────────────────────────────
    cur.execute("""
        ALTER TABLE t_cadastro_cliente_v2
        ADD COLUMN IF NOT EXISTS referencias_bancarias JSONB DEFAULT '[]'::jsonb;
    """)
    cur.execute("""
        UPDATE t_cadastro_cliente_v2
        SET referencias_bancarias = CASE
            WHEN ref_bancaria_banco IS NOT NULL OR ref_bancaria_agencia IS NOT NULL
              OR ref_bancaria_conta IS NOT NULL THEN
                jsonb_build_array(
                    jsonb_build_object(
                        'banco',          COALESCE(ref_bancaria_banco,   ''),
                        'agencia',        COALESCE(ref_bancaria_agencia, ''),
                        'conta_corrente', COALESCE(ref_bancaria_conta,   '')
                    )
                )
            ELSE '[]'::jsonb
        END;
    """)
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS ref_bancaria_banco;")
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS ref_bancaria_agencia;")
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS ref_bancaria_conta;")
    print("  ✓ ref_bancaria_* → referencias_bancarias JSONB[]")


    # ─── 5. Bens Imóveis ─────────────────────────────────────────
    cur.execute("""
        ALTER TABLE t_cadastro_cliente_v2
        ADD COLUMN IF NOT EXISTS bens_imoveis JSONB DEFAULT '[]'::jsonb;
    """)
    cur.execute("""
        UPDATE t_cadastro_cliente_v2
        SET bens_imoveis = CASE
            WHEN bem_imovel_imovel IS NOT NULL OR bem_imovel_localizacao IS NOT NULL
              OR bem_imovel_area IS NOT NULL OR bem_imovel_valor IS NOT NULL
              OR bem_imovel_hipotecado IS NOT NULL THEN
                jsonb_build_array(
                    jsonb_build_object(
                        'imovel',      COALESCE(bem_imovel_imovel,      ''),
                        'localizacao', COALESCE(bem_imovel_localizacao,  ''),
                        'area',        COALESCE(bem_imovel_area,         ''),
                        'valor',       COALESCE(bem_imovel_valor,        0),
                        'hipotecado',  COALESCE(bem_imovel_hipotecado,   '')
                    )
                )
            ELSE '[]'::jsonb
        END;
    """)
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS bem_imovel_imovel;")
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS bem_imovel_localizacao;")
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS bem_imovel_area;")
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS bem_imovel_valor;")
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS bem_imovel_hipotecado;")
    print("  ✓ bem_imovel_* → bens_imoveis JSONB[]")


    # ─── 6. Bens Móveis ──────────────────────────────────────────
    cur.execute("""
        ALTER TABLE t_cadastro_cliente_v2
        ADD COLUMN IF NOT EXISTS bens_moveis JSONB DEFAULT '[]'::jsonb;
    """)
    cur.execute("""
        UPDATE t_cadastro_cliente_v2
        SET bens_moveis = CASE
            WHEN bem_movel_marca IS NOT NULL OR bem_movel_modelo IS NOT NULL
              OR bem_movel_alienado IS NOT NULL THEN
                jsonb_build_array(
                    jsonb_build_object(
                        'marca',    COALESCE(bem_movel_marca,    ''),
                        'modelo',   COALESCE(bem_movel_modelo,   ''),
                        'alienado', COALESCE(bem_movel_alienado, '')
                    )
                )
            ELSE '[]'::jsonb
        END;
    """)
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS bem_movel_marca;")
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS bem_movel_modelo;")
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS bem_movel_alienado;")
    print("  ✓ bem_movel_* → bens_moveis JSONB[]")


    # ─── 7. Plantel de Animais ────────────────────────────────────
    cur.execute("""
        ALTER TABLE t_cadastro_cliente_v2
        ADD COLUMN IF NOT EXISTS planteis_animais JSONB DEFAULT '[]'::jsonb;
    """)
    cur.execute("""
        UPDATE t_cadastro_cliente_v2
        SET planteis_animais = CASE
            WHEN animal_especie IS NOT NULL OR animal_numero IS NOT NULL
              OR animal_consumo_diario IS NOT NULL OR animal_consumo_mensal IS NOT NULL THEN
                jsonb_build_array(
                    jsonb_build_object(
                        'especie',          COALESCE(animal_especie,          ''),
                        'numero_de_animais',COALESCE(animal_numero,            0),
                        'consumo_diario',   COALESCE(animal_consumo_diario,   0.0),
                        'consumo_mensal',   COALESCE(animal_consumo_mensal,   0.0)
                    )
                )
            ELSE '[]'::jsonb
        END;
    """)
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS animal_especie;")
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS animal_numero;")
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS animal_consumo_diario;")
    cur.execute("ALTER TABLE t_cadastro_cliente_v2 DROP COLUMN IF EXISTS animal_consumo_mensal;")
    print("  ✓ animal_* → planteis_animais JSONB[]")


    conn.commit()
    print("\n✅ Migração concluída com sucesso!")

except Exception as e:
    conn.rollback()
    print(f"\n❌ Erro na migração: {e}")
    raise

finally:
    cur.close()
    conn.close()
