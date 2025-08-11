import React, { useState } from 'react';
import BalanceCard from '../components/BalanceCard';
import NiivueViewer from '../components/NiivueViewer';
import api from '../services/api';

/**
 * Dashboard page: shows balance and allows CT (NIfTI) prediction.
 */
const DashboardPage = () => {
  const [file, setFile] = useState(null);
  const [previewInfo, setPreviewInfo] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedView, setSelectedView] = useState('original'); // 'original' | 'brain' | 'aneurysm'

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    if (!f.name.endsWith('.nii') && !f.name.endsWith('.nii.gz')) {
      setError('Please upload a NIfTI file (.nii or .nii.gz)');
      return;
    }
    setFile(f);
    setResult(null);
    setError(null);
    setPreviewInfo({
      name: f.name,
      size: (f.size / (1024 * 1024)).toFixed(2) + ' MB',
      type: f.type || 'NIfTI medical image'
    });
  };

  const handlePredict = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('scan', file);
      const response = await api.post('/predict/3d-scan', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const { credits_spent, brain_mask_url, aneurysm_mask_url, original_scan_url } = response.data;
      setResult({ credits_spent, brain_mask_url, aneurysm_mask_url, original_scan_url });
      setSelectedView('original');
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <BalanceCard />
      <h2>CT Prediction (NIfTI)</h2>
      <div className="mb-3">
        <input type="file" accept=".nii,.nii.gz" onChange={handleFileChange} />
      </div>

      {previewInfo && !result && (
        <div className="mb-3">
          <div className="card">
            <div className="card-body">
              <h6 className="card-title">Selected File:</h6>
              <p className="mb-1"><strong>Name:</strong> {previewInfo.name}</p>
              <p className="mb-1"><strong>Size:</strong> {previewInfo.size}</p>
              <p className="mb-0"><strong>Type:</strong> {previewInfo.type}</p>
            </div>
          </div>
        </div>
      )}

      <button
        className="btn btn-primary mb-3"
        onClick={handlePredict}
        disabled={loading || !file}
      >
        {loading ? 'Analyzing...' : 'Analyze Scan'}
      </button>

      {error && <div className="text-danger">{error}</div>}

      {result && (
        <div className="alert alert-info">
          <strong>Credits spent:</strong> {result.credits_spent}
        </div>
      )}

      {result && (
        <div className="card">
          <div className="card-header">
            <h5 className="mb-0">3D Visualization</h5>
          </div>
          <div className="card-body">
            <div className="mb-3">
              <div className="btn-group" role="group">
                <button
                  type="button"
                  className={`btn btn-sm ${selectedView === 'original' ? 'btn-primary' : 'btn-outline-primary'}`}
                  onClick={() => setSelectedView('original')}
                >
                  Original
                </button>
                <button
                  type="button"
                  className={`btn btn-sm ${selectedView === 'brain' ? 'btn-primary' : 'btn-outline-primary'}`}
                  onClick={() => setSelectedView('brain')}
                >
                  Brain Mask
                </button>
                <button
                  type="button"
                  className={`btn btn-sm ${selectedView === 'aneurysm' ? 'btn-primary' : 'btn-outline-danger'}`}
                  onClick={() => setSelectedView('aneurysm')}
                >
                  Aneurysm Mask
                </button>
              </div>
            </div>

            <NiivueViewer
              sources={{
                background: `/uploads/${result.original_scan_url}`,
                overlays:
                  selectedView === 'original'
                    ? []
                    : selectedView === 'brain'
                    ? [{ url: result.brain_mask_url, colormap: 'green', opacity: 0.5 }]
                    : [{ url: result.aneurysm_mask_url, colormap: 'red', opacity: 0.5 }],
              }}
              onReady={() => console.log('Niivue ready')}
              onError={(e) => console.error('Niivue error', e)}
            />

            <div className="mt-3">
              <h6>Download Results</h6>
              <div className="d-grid gap-2 d-md-block">
                <a href={result.brain_mask_url} className="btn btn-outline-primary btn-sm" target="_blank" rel="noopener noreferrer">Download Brain Mask</a>
                <a href={result.aneurysm_mask_url} className="btn btn-outline-danger btn-sm" target="_blank" rel="noopener noreferrer">Download Aneurysm Mask</a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardPage; 