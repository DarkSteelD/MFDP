import React from 'react';
import { Link } from 'react-router-dom';

/**
 * Home page: describes ML service features.
 */
const HomePage = () => (
  <div className="text-center">
    <h1>Welcome to ML Service</h1>
    <p>This service allows you to:</p>
    <ul className="list-group list-group-flush">
      <li className="list-group-item">Register and authenticate</li>
      <li className="list-group-item">View and top up your balance</li>
      <li className="list-group-item">Perform ML predictions (text or image)</li>
      <li className="list-group-item">View transaction history</li>
    </ul>
    <div className="mt-4">
      <Link className="btn btn-primary me-2" to="/register">Register</Link>
      <Link className="btn btn-secondary" to="/login">Login</Link>
    </div>
  </div>
);

export default HomePage; 