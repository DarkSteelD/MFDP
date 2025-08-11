import React, { useState, useRef } from 'react';
import BalanceCard from '../components/BalanceCard';
import NiftiViewer from '../components/NiftiViewer';
import MaskOverlay from '../components/MaskOverlay';
import api from '../services/api';

const Scan3DPage = () => {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [selectedView, setSelectedView] = useState('original'); // 'original', 'brain', 'aneurysm'
  const [showOverlay, setShowOverlay] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    
    if (!f.name.endsWith('.nii.gz') && !f.name.endsWith('.nii')) {
      setError('Please upload a NIfTI file (.nii or .nii.gz)');
      return;
    }
    
    setFile(f);
    setResult(null);
    setError(null);
    
    setPreviewData({
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
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      const { credits_spent, brain_mask_url, aneurysm_mask_url, original_scan_url } = response.data;
      setResult({
        credits_spent,
        brain_mask_url,
        aneurysm_mask_url,
        original_scan_url
      });
      setShowOverlay(true);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const f = files[0];
      if (f.name.endsWith('.nii.gz') || f.name.endsWith('.nii')) {
        setFile(f);
        setResult(null);
        setError(null);
        setPreviewData({
          name: f.name,
          size: (f.size / (1024 * 1024)).toFixed(2) + ' MB',
          type: f.type || 'NIfTI medical image'
        });
      } else {
        setError('Please upload a NIfTI file (.nii or .nii.gz)');
      }
    }
  };

  return (
    <div>
      <BalanceCard />
      <div className="row">
        <div className="col-md-8">
          <h2>3D Medical Scan Analysis</h2>
          <p className="text-muted">
            Upload a 3D medical scan in NIfTI format (.nii or .nii.gz) for brain and aneurysm analysis.
          </p>
          
          <div 
            className="border-2 border-dashed border-secondary rounded p-4 text-center mb-3"
            style={{ 
              borderStyle: 'dashed',
              minHeight: '200px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center'
            }}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            <div className="mb-3">
              <i className="fas fa-brain fa-3x text-secondary"></i>
            </div>
            <p className="mb-3">Drag and drop your NIfTI file here, or click to browse</p>
            <input 
              type="file" 
              accept=".nii,.nii.gz"
              onChange={handleFileChange}
              ref={fileInputRef}
              className="form-control"
            />
          </div>

          {previewData && (
            <div className="card mb-3">
              <div className="card-body">
                <h6 className="card-title">Selected File:</h6>
                <p className="mb-1"><strong>Name:</strong> {previewData.name}</p>
                <p className="mb-1"><strong>Size:</strong> {previewData.size}</p>
                <p className="mb-0"><strong>Type:</strong> {previewData.type}</p>
              </div>
            </div>
          )}

          <button
            className="btn btn-primary mb-3"
            onClick={handlePredict}
            disabled={loading || !file}
          >
            {loading ? (
              <>
                <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                Analyzing...
              </>
            ) : (
              'Analyze Scan'
            )}
          </button>

          {error && (
            <div className="alert alert-danger">
              <i className="fas fa-exclamation-triangle me-2"></i>
              {error}
            </div>
          )}
        </div>

        <div className="col-md-4">
          {result && (
            <div className="card">
              <div className="card-header">
                <h5 className="mb-0">Analysis Results</h5>
              </div>
              <div className="card-body">
                <div className="mb-3">
                  <strong>Credits Spent:</strong> {result.credits_spent}
                </div>
                
                <div className="mb-3">
                  <h6>View Options:</h6>
                  <div className="btn-group-vertical w-100" role="group">
                    <button
                      type="button"
                      className={`btn btn-sm ${selectedView === 'original' ? 'btn-primary' : 'btn-outline-primary'}`}
                      onClick={() => setSelectedView('original')}
                    >
                      <i className="fas fa-eye me-1"></i>
                      Original Scan
                    </button>
                    <button
                      type="button"
                      className={`btn btn-sm ${selectedView === 'brain' ? 'btn-primary' : 'btn-outline-primary'}`}
                      onClick={() => setSelectedView('brain')}
                    >
                      <i className="fas fa-brain me-1"></i>
                      Brain Mask
                    </button>
                    <button
                      type="button"
                      className={`btn btn-sm ${selectedView === 'aneurysm' ? 'btn-primary' : 'btn-outline-danger'}`}
                      onClick={() => setSelectedView('aneurysm')}
                    >
                      <i className="fas fa-exclamation-triangle me-1"></i>
                      Aneurysm Mask
                    </button>
                  </div>
                </div>

                <div className="mb-3">
                  <h6>Download Results:</h6>
                  <div className="d-grid gap-2">
                    <a 
                      href={result.brain_mask_url} 
                      className="btn btn-outline-primary btn-sm"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <i className="fas fa-download me-1"></i>
                      Download Brain Mask
                    </a>
                    <a 
                      href={result.aneurysm_mask_url} 
                      className="btn btn-outline-danger btn-sm"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <i className="fas fa-download me-1"></i>
                      Download Aneurysm Mask
                    </a>
                  </div>
                </div>

                <div className="alert alert-success">
                  <i className="fas fa-check-circle me-2"></i>
                  Analysis completed successfully!
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 3D Viewer Section */}
      {result && (
        <div className="row mt-4">
          <div className="col-12">
            <div className="card">
              <div className="card-header">
                <h5 className="mb-0">
                  <i className="fas fa-cube me-2"></i>
                  3D Visualization
                </h5>
              </div>
              <div className="card-body">
                <NiftiViewer
                  fileUrl={
                    selectedView === 'original' 
                      ? `/uploads/${result.original_scan_url}`
                      : selectedView === 'brain'
                      ? result.brain_mask_url
                      : result.aneurysm_mask_url
                  }
                  onLoad={() => console.log('NIfTI viewer loaded')}
                  onError={(error) => console.error('NIfTI viewer error:', error)}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mask Overlay Section */}
      {showOverlay && result && (
        <div className="row mt-4">
          <div className="col-12">
            <div className="card">
              <div className="card-header">
                <h5 className="mb-0">
                  <i className="fas fa-layer-group me-2"></i>
                  Mask Overlay Visualization
                </h5>
              </div>
              <div className="card-body">
                <div className="row">
                  <div className="col-md-6">
                    <h6>Brain Mask Overlay:</h6>
                    <MaskOverlay
                      originalImage={`/uploads/${result.original_scan_url}`}
                      maskImage={result.brain_mask_url}
                      onLoad={() => console.log('Brain mask overlay loaded')}
                      onError={(error) => console.error('Brain mask overlay error:', error)}
                    />
                  </div>
                  <div className="col-md-6">
                    <h6>Aneurysm Mask Overlay:</h6>
                    <MaskOverlay
                      originalImage={`/uploads/${result.original_scan_url}`}
                      maskImage={result.aneurysm_mask_url}
                      onLoad={() => console.log('Aneurysm mask overlay loaded')}
                      onError={(error) => console.error('Aneurysm mask overlay error:', error)}
                    />
                  </div>
                </div>
                <div className="mt-3">
                  <small className="text-muted">
                    Both original scan and masks are displayed with 50% transparency for better visualization.
                  </small>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reset Button */}
      {showOverlay && (
        <div className="row mt-3">
          <div className="col-12 text-center">
            <button
              className="btn btn-secondary"
              onClick={() => {
                setShowOverlay(false);
                setResult(null);
                setFile(null);
                setPreviewData(null);
                if (fileInputRef.current) {
                  fileInputRef.current.value = '';
                }
              }}
            >
              <i className="fas fa-upload me-2"></i>
              Upload New Scan
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Scan3DPage; 