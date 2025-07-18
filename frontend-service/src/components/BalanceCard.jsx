import React, { useState, useEffect } from 'react';
import api from '../services/api';

/**
 * Displays the current balance and provides a top-up form.
 */
const BalanceCard = () => {
  const [balance, setBalance] = useState(null);
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchBalance = async () => {
    try {
      const response = await api.get('/balance');
      setBalance(response.data.balance);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchBalance();
  }, []);

  const handleTopUp = async () => {
    setLoading(true);
    setError(null);
    try {
      const amt = parseFloat(amount);
      if (isNaN(amt) || amt <= 0) {
        throw new Error('Enter a valid positive amount');
      }
      await api.post('/balance/topup', { amount: amt });
      setAmount('');
      await fetchBalance();
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card mb-4">
      <div className="card-body">
        <h5 className="card-title">Balance</h5>
        <p className="card-text">
          {balance !== null ? `${balance.toFixed(2)} credits` : 'Loading...'}
        </p>
        <div className="input-group">
          <input
            type="number"
            className="form-control"
            placeholder="Top-up amount"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
          <button
            className="btn btn-primary"
            type="button"
            onClick={handleTopUp}
            disabled={loading}
          >
            {loading ? 'Processing...' : 'Top Up'}
          </button>
        </div>
        {error && <div className="text-danger mt-2">{error}</div>}
      </div>
    </div>
  );
};

export default BalanceCard; 