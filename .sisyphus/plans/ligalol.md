# Plan LIGALOL - Liga Competitiva League of Legends

## Estructura del Proyecto
```
LIGALOL/
├── config/
│   ├── players.json          # Lista de jugadores (Riot ID + Tagline)
│   └── .env.example          # Variables de entorno (API key, etc.)
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   └── riot_api.py       # Cliente para account-v1 y match-v5
│   ├── data/
│   │   ├── __init__.py
│   │   ├── processor.py      # Procesamiento de datos crudos
│   │   └── storage.py        # Almacenamiento CSV histórico
│   ├── challenges/
│   │   ├── __init__.py
│   │   ├── base.py           # Clase base para desafíos
│   │   └── definitions.py    # Definiciones de desafíos predefinidos
│   └── frontend/
│       ├── __init__.py
│       └── app.py            # Aplicación Streamlit
├── data/
│   └── matches_history.csv   # Base de datos histórica
├── requirements.txt
└── README.md
```

## TODOs

### Backend
- [ ] T1: Configuración y Gestión de Jugadores
  - Crear `config/players.json` con estructura para Riot ID + Tagline
  - Crear `config/.env.example` con RIOT_API_KEY, región, etc.
  - Implementar loader de configuración en Python
- [ ] T2: Módulo de API de Riot Games
  - Cliente para account-v1 (resolución de PUUID desde Riot ID)
  - Cliente para match-v5 (obtener IDs de partidas y detalles)
  - Filtrar por queueId 420 (SoloQ) y 440 (FlexQ)
  - Filtrar partidas de últimas 24 horas
  - Manejo de rate limits y errores
- [ ] T3: Procesamiento y Almacenamiento de Datos
  - Extraer métricas crudos: KDA, Daño total, Primera Sangre, Wards, CS, Oro, Duración
  - Almacenar en CSV histórico (`data/matches_history.csv`)
  - Funciones para consultar datos diarios y semanales
- [ ] T4: Sistema Modular de Desafíos y Títulos
  - Clase base `Challenge` con interfaz clara
  - Implementar desafíos de ejemplo (Rey del Farm, Fuente de Oro, Centinela, Fábrica de Daño, Adicto a la Sangre)
  - Motor de evaluación que procese datos y asigne títulos

### Frontend
- [ ] T5: Interfaz Streamlit
  - Tab 1: Resumen Diario (Racha, KDA, MVP, Fedeador)
  - Tab 2: Sala de Trofeos (Desafíos desbloqueados)
  - Tab 3: Histórico Semanal (Tablas acumuladas)

### Documentación
- [ ] T6: README y Guía de Extensión
  - Cómo ejecutar el proyecto
  - Cómo añadir nuevos jugadores
  - Cómo añadir nuevos desafíos/logros

## Final Verification Wave
- [ ] F1: Ejecutar sin errores (`python -m src.frontend.app`)
- [ ] F2: Revisar que los datos crudos se guardan correctamente en CSV
- [ ] F3: Verificar que el sistema de desafíos es extensible
- [ ] F4: Comprobar que Streamlit muestra las 3 pestañas correctamente
