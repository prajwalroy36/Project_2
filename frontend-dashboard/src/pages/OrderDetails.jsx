// src/pages/OrderDetails.jsx
import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getOrderDetails } from '../services/api';

export default function OrderDetails() {
    const { id } = useParams();
    const [order, setOrder] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        getOrderDetails(id)
            .then(setOrder)
            .catch(err => setError("Failed to load order details."));
    }, [id]);

    if (error) return <div className="p-8 text-center text-red-600">{error}</div>;
    if (!order) return <div className="p-8 text-center">Loading Order {id}...</div>;

    return (
        <div className="p-8 max-w-4xl mx-auto">
            <Link to="/" className="text-blue-600 hover:underline mb-4 inline-block">&larr; Back to Overview</Link>
            
            <h1 className="text-2xl font-bold mb-4">Order Cycle: {order.order_id}</h1>
            
            <div className="grid grid-cols-2 gap-6 mb-6">
                <div className="bg-white p-6 shadow rounded-lg border">
                    <h2 className="text-sm text-gray-500 uppercase tracking-wider mb-2">Current Status</h2>
                    <p className="text-xl font-bold">{order.status}</p>
                    <p className="text-sm text-gray-500 mt-2">Retries: {order.retry_count}</p>
                </div>

                {order.failure_reason && (
                    <div className="bg-red-50 p-6 shadow rounded-lg border border-red-200">
                        <h2 className="text-sm text-red-700 uppercase tracking-wider mb-2">Exact Error Log</h2>
                        <p className="font-mono text-red-900 text-sm whitespace-pre-wrap">
                            {order.failure_reason}
                        </p>
                    </div>
                )}
            </div>

            <div className="bg-white p-6 shadow rounded-lg border">
                <h2 className="text-sm text-gray-500 uppercase tracking-wider mb-4">Original Shopify Payload</h2>
                <pre className="bg-gray-900 text-green-400 p-4 rounded overflow-x-auto text-sm">
                    {JSON.stringify(order.raw_payload, null, 2)}
                </pre>
            </div>
        </div>
    );
}