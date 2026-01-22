/**
 * LogoMark component - The "Entity Seed" logo
 * A rounded rectangle representing a conceptual entity,
 * the atomic building block from which data models grow.
 */

interface LogoMarkProps {
  size?: number;
}

export const LogoMark = ({ size = 26 }: LogoMarkProps) => {
  const height = size * 1.125; // Maintain aspect ratio (36/32)
  return (
    <svg
      width={size}
      height={height}
      viewBox="0 0 32 36"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Container */}
      <rect
        x="1"
        y="1"
        width="30"
        height="34"
        rx="6"
        fill="url(#logo-container-gradient)"
        stroke="#4a7fb3"
        strokeWidth="2"
      />

      {/* Header bar */}
      <rect
        x="5"
        y="5"
        width="22"
        height="10"
        rx="3"
        fill="url(#logo-header-gradient)"
      />

      {/* Indicator dot */}
      <circle cx="9" cy="10" r="2" fill="rgba(255,255,255,0.85)" />

      {/* Attribute lines */}
      <rect x="6" y="19" width="14" height="2" rx="1" fill="#4a7fb3" opacity="0.4" />
      <rect x="6" y="24" width="10" height="2" rx="1" fill="#4a7fb3" opacity="0.4" />

      {/* Gradients - using unique IDs to avoid conflicts */}
      <defs>
        <linearGradient
          id="logo-container-gradient"
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
          id="logo-header-gradient"
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
