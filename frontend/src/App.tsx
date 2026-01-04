import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "./contexts/ThemeContext";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";
import { Threats } from "./pages/Threats";
import { AIChat } from "./pages/AIChat";
import { Analytics } from "./pages/Analytics";
import { Streams } from "./pages/Streams";
import { Alerts } from "./pages/Alerts";
import { Settings } from "./pages/Settings";

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="guardian-theme">
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="threats" element={<Threats />} />
            <Route path="ai-chat" element={<AIChat />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="streams" element={<Streams />} />
            <Route path="alerts" element={<Alerts />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
