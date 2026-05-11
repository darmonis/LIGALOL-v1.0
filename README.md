# 🏆 LIGALOL - Liga Competitiva de League of Legends

Sistema automatizado para extraer estadísticas de la API de Riot Games y generar rankings, desafíos y trofeos para un grupo de amigos.

---

## 📁 Estructura del Proyecto

```
LIGALOL/
├── config/
│   ├── players.json          # Lista de jugadores (Riot ID + Tagline)
│   └── .env                  # Variables de entorno (API key, etc.)
├── src/
│   ├── config_loader.py      # Carga configuración y jugadores
│   ├── api/
│   │   └── riot_api.py       # Cliente para account-v1 y match-v5
│   ├── data/
│   │   ├── processor.py      # Extrae métricas de partidas
│   │   └── storage.py        # Almacena en CSV histórico
│   ├── challenges/
│   │   ├── base.py           # Clase base para desafíos
│   │   ├── definitions.py    # Desafíos predefinidos
│   │   └── engine.py         # Motor de evaluación
│   └── frontend/
│       └── app.py            # Interfaz Streamlit
├── data/
│   └── matches_history.csv   # Base de datos histórica (auto-generado)
├── requirements.txt
└── README.md
```

---

## 🚀 Cómo empezar

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Copia el archivo de ejemplo y rellena tu API key:

```bash
cp config/.env.example config/.env
```

Edita `config/.env`:

```env
RIOT_API_KEY=tu_api_key_aqui
REGION=europe
DEFAULT_TAGLINE=EUW
```

> 🔑 Obtén tu API key gratuita en: https://developer.riotgames.com/

### 3. Configurar jugadores

Edita `config/players.json`:

```json
[
  {
    "game_name": "TuRiotID",
    "tag_line": "EUW"
  },
  {
    "game_name": "Amigo1",
    "tag_line": "EUW"
  }
]
```

Puedes añadir de 5 a 8 jugadores (o más) simplemente añadiendo objetos a esta lista.

### 4. Ejecutar la aplicación

```bash
streamlit run src/frontend/app.py
```

La interfaz se abrirá en tu navegador.

---

## 🎮 Funcionalidades

### Extracción de datos
- Conecta con **account-v1** para resolver PUUID desde Riot ID
- Consulta **match-v5** para obtener partidas de las últimas 24h
- Filtra automáticamente **SoloQ (queueId 420)** y **FlexQ (queueId 440)**
- Extrae métricas crudos: KDA, Daño, Primera Sangre, Wards, CS, Oro, Duración

### Almacenamiento histórico
- Guarda todos los datos en `data/matches_history.csv`
- Evita duplicados automáticamente (upsert por puuid + match_id)
- Permite análisis histórico diario y semanal

### Desafíos y Títulos

**Diarios:**
- 🌾 **Rey del Farm**: Mayor CS/min en una partida
- 💀 **La Fuente de Oro**: Más muertes (¡irónico!)
- 👁️ **El Centinela**: Mayor visión
- ⭐ **MVP del Día**: Mejor KDA
- 💩 **Fedeador del Día**: Peor KDA

**Semanales:**
- ⚔️ **Fábrica de Daño**: +80k daño en últimas 5 partidas
- 🩸 **Adicto a la Sangre**: Mayor % de primeras sangres

### Interfaz Streamlit
- **Tab 1 - Resumen Diario**: Racha, KDA, MVP y Fedeador del día
- **Tab 2 - Sala de Trofeos**: Desafíos desbloqueados
- **Tab 3 - Histórico Semanal**: Tablas acumuladas con gráficos

---

## 🛠️ Cómo añadir un nuevo desafío/logro

El sistema está diseñado para ser **100% modular**. Añadir un nuevo título es muy sencillo:

### Paso 1: Crear la clase del desafío

Abre `src/challenges/definitions.py` y añade una nueva clase que herede de `Challenge`:

```python
class MiNuevoDesafio(Challenge):
    def __init__(self):
        super().__init__(
            name="Nombre del Desafío",
            description="Descripción de qué mide",
            category="daily",  # o "weekly"
        )

    def evaluate(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        if df.empty:
            return []
        
        # Tu lógica aquí
        # Ejemplo: encontrar el jugador con más kills
        best = df.groupby("game_name")["kills"].sum().reset_index()
        overall_max = best["kills"].max()
        winners = best[best["kills"] == overall_max]
        
        results = []
        for _, row in winners.iterrows():
            results.append(self._build_result(
                player=row["game_name"],
                value=int(row["kills"]),
                achieved=True,
            ))
        return results
```

