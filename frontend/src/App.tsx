import { Canvas } from './components/Canvas';
import { PropertyPanel } from './components/PropertyPanel';
import { Toolbar } from './components/Toolbar';
import { MessagesPanel } from './components/MessagesPanel';
import { ErrorBoundary } from './components/ErrorBoundary';
import './tokens.css';

function App() {
  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      <Toolbar />
      <div style={{ display: 'flex', height: '100%', paddingTop: '48px' }}>
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
