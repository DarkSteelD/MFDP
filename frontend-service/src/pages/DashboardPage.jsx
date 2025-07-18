import React, { useState } from 'react';
import BalanceCard from '../components/BalanceCard';
import MaskOverlay from '../components/MaskOverlay';
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
  const [showOverlay, setShowOverlay] = useState(false);

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
      const { credits_spent, image_prediction } = response.data;
      setResult({
        credits_spent,
        mask_url: image_prediction
      });
      setShowOverlay(true);
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
      {previewSrc && !showOverlay && (
        <div className="mb-3">
          <img src={previewSrc} alt="Preview" className="img-fluid" />
        </div>
      )}
      
      {showOverlay && result && (
        <div className="mb-3">
          <h5>Result with Mask Overlay:</h5>
          <MaskOverlay
            originalImage={previewSrc}
            maskImage={result.mask_url}
            onLoad={() => console.log('Overlay loaded')}
            onError={(error) => console.error('Overlay error:', error)}
          />
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
          <strong>Credits spent:</strong> {result.credits_spent}
          <br />
          <small>Mask has been applied to the image with 50% transparency.</small>
        </div>
      )}
      
      {showOverlay && (
        <button
          className="btn btn-secondary mb-3"
          onClick={() => {
            setShowOverlay(false);
            setResult(null);
            setFile(null);
            setPreviewSrc(null);
          }}
        >
          Upload New Image
        </button>
      )}
    </div>
  );
};

export default DashboardPage; 