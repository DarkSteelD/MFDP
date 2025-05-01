import React, { useState } from 'react';
import BalanceCard from '../components/BalanceCard';
import api from '../services/api';

/**
 * Dashboard page: shows balance and allows image prediction.
 */
const DashboardPage = () => {
  const [previewSrc, setPreviewSrc] = useState(null);
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f);
    setResult(null);
    setError(null);
    const reader = new FileReader();
    reader.onloadend = () => setPreviewSrc(reader.result);
    reader.readAsDataURL(f);
  };

  const handlePredict = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const base64 = previewSrc.split(',')[1];
      const response = await api.post('/predict', { image: base64 });
      const { credits_spent } = response.data;
      setResult(`Prediction queued! Credits spent: ${credits_spent}`);
      setFile(null);
      setPreviewSrc(null);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <BalanceCard />
      <h2>Image Prediction</h2>
      <div className="mb-3">
        <input type="file" accept="image/*" onChange={handleFileChange} />
      </div>
      {previewSrc && (
        <div className="mb-3">
          <img src={previewSrc} alt="Preview" className="img-fluid" />
        </div>
      )}
      <button
        className="btn btn-primary mb-3"
        onClick={handlePredict}
        disabled={loading || !file}
      >
        {loading ? 'Predicting...' : 'Predict'}
      </button>
      {error && <div className="text-danger">{error}</div>}
      {result && (
        <div className="alert alert-info">
          {result}
        </div>
      )}
    </div>
  );
};

export default DashboardPage; 