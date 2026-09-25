import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { useState, useEffect } from "react";
import ProtectedRoute from "@/components/ProtectedRoute";
import Login from "./pages/Login";
import SearchPage from "./pages/SearchPage";
import LoadingPage from "./pages/LoadingPage";
import ResultsPage from "./pages/ResultsPage";
import GeneratePaperPage from "./pages/GeneratePaperPage";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => {
  const [darkMode, setDarkMode] = useState(true);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  const toggleDark = () => setDarkMode((d) => !d);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Login />} />
            <Route
              path="/search"
              element={
                <ProtectedRoute>
                  <SearchPage darkMode={darkMode} onToggleDark={toggleDark} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/loading"
              element={
                <ProtectedRoute>
                  <LoadingPage darkMode={darkMode} onToggleDark={toggleDark} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/results"
              element={
                <ProtectedRoute>
                  <ResultsPage darkMode={darkMode} onToggleDark={toggleDark} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/generate-paper"
              element={
                <ProtectedRoute>
                  <GeneratePaperPage darkMode={darkMode} onToggleDark={toggleDark} />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;