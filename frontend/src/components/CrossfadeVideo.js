import React, { useRef, useEffect, useState } from 'react';

/**
 * Crossfading looping video — two stacked <video> elements alternate
 * so the loop point is never visible. Each video fades out near its end
 * while the other fades in from the start.
 */
const CrossfadeVideo = ({ src, poster, style, className, mask }) => {
  const videoA = useRef(null);
  const videoB = useRef(null);
  const [opacityA, setOpacityA] = useState(1);
  const [opacityB, setOpacityB] = useState(0);
  const activeRef = useRef('A'); // which video is currently "on top"
  const FADE_DURATION = 1.2; // seconds of crossfade overlap

  useEffect(() => {
    const a = videoA.current;
    const b = videoB.current;
    if (!a || !b) return;

    const handleTimeUpdate = () => {
      const active = activeRef.current === 'A' ? a : b;
      const standby = activeRef.current === 'A' ? b : a;
      if (!active.duration || active.duration === Infinity) return;

      const remaining = active.duration - active.currentTime;

      if (remaining <= FADE_DURATION && remaining > 0) {
        // Start crossfade
        const progress = 1 - (remaining / FADE_DURATION);
        if (activeRef.current === 'A') {
          setOpacityA(1 - progress);
          setOpacityB(progress);
        } else {
          setOpacityB(1 - progress);
          setOpacityA(progress);
        }

        // Start the standby video if paused
        if (standby.paused) {
          standby.currentTime = 0;
          standby.play().catch(() => {});
        }
      }
    };

    const handleEnded = (which) => {
      if (which === 'A') {
        activeRef.current = 'B';
        setOpacityA(0);
        setOpacityB(1);
        b.currentTime = b.currentTime || 0;
        b.play().catch(() => {});
      } else {
        activeRef.current = 'A';
        setOpacityB(0);
        setOpacityA(1);
        a.currentTime = a.currentTime || 0;
        a.play().catch(() => {});
      }
    };

    a.addEventListener('timeupdate', handleTimeUpdate);
    b.addEventListener('timeupdate', handleTimeUpdate);
    a.addEventListener('ended', () => handleEnded('A'));
    b.addEventListener('ended', () => handleEnded('B'));

    // Start A immediately
    a.play().catch(() => {});

    return () => {
      a.removeEventListener('timeupdate', handleTimeUpdate);
      b.removeEventListener('timeupdate', handleTimeUpdate);
    };
  }, []);

  const baseStyle = {
    ...style,
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    transition: 'opacity 0.3s linear',
    WebkitMaskImage: mask,
    maskImage: mask,
  };

  return (
    <div style={{ position: 'relative', width: style?.width, height: '100%', flexShrink: 0, marginLeft: style?.marginLeft, marginRight: style?.marginRight }}>
      <video
        ref={videoA}
        muted
        playsInline
        disablePictureInPicture
        poster={poster}
        className={className}
        style={{ ...baseStyle, opacity: opacityA, zIndex: opacityA >= opacityB ? 2 : 1 }}
      >
        <source src={src} type="video/mp4" />
      </video>
      <video
        ref={videoB}
        muted
        playsInline
        disablePictureInPicture
        poster={poster}
        className={className}
        style={{ ...baseStyle, opacity: opacityB, zIndex: opacityB > opacityA ? 2 : 1 }}
      >
        <source src={src} type="video/mp4" />
      </video>
    </div>
  );
};

export default CrossfadeVideo;
