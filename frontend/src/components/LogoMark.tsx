/**
 * LogoMark component - The infinity loop mark
 * Two interlocking loops representing the connection between
 * conceptual (orange) and physical (gray), with a flow bar beneath.
 */

interface LogoMarkProps {
  size?: number;
}

export const LogoMark = ({ size = 26 }: LogoMarkProps) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 80 80"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Left loop (conceptual - orange) */}
      <path
        d="M12 32 C12 16 24 12 40 32 C24 52 12 48 12 32"
        stroke="var(--logo-gradient-start, #e67e22)"
        strokeWidth="6"
        fill="none"
        strokeLinecap="round"
      />

      {/* Right loop (physical - gray) */}
      <path
        d="M40 32 C56 52 68 48 68 32 C68 16 56 12 40 32"
        stroke="var(--logo-gray, #888888)"
        strokeWidth="6"
        fill="none"
        strokeLinecap="round"
      />

      {/* Flow bar */}
      <path
        d="M12 58 L68 58"
        stroke="var(--logo-gradient-start, #e67e22)"
        strokeWidth="5"
        strokeLinecap="round"
      />
    </svg>
  );
};
