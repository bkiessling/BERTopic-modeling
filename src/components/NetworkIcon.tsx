export function NetworkIcon({ size = 17 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
      focusable="false"
    >
      <path
        d="M11.6 11.7 3.8 5.5m8.4 6L19.4 2.8m-7.2 9.1 8.1 1.5m-8.7-.8L6.1 20m6.3-7.3 6.1 7.6"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.3"
      />
      <circle cx="12" cy="12" r="3.5" />
      <circle cx="3.8" cy="5.5" r="2.1" />
      <circle cx="19" cy="2.8" r="2.7" />
      <circle cx="20.3" cy="13.4" r="2.1" />
      <circle cx="6.1" cy="20" r="2.9" />
      <circle cx="18.5" cy="20.3" r="2.4" />
    </svg>
  );
}
