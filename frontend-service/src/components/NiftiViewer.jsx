import React, { useEffect, useRef, useState } from 'react';

/**
 * NIfTI Viewer component that integrates MRIcroWeb for 3D medical image visualization
 */
const NiftiViewer = ({ fileUrl, onLoad, onError }) => {
  const iframeRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!fileUrl) return;

    setIsLoading(true);
    setError(null);

    // Create a URL for the NIfTI file
    const viewerUrl = `/nifti-viewer/index.html?file=${encodeURIComponent(fileUrl)}`;
    
    if (iframeRef.current) {
      iframeRef.current.src = viewerUrl;
    }
  }, [fileUrl]);

  const handleIframeLoad = () => {
    setIsLoading(false);
    if (onLoad) onLoad();
  };

  const handleIframeError = () => {
    setIsLoading(false);
    const errorMsg = 'Failed to load NIfTI viewer';
    setError(errorMsg);
    if (onError) onError(errorMsg);
  };

  return (
    <div className="nifti-viewer-container" style={{ position: 'relative', width: '100%', height: '600px' }}>
      {isLoading && (
        <div className="loading-overlay" style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          zIndex: 10
        }}>
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      )}
      
      {error && (
        <div className="error-overlay" style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          zIndex: 10
        }}>
          <div className="alert alert-danger">
            <i className="fas fa-exclamation-triangle me-2"></i>
            {error}
          </div>
        </div>
      )}
      
      <iframe
        ref={iframeRef}
        title="NIfTI Viewer"
        style={{
          width: '100%',
          height: '100%',
          border: '1px solid #ddd',
          borderRadius: '4px'
        }}
        onLoad={handleIframeLoad}
        onError={handleIframeError}
        sandbox="allow-scripts allow-same-origin"
      />
    </div>
  );
};

export default NiftiViewer; 