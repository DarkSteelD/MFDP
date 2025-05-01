import React, { useState } from 'react';
import api from '../services/api';
import { useNavigate } from 'react-router-dom';

/**
 * Registration page for new users.
 */
const RegisterPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await api.post('/auth/register', { email, password });
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  return (
    <div className="col-md-6 offset-md-3">
      <h2>Register</h2>
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label>Email</label>
          <input
            type="email"
            className="form-control"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="mb-3">
          <label>Password</label>
          <input
            type="password"
            className="form-control"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            required
          />
        </div>
        {error && <div className="text-danger mb-3">{error}</div>}
        <button type="submit" className="btn btn-primary">Register</button>
      </form>
    </div>
  );
};

export default RegisterPage; 