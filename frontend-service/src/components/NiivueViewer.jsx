import React, { useEffect, useRef } from 'react';
import { Niivue } from '@niivue/niivue';

const defaultOverlayOptions = {
  colormap: 'red',
  opacity: 0.5,
  cal_min: 0.5,
};

// sources: { background: string, overlays?: Array<{ url: string, colormap?: string, opacity?: number, cal_min?: number, cal_max?: number }> }
const NiivueViewer = ({ sources, onReady, onError, height = 600 }) => {
  const canvasRef = useRef(null);
  const nvRef = useRef(null);

  useEffect(() => {
    let isCancelled = false;

    const init = async () => {
      try {
        const nv = new Niivue({ logging: false, dragAndDropEnabled: false });
        nvRef.current = nv;
        await nv.attachToCanvas(canvasRef.current);
        // Load background volume (grayscale)
        await nv.loadVolumes([{ url: sources.background, colormap: 'gray' }]);

        // Load overlays with explicit options
        if (Array.isArray(sources.overlays)) {
          for (const ov of sources.overlays) {
            const opts = {
              url: ov.url,
              colormap: ov.colormap || defaultOverlayOptions.colormap,
              opacity: typeof ov.opacity === 'number' ? ov.opacity : defaultOverlayOptions.opacity,
              cal_min: typeof ov.cal_min === 'number' ? ov.cal_min : defaultOverlayOptions.cal_min,
            };
            await nv.addVolumeFromUrl(opts);
          }
        }

        if (!isCancelled) {
          nv.updateGLVolume();
          if (onReady) onReady();
        }
      } catch (e) {
        if (onError) onError(e?.message || String(e));
      }
    };

    init();

    return () => {
      isCancelled = true;
      if (nvRef.current) {
        nvRef.current = null;
      }
    };
  }, [sources?.background, JSON.stringify(sources?.overlays)]);

  return (
    <div style={{ width: '100%', height }}>
      <canvas ref={canvasRef} style={{ width: '100%', height: '100%' }} />
    </div>
  );
};

export default NiivueViewer; 