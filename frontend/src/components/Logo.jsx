import { useId } from 'react';

// Nextrung mark: three rungs stepping up toward an AI spark. Same artwork as
// public/favicon.svg - keep them in sync.
export function LogoMark({ size = 30, className }) {
  const gradient = `nr-${useId().replace(/:/g, '')}`;
  return (
    <svg className={className} width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id={gradient} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#0f766e" />
          <stop offset="1" stopColor="#0d9488" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="8" fill={`url(#${gradient})`} />
      <g fill="#fff">
        <rect x="5" y="21.5" width="8" height="3.6" rx="1.8" opacity=".55" />
        <rect x="10" y="15.5" width="8" height="3.6" rx="1.8" opacity=".8" />
        <rect x="15" y="9.5" width="8" height="3.6" rx="1.8" />
      </g>
      <path className="logo-spark" d="M26 3.6Q26 7 29.4 7Q26 7 26 10.4Q26 7 22.6 7Q26 7 26 3.6Z" fill="#fbbf24" />
    </svg>
  );
}

export function Brand() {
  return (
    <span className="brand">
      <LogoMark className="brand-mark" />
      <span className="brand-name">Next<span className="brand-accent">rung</span></span>
    </span>
  );
}
