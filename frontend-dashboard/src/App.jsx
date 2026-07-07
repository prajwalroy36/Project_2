// src/App.jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Overview from './pages/Overview';
import OrderDetails from './pages/OrderDetails';

export default function App() {
    return (
        <BrowserRouter>
            <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">
                <Routes>
                    <Route path="/" element={<Overview />} />
                    <Route path="/order/:id" element={<OrderDetails />} />
                </Routes>
            </div>
        </BrowserRouter>
    );
}