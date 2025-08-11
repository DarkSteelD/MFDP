import React, { useState, useEffect, useRef } from 'react';

/**
 * Component for displaying an image with an overlaid mask
 */
const MaskOverlay = ({ originalImage, maskImage, onLoad, onError }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!originalImage || !maskImage) return;

    setIsLoading(true);
    setError(null);

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    // Load both images
    const originalImg = new Image();
    const maskImg = new Image();

    originalImg.crossOrigin = 'anonymous';
    maskImg.crossOrigin = 'anonymous';

    let imagesLoaded = 0;
    const totalImages = 2;

    const checkAllLoaded = () => {
      imagesLoaded++;
      if (imagesLoaded === totalImages) {
        drawOverlay();
      }
    };

    originalImg.onload = checkAllLoaded;
    originalImg.onerror = () => {
      setError('Failed to load original image');
      setIsLoading(false);
    };

    maskImg.onload = checkAllLoaded;
    maskImg.onerror = () => {
      setError('Failed to load mask image');
      setIsLoading(false);
    };

    originalImg.src = originalImage;
    maskImg.src = maskImage;
  }, [originalImage, maskImage]);

  const drawOverlay = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const originalImg = new Image();
    const maskImg = new Image();

    originalImg.onload = () => {
      // Set canvas size to match original image
      canvas.width = originalImg.width;
      canvas.height = originalImg.height;

      // Draw original image with 0.5 opacity
      ctx.globalAlpha = 0.5;
      ctx.drawImage(originalImg, 0, 0);

      // Load and draw mask
      maskImg.onload = () => {
        // Draw mask with 0.5 opacity
        ctx.globalAlpha = 0.5;
        ctx.drawImage(maskImg, 0, 0);
        
        // Reset opacity
        ctx.globalAlpha = 1.0;
        
        setIsLoading(false);
        if (onLoad) onLoad();
      };
      maskImg.src = maskImage;
    };
    originalImg.src = originalImage;
  };

  return (
    <div className="mask-overlay-container" style={{ position: 'relative', width: '100%' }}>
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
      
      <canvas
        ref={canvasRef}
        style={{
          width: '100%',
          height: 'auto',
          border: '1px solid #ddd',
          borderRadius: '4px',
          maxWidth: '100%'
        }}
      />
    </div>
  );
};

export default MaskOverlay; 