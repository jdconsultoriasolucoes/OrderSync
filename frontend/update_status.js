const { Client } = require('pg');

const client = new Client({
  connectionString: "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync",
  ssl: { rejectUnauthorized: false }
});

async function run() {
  await client.connect();
  console.log("✅ Connected to Render DB via Node.js");
  
  await client.query("UPDATE public.pedido_status SET ativo = FALSE;");
  
  const novos_status = [
      {codigo: "ORCAMENTO", rotulo: "Orçamento", ordem: 1},
      {codigo: "PEDIDO", rotulo: "Pedido", ordem: 2},
      {codigo: "FATURADO_SUPRA", rotulo: "Faturado Supra", ordem: 3},
      {codigo: "FATURADO_DISPET", rotulo: "Faturado Dispet", ordem: 4},
      {codigo: "CANCELADO", rotulo: "Cancelado", ordem: 5}
  ];
  
  for (const st of novos_status) {
      await client.query(`
          INSERT INTO public.pedido_status (codigo, rotulo, ordem, ativo)
          VALUES ($1, $2, $3, TRUE)
          ON CONFLICT (codigo) DO UPDATE 
          SET rotulo = EXCLUDED.rotulo, 
              ordem = EXCLUDED.ordem, 
              ativo = TRUE;
      `, [st.codigo, st.rotulo, st.ordem]);
  }
  
  console.log("✅ Statuses updated successfully!");
  await client.end();
}

run().catch(err => {
    console.error("❌ Erro:", err);
    client.end();
});