### Paso 2: Registrar el desafío

Abre `src/challenges/engine.py` y añade tu clase a `get_all_challenges()`:

```python
from src.challenges.definitions import (
    # ... otras importaciones ...
    MiNuevoDesafio,
)

def get_all_challenges() -> list[Challenge]:
    return [
        # ... desafíos existentes ...
        MiNuevoDesafio(),
    ]
```

### ¡Listo!

El desafío aparecerá automáticamente en la interfaz de Streamlit. **No necesitas tocar nada más**.

### Guía rápida de métricas disponibles

Las columnas del DataFrame que recibes en `evaluate()` son:

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `game_name` | str | Nombre del jugador |
| `kills` | int | Asesinatos |
| `deaths` | int | Muertes |
| `assists` | int | Asistencias |
| `kda` | float | Ratio KDA |
| `total_damage` | int | Daño a campeones |
| `first_blood` | bool | ¿Consiguió primera sangre? |
| `wards_placed` | int | Wards colocados |
| `wards_killed` | int | Wards destruidos |
| `vision_score` | int | Puntuación de visión |
| `cs` | int | CS total |
| `cs_per_min` | float | CS por minuto |
| `gold_earned` | int | Oro ganado |
| `game_duration` | int | Duración en segundos |
| `win` | bool | ¿Victoria? |

Usa `df.groupby("game_name")` para agregar por jugador, o filtra directamente el DataFrame.

---

## ⚙️ Configuración avanzada

### Cambiar el rango de horas de búsqueda

Por defecto se buscan partidas de las últimas 24h. Para cambiarlo, modifica el parámetro `hours` en `src/frontend/app.py`:

```python
matches = fetch_player_matches(player, hours=48)  # Últimas 48h
```

### Cambiar de región

Si tus amigos juegan en otra región, edita `src/api/riot_api.py`:

```python
# Para América (LAN, LAS, BR, NA)
ACCOUNT_API_URL = "https://americas.api.riotgames.com/riot/account/v1"
MATCH_API_URL = "https://americas.api.riotgames.com/lol/match/v5"
```

Regiones disponibles: `americas`, `europe`, `asia`, `sea`.

---

## 📝 Notas

- La API de Riot tiene límites de rate. El cliente implementa retries automáticos con espera.
- El CSV histórico crece indefinidamente, lo que permite análisis a largo plazo.
- Los PUUID se resuelven en cada ejecución, por lo que los jugadores pueden cambiar de nombre sin problemas.

---

## 🏗️ Tecnologías

- Python 3.10+
- `requests` - Cliente HTTP
- `pandas` - Manipulación de datos
- `streamlit` - Interfaz visual
- `python-dotenv` - Variables de entorno

---

## ☁️ Despliegue en Streamlit Community Cloud (Gratis)

La forma más sencilla de tener la app online 24/7.

### 1. Subir a GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/ligalol.git
git push -u origin main
```

> ⚠️ **Importante**: No subas tu API key. El archivo `.gitignore` ya protege `config/.env` y `data/matches_history.csv`.

### 2. Desplegar en Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Haz clic en **"New app"**
3. Selecciona tu repositorio `ligalol`
4. En **Main file path** escribe: `streamlit_app.py`
5. Haz clic en **Deploy**

### 3. Configurar Secrets

Una vez desplegada, ve a **Settings → Secrets** y añade:

```toml
RIOT_API_KEY = "RGAPI-tu-api-key-aqui"
REGION = "europe"
DEFAULT_TAGLINE = "EUW"
```

> 🔑 Obtén tu API key gratuita en: https://developer.riotgames.com/

### 4. Configurar jugadores

Edita `config/players.json` directamente en GitHub (o localmente y haz push) con los Riot IDs reales:

```json
[
  {
    "game_name": "YasuoMain",
    "tag_line": "EUW"
  },
  {
    "game_name": "JungleDiff",
    "tag_line": "1234"
  }
]
```

La app se reiniciará automáticamente con cada cambio en el repo.

---

## ☁️ Alternativas de hosting gratuitas

| Plataforma | Ventajas | Limitaciones |
|---|---|---|
| **Streamlit Cloud** | Nativo para Streamlit, muy fácil | Repo público, duerme tras inactividad |
| **Render** | Repo privado permitido | Duerme tras 15 min, tarda en despertar |
| **Hugging Face Spaces** | Buena CPU, ideal para demos | Orientado a ML/AI |
| **Railway** | Siempre activo (con crédito) | $5/mes de crédito gratis |

Para **Render**, usa el siguiente comando de inicio:
```bash
streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0
```
