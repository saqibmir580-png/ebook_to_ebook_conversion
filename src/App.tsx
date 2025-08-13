import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import SubscriptionPage from './pages/SubscriptionPage';
import AboutPage from './pages/AboutPage';
import Dashboard from './pages/Dashboard';
import ConversionWorkflow from './pages/ConversionWorkflow';
import { AuthProvider } from './context/AuthContext';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-50 flex flex-col">
          <Navbar />
          <main className="flex-grow">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/subscription" element={<SubscriptionPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/convert" element={<ConversionWorkflow />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;