import { Canvas } from './components/Canvas';
import { PropertyPanel } from './components/PropertyPanel';
import './tokens.css';

function App() {
  return (
    <div style={{ display: 'flex', width: '100vw', height: '100vh' }}>
      <Canvas />
      <PropertyPanel />
    </div>
  );
}

export default App;
