import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import App from './App';
import Success from './Success';
import Verify from './Verify';
import Playground from './Playground'; // ✅ New playground route
import ApiKeys from './ApiKeys'; // ✅ Added ApiKeys route

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/success" element={<Success />} />
        <Route path="/verify" element={<Verify />} />
        <Route path="/playground" element={<Playground />} /> {/* ✅ Added here */}
        <Route path="/api-keys" element={<ApiKeys />} /> {/* ✅ New route */}
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
