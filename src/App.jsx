import DeploymentForm from './components/DeploymentForm';
import './App.css';

function App() {
  return (
    <div className="app-container">
      <header className="app-header">
        <h1>PaaS Control Panel</h1>
      </header>
      <main>
        <DeploymentForm />
      </main>
    </div>
  );
}

export default App;