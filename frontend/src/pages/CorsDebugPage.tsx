import React from 'react';
import { CorsDebug } from '../components/CorsDebug';

function CorsDebugPage() {
  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="container mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            🔧 Diagnóstico CORS - Drive+
          </h1>
          <p className="text-gray-600">
            Herramienta para diagnosticar problemas de conectividad con el backend
          </p>
        </div>
        
        <CorsDebug />
        
        <div className="mt-8 text-center">
          <a 
            href="/" 
            className="text-blue-500 hover:text-blue-700 underline"
          >
            ← Volver al inicio
          </a>
        </div>
      </div>
    </div>
  );
}

export default CorsDebugPage;
