export const LogoMark = ({ size = 26 }: { size?: number }) => {
  const height = size * 1.125; // Maintain aspect ratio
  return (
    <svg width={size} height={height} viewBox="0 0 32 36" fill="none">
      <rect
        x="1"
        y="1"
        width="30"
        height="34"
        rx="6"
        fill="url(#container-gradient)"
        stroke="#4a7fb3"
        strokeWidth="2"
      />
      <rect x="5" y="5" width="22" height="10" rx="3" fill="url(#header-gradient)" />
      <circle cx="9" cy="10" r="2" fill="rgba(255,255,255,0.85)" />
      <rect x="6" y="19" width="14" height="2" rx="1" fill="#4a7fb3" opacity="0.4" />
      <rect x="6" y="24" width="10" height="2" rx="1" fill="#4a7fb3" opacity="0.4" />
      <defs>
        <linearGradient
          id="container-gradient"
          x1="0"
          y1="0"
          x2="16"
          y2="36"
          gradientUnits="userSpaceOnUse"
        >
          <stop offset="0%" stopColor="#1e3a5f" />
          <stop offset="100%" stopColor="#112235" />
        </linearGradient>
        <linearGradient
          id="header-gradient"
          x1="5"
          y1="10"
          x2="27"
          y2="10"
          gradientUnits="userSpaceOnUse"
        >
          <stop offset="0%" stopColor="#5ba3f5" />
          <stop offset="100%" stopColor="#3d8ae0" />
        </linearGradient>
      </defs>
    </svg>
  );
};
