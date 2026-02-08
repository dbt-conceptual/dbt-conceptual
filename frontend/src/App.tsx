import { Canvas } from './components/Canvas';
import { PropertyPanel } from './components/PropertyPanel';
import { Toolbar } from './components/Toolbar';
import { MessagesPanel } from './components/MessagesPanel';
import { ErrorBoundary } from './components/ErrorBoundary';
import './tokens.css';

function App() {
  return (
    <div className="app-root">
      <Toolbar />
      <div className="app-main">
        <MessagesPanel />
        <ErrorBoundary>
          <Canvas />
        </ErrorBoundary>
        <ErrorBoundary>
          <PropertyPanel />
        </ErrorBoundary>
      </div>
    </div>
  );
}

export default App;
