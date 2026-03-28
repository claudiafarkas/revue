import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { RevueProvider } from './context/RevueContext';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <RevueProvider>
        <App />
      </RevueProvider>
    </BrowserRouter>
  </React.StrictMode>,
);