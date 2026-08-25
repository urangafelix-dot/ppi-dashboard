# PPI Portfolio Live Dashboard

Tablero de monitoreo en vivo de tu cartera en **Portfolio Personal Inversiones (PPI)**.

Muestra:
- Saldos disponibles por moneda y plazo
- Posiciones actuales + valuación
- Órdenes activas
- Últimos movimientos
- Auto-refresh configurable

---

## 1. Correr en local (recomendado para probar)

### Requisitos
- Python 3.10+
- Tus API keys de PPI

### Pasos

```bash
# 1. Clonar o copiar la carpeta
cd ppi-dashboard

# 2. Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar keys
cp .env.example .env
# Editá .env y poné tus keys reales:
# PPI_PUBLIC_KEY=...
# PPI_PRIVATE_KEY=...
# PPI_SANDBOX=false   (o true si querés probar en sandbox)

# 5. Correr el dashboard
streamlit run app.py
```

Se abre automáticamente en http://localhost:8501

---

## 2. Deploy gratis en Streamlit Community Cloud (acceso desde cualquier lado)

Esto es lo que te permite **acceder todos los días desde el celular o cualquier PC** sin dejar nada corriendo en tu máquina.

### Pasos (5-10 minutos)

1. **Creá un repositorio público o privado en GitHub**
   - Subí todos los archivos de esta carpeta (`app.py`, `ppi_wrapper.py`, `requirements.txt`, etc.)
   - **Importante**: NO subas el archivo `.env` (ya está en .gitignore implícito)

2. Andá a [https://share.streamlit.io](https://share.streamlit.io) e iniciá sesión con tu cuenta de GitHub.

3. Click en **"New app"**
   - Repository: el que acabás de crear
   - Branch: `main` (o la que uses)
   - Main file path: `app.py`
   - Click **Deploy**

4. **Configurar las Secrets (muy importante)**
   - En la app deployada andá a ⚙️ Settings → Secrets
   - Pegá exactamente esto (reemplazando con tus keys reales):

```toml
PPI_PUBLIC_KEY = "tu_key_publica_aca"
PPI_PRIVATE_KEY = "tu_key_privada_aca"
PPI_SANDBOX = "false"
```

5. Guardá y esperá que se reinicie la app.

¡Listo! Te queda un link tipo `https://tu-app.streamlit.app` que podés abrir todos los días desde cualquier dispositivo.

---

## Seguridad

- Nunca compartas tus keys ni las subas a GitHub.
- El dashboard es **solo lectura** (no puede comprar ni vender).
- Si usás Streamlit Cloud, las secrets están encriptadas.

---

## Próximos pasos (cuando quieras)

- Agregar más gráficos de evolución
- Integrar el agente de Cash Sweeper
- Alertas por Telegram
- Modo dark / personalización

Cualquier duda o mejora, avisame.
