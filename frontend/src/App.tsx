import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import PrivateRoute from './components/PrivateRoute';
import ErrorBoundary from './components/ErrorBoundary';
import { AuthProvider } from './context/AuthContext';
import { SalasProvider } from './context/SalasContext';
import { TorneosProvider } from './context/TorneosContext';
import { PWAInstallBanner } from './components/PWAInstallBanner';
import { PWAUpdateBanner } from './components/PWAUpdateBanner';

// Páginas críticas (carga inmediata)
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import { CorsDebugPage } from './pages/CorsDebugPage';

// Lazy loading para páginas secundarias
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Salas = lazy(() => import('./pages/Salas'));
const Torneos = lazy(() => import('./pages/Torneos'));
const TorneoDetalle = lazy(() => import('./pages/TorneoDetalle'));
const MisTorneos = lazy(() => import('./pages/MisTorneos'));
const Estadisticas = lazy(() => import('./pages/Estadisticas'));
const Rankings = lazy(() => import('./pages/Rankings'));
const RankingsCategorias = lazy(() => import('./pages/RankingsCategorias'));
const Confirmaciones = lazy(() => import('./pages/Confirmaciones'));
const MiPerfil = lazy(() => import('./pages/MiPerfil'));
const EditarPerfil = lazy(() => import('./pages/EditarPerfil'));
const MiRanking = lazy(() => import('./pages/MiRanking'));
const CompletarPerfil = lazy(() => import('./pages/CompletarPerfil'));
const PerfilPublico = lazy(() => import('./pages/PerfilPublico'));
const BuscarJugadores = lazy(() => import('./pages/BuscarJugadores'));
const AdminPanel = lazy(() => import('./pages/AdminPanel'));
const DebugAuth = lazy(() => import('./pages/DebugAuth'));

// Loading component
const PageLoader = () => (
  <div className="min-h-screen bg-background flex items-center justify-center">
    <div className="text-center">
      <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
      <p className="text-textSecondary">Cargando...</p>
    </div>
  </div>
);

// La Landing siempre es accesible, incluso si estás autenticado
// El usuario decide cuándo entrar a la app

function App() {
  // Configuración para drive-plus.com.ar
  const basename = import.meta.env.PROD ? '/' : '/';
  
  return (
    <ErrorBoundary>
      <Router basename={basename}>
        <AuthProvider>
          <SalasProvider>
            <TorneosProvider>
              <Suspense fallback={<PageLoader />}>
                <Routes>
              {/* Ruta principal - Landing siempre visible */}
              <Route path="/" element={<Landing />} />

              {/* Rutas públicas */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/cors-debug" element={<CorsDebugPage />} />
              <Route path="/debug-auth" element={<DebugAuth />} />
              
              {/* Ruta semi-protegida: requiere Firebase auth pero no usuario completo */}
              <Route
                path="/completar-perfil"
                element={
                  <PrivateRoute>
                    <CompletarPerfil />
                  </PrivateRoute>
                }
              />

              {/* Rutas protegidas */}
              <Route
                path="/dashboard"
                element={
                  <PrivateRoute>
                    <Layout>
                      <Dashboard />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/salas"
                element={
                  <PrivateRoute>
                    <Layout>
                      <Salas />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/torneos"
                element={
                  <PrivateRoute>
                    <Layout>
                      <Torneos />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/torneos/mis-torneos"
                element={
                  <PrivateRoute>
                    <Layout>
                      <MisTorneos />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/torneos/:id"
                element={
                  <PrivateRoute>
                    <Layout>
                      <TorneoDetalle />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/estadisticas"
                element={
                  <PrivateRoute>
                    <Layout>
                      <Estadisticas />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/rankings"
                element={
                  <PrivateRoute>
                    <Layout>
                      <Rankings />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/rankings/categorias"
                element={
                  <PrivateRoute>
                    <Layout>
                      <RankingsCategorias />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/rankings/mi-ranking"
                element={
                  <PrivateRoute>
                    <Layout>
                      <MiRanking />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/salas/programados"
                element={
                  <PrivateRoute>
                    <Layout>
                      <div className="text-textPrimary">Partidos Programados - Próximamente</div>
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/salas/confirmaciones"
                element={
                  <PrivateRoute>
                    <Layout>
                      <Confirmaciones />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/perfil"
                element={
                  <PrivateRoute>
                    <Layout>
                      <MiPerfil />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/perfil/editar"
                element={
                  <PrivateRoute>
                    <Layout>
                      <EditarPerfil />
                    </Layout>
                  </PrivateRoute>
                }
              />
              {/* Perfil público por ID */}
              <Route
                path="/perfil/:id"
                element={
                  <PrivateRoute>
                    <Layout>
                      <PerfilPublico />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/configuracion"
                element={
                  <PrivateRoute>
                    <Layout>
                      <div className="text-textPrimary">Configuración - Próximamente</div>
                    </Layout>
                  </PrivateRoute>
                }
              />
              {/* Búsqueda de jugadores */}
              <Route
                path="/jugadores"
                element={
                  <PrivateRoute>
                    <Layout>
                      <BuscarJugadores />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Panel de Administración - Solo para administradores */}
              <Route
                path="/admin"
                element={
                  <PrivateRoute>
                    <Layout>
                      <AdminPanel />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Perfil público de otros usuarios - URL amigable por username */}
              <Route
                path="/jugador/:username"
                element={
                  <PrivateRoute>
                    <Layout>
                      <PerfilPublico />
                    </Layout>
                  </PrivateRoute>
                }
              />

              {/* Ruta 404 */}
              <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Suspense>
              
              {/* PWA Install Banner */}
              <PWAUpdateBanner />
              <PWAInstallBanner />
          </TorneosProvider>
        </SalasProvider>
      </AuthProvider>
    </Router>
    </ErrorBoundary>
  );
}

export default App;
