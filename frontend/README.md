# dbt-conceptual UI

This directory contains the React frontend for the dbt-conceptual interactive web UI.

## Development

### Prerequisites
- Node.js 18+ and npm

### Setup

```bash
cd frontend
npm install
```

### Development Server

Run the frontend dev server with hot reload:

```bash
npm run dev
```

This starts Vite on `http://localhost:5173` with API proxy to `http://localhost:5000`.

In another terminal, start the Flask backend:

```bash
cd ..
pip install -e ".[serve]"
dbt-conceptual serve
```

### Build for Production

Build the frontend to `../src/dbt_conceptual/static/`:

```bash
npm run build
```

The built files are served by the Flask server when running `dbt-conceptual serve`.

## Architecture

- **React** — UI framework
- **TypeScript** — Type safety
- **D3.js** — Force-directed graph visualization
- **Vite** — Build tool and dev server

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── GraphEditor.tsx     # Main graph visualization + editing
│   │   ├── CoverageView.tsx    # Coverage report iframe
│   │   └── BusMatrixView.tsx   # Bus matrix iframe
│   ├── App.tsx                  # Main app with tabs
│   ├── types.ts                 # TypeScript types
│   └── main.tsx                 # Entry point
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## API Endpoints

The frontend communicates with these Flask API endpoints:

- `GET /api/state` - Get current conceptual model state
- `POST /api/state` - Save changes to conceptual.yml
- `GET /api/coverage` - Get coverage report HTML
- `GET /api/bus-matrix` - Get bus matrix HTML
