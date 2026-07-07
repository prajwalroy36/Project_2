// src/pages/Overview.jsx
import { useEffect, useState } from 'react';
import { getOrders } from '../services/api';
import { Link } from 'react-router-dom';

export default function Overview() {
    const [orders, setOrders] = useState([]);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchOrders = () => {
            getOrders()
                .then(setOrders)
                .catch(err => setError("Could not connect to backend. Is Uvicorn running?"));
        };
        
        fetchOrders();
        // Auto-refresh every 15 seconds
        const interval = setInterval(fetchOrders, 15000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="p-8 max-w-6xl mx-auto">
            <h1 className="text-2xl font-bold mb-6">Operations Overview</h1>
            
            {error && <div className="bg-red-100 text-red-800 p-4 rounded mb-4">{error}</div>}

            <div className="bg-white shadow rounded-lg overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-gray-100">
                        <tr>
                            <th className="p-4 border-b">DB ID</th>
                            <th className="p-4 border-b">Shopify Order #</th>
                            <th className="p-4 border-b">Status</th>
                            <th className="p-4 border-b">Retries</th>
                            <th className="p-4 border-b">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {orders.length === 0 && !error ? (
                            <tr><td colSpan="5" className="p-4 text-center text-gray-500">No orders found. Send a test webhook!</td></tr>
                        ) : (
                            orders.map(order => (
                                <tr key={order.db_id} className="hover:bg-gray-50 border-b">
                                    <td className="p-4">{order.db_id}</td>
                                    <td className="p-4 font-medium">{order.order_id}</td>
                                    <td className="p-4">
                                        <span className={`px-2 py-1 rounded text-xs font-bold ${
                                            order.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                                            order.status.includes('FAILED') || order.status.includes('HELD') ? 'bg-red-100 text-red-800' :
                                            'bg-blue-100 text-blue-800'
                                        }`}>
                                            {order.status}
                                        </span>
                                    </td>
                                    <td className="p-4">{order.retry_count}</td>
                                    <td className="p-4">
                                        <Link to={`/order/${order.db_id}`} className="text-blue-600 hover:underline font-semibold">
                                            View Cycle &rarr;
                                        </Link>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}