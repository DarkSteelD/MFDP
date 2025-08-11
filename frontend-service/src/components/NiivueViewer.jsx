import React, { useEffect, useRef } from 'react';
import { Niivue } from '@niivue/niivue';

const defaultOverlayOptions = {
  colormap: 'red',
  opacity: 0.5,
};

// sources: { background: string, overlays?: Array<{ url: string, colormap?: string, opacity?: number }> }
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
        await nv.loadVolumes([{ url: sources.background }]);

        if (Array.isArray(sources.overlays)) {
          for (const ov of sources.overlays) {
            await nv.addVolumeFromUrl({ url: ov.url });
            const index = nv.volumes.length - 1;
            nv.setColormap(index, ov.colormap || defaultOverlayOptions.colormap);
            nv.setOpacity(index, typeof ov.opacity === 'number' ? ov.opacity : defaultOverlayOptions.opacity);
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